import sys
import json
import github_api
import actions
import reports
import label_diff


def readFromFile(path: str):
    data = None
    with open(path, 'r') as f:
        data = json.load(f)

    labels = data['labels']

    return labels


if __name__ == '__main__':
    truth = readFromFile('github-default.json')

    namespace = 'alex-s-awesome-org'
    repository = 'repoB'

    (repo, err) = github_api.fetchLabels(namespace, repository)
    if err is not None:
        print(err, file=sys.stderr)
        exit(1)

    diff = label_diff.createDiff(truth, repo, namespace, repository)

    print(reports.createMakrdownReport(diff))

    actions.applyAllCreate(diff)
    actions.applyAllDelete(diff)
    actions.applyAllModify(diff)
