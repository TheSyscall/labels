from label_diff import LabelDiff
import github_api


def _confirm():
    while True:
        selection = input("Is this ok [Y/n]: ").lower()
        if selection == "n":
            return False
        elif selection == "y" or selection == '':
            return True


def applyAllCreate(diff: LabelDiff, yes: bool = False, report=None):
    for label in diff.missing:
        if report is not None:
            report(diff, 'create', label)
        if not yes:
            if not _confirm():
                continue
        (response, err) = github_api.createLabel(
            diff.namespace,
            diff.repository,
            label['name'],
            label.get('description'),
            label.get('color')
        )


def applyAllDelete(diff: LabelDiff, yes: bool = False, report=None):
    for label in diff.extra:
        if report is not None:
            report(diff, 'delete', label)
        if not yes:
            if not _confirm():
                continue
        github_api.deleteLabel(diff.namespace, diff.repository, label['name'])


def applyAllModify(diff: LabelDiff, yes: bool = False, report=None):
    for label in diff.diff:
        if report is not None:
            report(diff, 'modify', label)
        if not yes:
            if not _confirm():
                continue
        github_api.updateLabel(
            diff.namespace,
            diff.repository,
            label['actual']['name'],
            description=label['truth']['description'] if 'description' in label['delta'] else None,
            color=label['truth']['color'] if 'color' in label['delta'] else None
        )
