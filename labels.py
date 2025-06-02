import sys
import json
import github_api


def readFromFile(path: str):
    data = None
    with open(path, 'r') as f:
        data = json.load(f)

    labels = data['labels']

    return labels


def getByName(list: dict, name: str):
    for label in list:
        if label['name'] == name:
            return label
    return None


class LabelDiff:
    def __init__(self, namespace, repository, valid, missing, extra, diff):
        self.namespace = namespace
        self.repository = repository
        self.valid = valid
        self.missing = missing
        self.extra = extra
        self.diff = diff


def createDiff(truth: dict, actual: dict, namespace: str, repository: str):
    # return: valid, missing, extra, diff

    valid = []
    missing = []
    extra = []
    diff = []

    for true_label in truth:
        found_label = getByName(actual, true_label['name'])
        if found_label is None:
            missing.append(true_label)
            continue

        delta = []
        if 'description' in true_label:
            true_description = true_label['description'] if true_label['description'] is not None else ''
            if true_description != found_label['description']:
                delta.append('description')

        if 'color' in true_label and true_label['color'] is not None:
            if true_label['color'] != found_label['color']:
                delta.append('color')

        if len(delta) > 0:
            diff.append({
                'truth': true_label,
                'actual': found_label,
                'delta': delta,
            })
            continue
        valid.append(true_label)

    for actual_label in actual:
        found_label = getByName(truth, actual_label['name'])

        if found_label is None:
            extra.append(actual_label)

    return LabelDiff(namespace, repository, valid, missing, extra, diff)


def createJsonReport(diff: LabelDiff):
    return json.dumps({
        'valid': diff.valid,
        'missing': diff.missing,
        'extra': diff.extra,
        'diff': diff.diff,
    }, indent=4)


def createMakrdownReport(diff: LabelDiff):
    out = f"# {diff.repository}\n\n"

    out += "## Valid Labels\n\n"
    if len(diff.valid) == 0:
        out += "<!-- no valid labels -->\n"
    else:
        out += f"Count: {len(diff.valid)}\n\n"
        for label in diff.valid:
            out += f" - {label['name']}\n"

    out += "\n## Missing Labels (Create)\n\n"
    if len(diff.missing) == 0:
        out += "<!-- no missing labels -->\n"
    else:
        out += f"Count: {len(diff.missing)}\n\n"
        for label in diff.missing:
            out += f" - {label['name']}: {label['description']}\n"

    out += "\n## Extra Labels (Delete)\n\n"
    if len(diff.extra) == 0:
        out += "<!-- no extra labels -->\n"
    else:
        out += f"Count: {len(diff.extra)}\n\n"
        for label in diff.extra:
            out += f" - {label['name']}: {label['description']}\n"

    out += "\n## Different Labels (Modify)\n\n"
    if len(diff.diff) == 0:
        out += "<!-- no different labels -->\n"
    else:
        out += f"Count: {len(diff.diff)}\n\n"
        for label in diff.diff:
            out += f" - {label['truth']['name']}\n"
            if 'color' in label['delta']:
                out += f"   - Change color from: '{label['actual']['color']}' to '{label['truth']['color']}'\n"
            if 'description' in label['delta']:
                out += f"   - Change description from: '{label['actual']['description']}' to '{label['truth']['description']}'\n"

    return out


def applyCreate(diff: LabelDiff):
    for label in diff.missing:
        github_api.createLabel(
            diff.namespace,
            diff.repository,
            label['name'],
            label['description'],
            label['color']
        )


def applyDelete(diff: LabelDiff):
    for label in diff.extra:
        github_api.deleteLabel(diff.namespace, diff.repository, label['name'])


def applyModify(diff: LabelDiff):
    for label in diff.diff:
        print(github_api.updateLabel(
            diff.namespace,
            diff.repository,
            label['actual']['name'],
            description=label['truth']['description'] if 'description' in label['delta'] else None,
            color=label['truth']['color'] if 'color' in label['delta'] else None
        ))


if __name__ == '__main__':
    truth = readFromFile('github-default.json')

    namespace = 'alex-s-awesome-org'
    repository = 'repoA'

    (repo, err) = github_api.fetchLabels(namespace, repository)
    if err is not None:
        print(err, file=sys.stderr)
        exit(1)

    diff = createDiff(truth, repo, namespace, repository)

    print(createMakrdownReport(diff))

    # applyCreate(diff)
    # applyDelete(diff)
    # applyModify(diff)
