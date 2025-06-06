import requests
import os
import re


def fetchJson(endpoint: str, params={}, body={}, method="GET"):
    base_url = "https://api.github.com"
    url = base_url + endpoint
    if endpoint.startswith('http'):
        url = endpoint

    headers = {
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
    }

    token = os.getenv('GITHUB_ACCESS_TOKEN')
    if token is not None and token != '':
        headers['Authorization'] = 'token ' + token

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

    return content, None


def fetchLabels(namespace: str, repository: str):
    return fetchPaginatedJson(f"/repos/{namespace}/{repository}/labels")


def deleteLabel(namespace: str, repository: str, label: str):
    (data, code, _) = fetchJson(f"/repos/{namespace}/{repository}/labels/{label}",
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
    body = {
        'name': name,
    }

    if description is not None:
        body['description'] = description
    if color is not None:
        body['color'] = color

    (data, code, _) = fetchJson(f"/repos/{namespace}/{repository}/labels", body=body, method='POST')

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

    (data, code, _) = fetchJson(
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
        (data, err) = fetchPaginatedJson("/user/repos")
    else:
        (data, err) = fetchPaginatedJson(f"/orgs/{namespace}/repos")
        if err is not None:
            (data, err) = fetchPaginatedJson(f"/users/{namespace}/repos")

    return data, err


def parseLinkHeader(header: str):
    regex = re.compile(r'<(.*?)>(?:.*?)rel="([A-z\s]*)"')

    links = {}
    for match in regex.finditer(header):
        link = match.group(1)
        rel = match.group(2)

        links[rel] = link

    return links
