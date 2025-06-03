from label_diff import LabelDiff
import github_api


def applyAllCreate(diff: LabelDiff, report=None):
    for label in diff.missing:
        github_api.createLabel(
            diff.namespace,
            diff.repository,
            label['name'],
            label['description'],
            label['color']
        )
        if report is not None:
            report(diff, 'create', label)


def applyAllDelete(diff: LabelDiff, report=None):
    for label in diff.extra:
        github_api.deleteLabel(diff.namespace, diff.repository, label['name'])
        if report is not None:
            report(diff, 'delete', label)


def applyAllModify(diff: LabelDiff, report=None):
    for label in diff.diff:
        github_api.updateLabel(
            diff.namespace,
            diff.repository,
            label['actual']['name'],
            description=label['truth']['description'] if 'description' in label['delta'] else None,
            color=label['truth']['color'] if 'color' in label['delta'] else None
        )
        if report is not None:
            report(diff, 'modify', label)
