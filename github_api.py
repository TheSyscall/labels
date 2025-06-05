import requests
import os
import re


def fetchJson(endpoint: str, params={}, body={}, method="GET"):
    token = os.getenv('GITHUB_ACCESS_TOKEN')

    if token is None or token == '':
        return "No API Token Provided", -500

    base_url = "https://api.github.com"

    url = base_url + endpoint

    if endpoint.startswith('http'):
        url = endpoint

    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': 'token ' + token,
        'X-GitHub-Api-Version': '2022-11-28',
    }

    response = None

    match(method):
        case 'GET':
            response = requests.get(url,
                                    params=params,
                                    headers=headers)
        case 'POST':
            response = requests.post(url,
                                     params=params,
                                     json=body,
                                     headers=headers)
        case 'PATCH':
            response = requests.patch(url,
                                      params=params,
                                      json=body,
                                      headers=headers)
        case 'DELETE':
            response = requests.delete(url,
                                       params=params,
                                       headers=headers)

    result = response.content
    try:
        result = response.json()
    except:
        pass

    return (result, response.status_code, response.headers)


def fetchPaginatedJson(endpoint: str, params={}, body={}, method="GET"):
    content = []
    params['per_page'] = 100

    code = 0
    while True:
        (data, code, headers) = fetchJson(endpoint, params, body, method)

        if code >= 200 and code < 300:
            pass  # Nothing to do
        elif code == 404:
            return {}, 'Resource not found'
        elif code < 0:
            return {}, data
        else:
            return {}, 'Unknown error'

        content += data

        if 'Link' not in headers:
            break
        links = parseLinkHeader(headers['Link'])

        if 'next' not in links:
            break

        endpoint = links['next']

    return content, code


def fetchLabels(namespace: str, repository: str):
    (data, code) = fetchPaginatedJson(f"/repos/{namespace}/{repository}/labels")

    if code >= 200 and code < 300:
        return data, None
    elif code == 404:
        return {}, 'Resource not found'
    elif code < 0:
        return {}, data
    else:
        return {}, 'Unknown error'


def deleteLabel(namespace: str, repository: str, label: str):
    (data, code) = fetchJson(f"/repos/{namespace}/{repository}/labels/{label}",
                             method="DELETE")

    if code >= 200 and code < 300:
        return True, None
    elif code == 404:
        return False, 'Not found'
    elif code < 0:
        return {}, data
    else:
        return False, 'Unknown error'


def createLabel(
        namespace: str,
        repository: str,
        name: str,
        description: str = None,
        color: str = None):
    (data, code) = fetchJson(f"/repos/{namespace}/{repository}/labels", body={
        'name': name,
        'description': description,
        'color': color
    }, method='POST')

    if code >= 200 and code < 300:
        return True, None
    elif code == 404:
        return False, 'Resource not found'
    elif code == 422:
        return False, 'Validation failed'
    elif code < 0:
        return {}, data
    else:
        return False, 'Unknown error'


def updateLabel(
        namespace: str,
        repository: str,
        old_name: str,
        new_name: str = None,
        description: str = None,
        color: str = None):
    body = {}

    if new_name is not None:
        body['new_name'] = new_name
    if description is not None:
        body['description'] = description
    if color is not None:
        body['color'] = color

    (data, code) = fetchJson(
        f"/repos/{namespace}/{repository}/labels/{old_name}",
        body=body,
        method="PATCH")

    if code >= 200 and code < 300:
        return True, None
    elif code == 404:
        return False, 'Not found'
    elif code == 422:
        return False, 'Validation failed'
    elif code < 0:
        return {}, data
    else:
        return False, 'Unknown error'


def fetchRepositories(namespace: str):
    if namespace == '-':
        (data, code) = fetchPaginatedJson("/user/repos")
    else:
        (data, code) = fetchPaginatedJson(f"/orgs/{namespace}/repos")
        if code == 404:
            # FIXME: This only returns public repositories
            (data, code) = fetchPaginatedJson(f"/users/{namespace}/repos")

    if code >= 200 and code < 300:
        return data, None
    elif code == 404:
        return {}, 'Resource not found'
    elif code < 0:
        return {}, data
    else:
        return {}, 'Unknown error'


def parseLinkHeader(header: str):
    regex = re.compile(r'<(.*?)>(?:.*?)rel="([A-z\s]*)"')

    links = {}
    for match in regex.finditer(header):
        link = match.group(1)
        rel = match.group(2)

        links[rel] = link

    return links
