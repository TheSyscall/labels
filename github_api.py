import json
import os
import re
import sys

import requests


def fetch_json(endpoint: str, params={}, body={}, method="GET"):
    base_url = "https://api.github.com"
    url = base_url + endpoint
    if endpoint.startswith("http"):
        url = endpoint

    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    token = os.getenv("GITHUB_ACCESS_TOKEN")
    if token is not None and token != "":
        headers["Authorization"] = "token " + token

    response = None

    match (method):
        case "GET":
            response = requests.get(
                url,
                params=params,
                headers=headers,
            )
        case "POST":
            response = requests.post(
                url,
                params=params,
                json=body,
                headers=headers,
            )
        case "PATCH":
            response = requests.patch(
                url,
                params=params,
                json=body,
                headers=headers,
            )
        case "DELETE":
            response = requests.delete(
                url,
                params=params,
                headers=headers,
            )

    result = response.content
    try:
        result = response.json()
    except json.JSONDecodeError as e:
        print(f"Failed to decode API response! {e.msg}", file=sys.stderr)
        exit(1)

    return (result, response.status_code, response.headers)


def fetch_paginated_json(endpoint: str, params={}, body={}, method="GET"):
    content = []
    params["per_page"] = 100

    code = 0
    while True:
        (data, code, headers) = fetch_json(endpoint, params, body, method)

        if code >= 200 and code < 300:
            pass  # Nothing to do
        elif code == 404:
            return {}, "Resource not found"
        elif code < 0:
            return {}, data
        else:
            return {}, "Unknown error"

        content += data

        if "Link" not in headers:
            break
        links = parse_link_header(headers["Link"])

        if "next" not in links:
            break

        endpoint = links["next"]

    return content, None


def fetch_labels(namespace: str, repository: str):
    return fetch_paginated_json(f"/repos/{namespace}/{repository}/labels")


def delete_label(namespace: str, repository: str, label: str):
    (data, code, _) = fetch_json(
        f"/repos/{namespace}/{repository}/labels/{label}",
        method="DELETE",
    )

    if code >= 200 and code < 300:
        return True, None
    elif code == 404:
        return False, "Not found"
    elif code < 0:
        return {}, data
    else:
        return False, "Unknown error"


def create_label(
    namespace: str,
    repository: str,
    name: str,
    description: str = None,
    color: str = None,
):
    body = {
        "name": name,
    }

    if description is not None:
        body["description"] = description
    if color is not None:
        body["color"] = color

    (data, code, _) = fetch_json(
        f"/repos/{namespace}/{repository}/labels",
        body=body,
        method="POST",
    )

    if code >= 200 and code < 300:
        return True, None
    elif code == 404:
        return False, "Resource not found"
    elif code == 422:
        return False, "Validation failed"
    elif code < 0:
        return {}, data
    else:
        return False, "Unknown error"


def update_label(
    namespace: str,
    repository: str,
    old_name: str,
    new_name: str = None,
    description: str = None,
    color: str = None,
):
    body = {}

    if new_name is not None:
        body["new_name"] = new_name
    if description is not None:
        body["description"] = description
    if color is not None:
        body["color"] = color

    (data, code, _) = fetch_json(
        f"/repos/{namespace}/{repository}/labels/{old_name}",
        body=body,
        method="PATCH",
    )

    if code >= 200 and code < 300:
        return True, None
    elif code == 404:
        return False, "Not found"
    elif code == 422:
        return False, "Validation failed"
    elif code < 0:
        return {}, data
    else:
        return False, "Unknown error"


def fetch_repositories(namespace: str):
    if namespace == "-":
        (data, err) = fetch_paginated_json("/user/repos")
    else:
        (data, err) = fetch_paginated_json(f"/orgs/{namespace}/repos")
        if err is not None:
            (data, err) = fetch_paginated_json(f"/users/{namespace}/repos")

    return data, err


def parse_link_header(header: str):
    regex = re.compile(r'<(.*?)>(?:.*?)rel="([A-z\s]*)"')

    links = {}
    for match in regex.finditer(header):
        link = match.group(1)
        rel = match.group(2)

        links[rel] = link

    return links
