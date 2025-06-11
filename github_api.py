import json
import os
import re
import sys
from typing import Any
from typing import Optional
from typing import Tuple
from typing import Union

import requests

from label_diff import Label


def fetch_json(
    endpoint: str,
    params: dict[str, Any] = {},
    body: dict[str, Any] = {},
    method: str = "GET",
) -> Tuple[Union[dict[str, Any], list[dict[str, Any]]], int, dict[str, Any]]:
    """
    Fetches JSON data from a specified API endpoint using a given HTTP method.
    Supports GET, POST, PATCH, and DELETE methods. The function accepts query
    parameters, a request body, and authorization headers, and returns the
    decoded JSON response, the HTTP status code, and the response headers.
    If the response cannot be decoded as JSON, the program exits with an error
    message.

    Args:
        endpoint (str): The API endpoint to fetch data from. Can be a full URL
            including the protocol, host, and port, or a relative path appended
            to the base GitHub API URL.
        params (dict[str, Any], optional): A dictionary of query parameters to
            include in the request. Defaults to an empty dictionary.
        body (dict[str, Any], optional): A dictionary of data to include in the
            request body for POST or PATCH requests. Defaults to an empty
            dictionary.
        method (str, optional): The HTTP method to use for the request.
            Accepts 'GET', 'POST', 'PATCH', or 'DELETE'. Defaults to 'GET'.

    Returns:
        Tuple[Union[dict[str, Any], list[dict[str, Any]]], int, dict[str, Any]]
            A tuple containing:
                - the parsed JSON response as a dictionary or list of
                  dictionaries
                - the HTTP status code as an integer
                - the response headers as a dictionary
    """
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

    match method:
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

    return result, response.status_code, dict(response.headers)


def fetch_paginated_json(
    endpoint: str,
    params: dict[str, Any] = {},
    body: dict[str, Any] = {},
    method: str = "GET",
) -> Tuple[list[dict[str, Any]], Optional[str]]:
    """
    Fetches paginated JSON data from a given endpoint and returns the combined
    content along with an optional error message if applicable.
    Supports handling of HTTP pagination through link headers and can process
    GET or other HTTP methods.

    Parameters:
        endpoint (str): The URL endpoint to fetch data from.
        params (dict[str, Any]): Query parameters to include in the request.
            Defaults to an empty dictionary.
        body (dict[str, Any]): Payload to send for non-GET requests, such
            as POST or PUT. Defaults to an empty dictionary.
        method (str): The HTTP method to use for the request. Defaults
            to "GET".

    Returns:
        Tuple[list[dict[str, Any]], Optional[str]] A tuple containing:
            - the combined content of all paginated responses as a list of
              dictionaries
            - An optional string containing an error message, or None if no
              error occurs.
    """
    content: list[dict[str, Any]] = []
    params["per_page"] = 100

    while True:
        (data, code, headers) = fetch_json(endpoint, params, body, method)

        if code >= 200 and code < 300:
            pass  # Nothing to do
        elif code == 404:
            return [], "Resource not found"
        else:
            return [], "Unknown error"

        assert isinstance(data, list)

        content += data

        if "Link" not in headers:
            break
        links = parse_link_header(headers["Link"])

        if "next" not in links:
            break

        endpoint = links["next"]

    return content, None


def fetch_labels(
    namespace: str,
    repository: str,
) -> Tuple[list[Label], Optional[str]]:
    """
    Fetches a list of labels for a specified repository.

    This function retrieves labels associated with a specific repository within
    a given namespace. The labels are extracted from the API response and
    returned as a list of label objects. It returns an error string in case the
    API request fails.

    Arguments:
        namespace (str): The namespace or organization of the repository.
        repository (str): The repository name for which labels are to be
            fetched.

    Returns:
        Tuple[list[Label], Optional[str]] A tuple containing:
            - A list of Label objects if the operation is successful;
              otherwise, an empty list.
            - An optional string containing an error message, or None if no
              error occurs.
    """
    (data, err) = fetch_paginated_json(
        f"/repos/{namespace}/{repository}/labels",
    )

    if err:
        return [], err

    result = []
    for jdata in data:
        result.append(Label.from_dict(jdata))

    return result, None


def delete_label(
    namespace: str,
    repository: str,
    label: str,
) -> Tuple[bool, Optional[str]]:
    """
    Deletes a specific label from a repository in the given namespace.

    This function sends an HTTP DELETE request to remove a label from
    a specified repository. The function returns a tuple indicating
    whether the operation was successful and an optional error message
    if it was not.

    Parameters:
        namespace (str): The namespace under which the repository is located.
        repository (str): The name of the repository from which the label is to
            be deleted.
        label (str): The name of the label to be deleted.

    Returns:
        Tuple[bool, Optional[str]] A tuple containing:
            - a boolean indicating success  (True) or failure (False) of the
              operation.
            - an optional string containing an error message if the operation
              failed.
    """
    (data, code, _) = fetch_json(
        f"/repos/{namespace}/{repository}/labels/{label}",
        method="DELETE",
    )

    if code >= 200 and code < 300:
        return True, None
    elif code == 404:
        return False, "Not found"
    else:
        return False, "Unknown error"


def create_label(
    namespace: str,
    repository: str,
    name: str,
    description: Optional[str] = None,
    color: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Create a new label in the specified repository within a given namespace.

    This function sends a POST request to the repository API to create a label
    with the specified name, and optionally, a description and color.
    It returns a tuple indicating the success status of the operation and an
    optional error message if the operation was not successful.

    Arguments:
        namespace (str): The namespace or organization owning the repository.
        repository (str): The repository name where the label will be created.
        name (str): The name of the label to be created.
        description (Optional[str]): The optional description of the label.
        color (Optional[str]): The RGB hex code of the label color
            (e.g., 'ff5733').

    Returns:
        Tuple[bool, Optional[str]]: A tuple containing:
            - a boolean indicating success  (True) or failure (False) of the
              operation.
            - an optional string containing an error message if the
              operation failed.
    """
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
    else:
        return False, "Unknown error"


def update_label(
    namespace: str,
    repository: str,
    old_name: str,
    new_name: Optional[str] = None,
    description: Optional[str] = None,
    color: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Updates a label in a specified repository with new values for its
    properties.
    Allows changing the name, description, and color of the label.
    Returns the result of the update operation.

    Arguments:
        namespace (str): The namespace of the repository
            (e.g., organization or username).
        repository (str): The name of the repository containing the label to
            update.
        old_name (str): The current name of the label to be updated.
        new_name (Optional[str]): The new name for the label (if provided).
            Defaults to None.
        description (Optional[str]): A description to update the label with
            (if provided). Defaults to None.
        color (Optional[str]): A new color for the label in hexadecimal format
            (if provided). Defaults to None.

    Returns:
        Tuple[bool, Optional[str]] A tuple containing:
            - a boolean indicating success  (True) or failure (False) of the
              operation.
            - an optional string containing an error message if the
              operation failed.
    """
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
    else:
        return False, "Unknown error"


def fetch_repositories(
    namespace: str,
) -> Tuple[list[dict[str, Any]], Optional[str]]:
    """
    Fetch a list of repositories for the given namespace.

    This function retrieves all repositories associated with a specific
    namespace, which can be a user or an organization.
    If the namespace is "-", it fetches the repositories for the authenticated
    user. It uses pagination to ensure that all repositories are retrieved.
    An error, if occurred during either fetch attempt, is also returned.

    Parameters:
        namespace (str): The namespace for which the repositories should be
            fetched. This can be the name of a user, an organization, or "-"
            for the authenticated user.

    Returns:
        tuple[list[dict[str, Any]], Optional[str]]
            A tuple containing:
                - A list of dictionaries, where each dictionary represents a
                  single repository and its details.
                - An optional string representing any error message encountered
                  while attempting to fetch the repositories.
    """
    if namespace == "-":
        (data, err) = fetch_paginated_json("/user/repos")
    else:
        (data, err) = fetch_paginated_json(f"/orgs/{namespace}/repos")
        if err is not None:
            (data, err) = fetch_paginated_json(f"/users/{namespace}/repos")

    return data, err


def parse_link_header(header: str) -> dict[str, str]:
    """
    Parses the provided HTTP Link header into a dictionary where the keys
    are the "rel" attributes and the values are the corresponding URLs.

    The function uses a regular expression to find all link entries and
    extracts the "rel" attribute and the corresponding URL. It stores this
    information in a dictionary and returns the result.

    Arguments:
        header (str): The HTTP Link header string to be parsed.

    Returns:
        dict[str, str]: A dictionary mapping "rel" attributes to their
        corresponding URLs.
    """
    regex = re.compile(r'<(.*?)>(?:.*?)rel="([A-z\s]*)"')

    links = {}
    for match in regex.finditer(header):
        link = match.group(1)
        rel = match.group(2)

        links[rel] = link

    return links
