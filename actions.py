from label_diff import LabelDiff
import github_api


def applyAllCreate(diff: LabelDiff):
    for label in diff.missing:
        github_api.createLabel(
            diff.namespace,
            diff.repository,
            label['name'],
            label['description'],
            label['color']
        )


def applyAllDelete(diff: LabelDiff):
    for label in diff.extra:
        github_api.deleteLabel(diff.namespace, diff.repository, label['name'])


def applyAllModify(diff: LabelDiff):
    for label in diff.diff:
        github_api.updateLabel(
            diff.namespace,
            diff.repository,
            label['actual']['name'],
            description=label['truth']['description'] if 'description' in label['delta'] else None,
            color=label['truth']['color'] if 'color' in label['delta'] else None
        )
