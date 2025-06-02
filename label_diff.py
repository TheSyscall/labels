
class LabelDiff:
    def __init__(self, namespace, repository, valid, missing, extra, diff):
        self.namespace = namespace
        self.repository = repository
        self.valid = valid
        self.missing = missing
        self.extra = extra
        self.diff = diff


def getByName(list: dict, name: str):
    for label in list:
        if label['name'] == name:
            return label
    return None


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
