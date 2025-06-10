import sys

import github_api
from label_diff import LabelDiff


def _confirm():
    while True:
        selection = input("Is this ok [Y/n]: ").lower()
        if selection == "n":
            return False
        elif selection == "y" or selection == "":
            return True


def apply_create(diff: LabelDiff, yes: bool = False, report=None):
    for label in diff.missing:
        if report is not None:
            report(diff, "create", label)
        if not yes:
            if not _confirm():
                continue
        (response, err) = github_api.create_label(
            diff.namespace,
            diff.repository,
            label["name"],
            label.get("description"),
            label.get("color"),
        )

        if err is not None:
            print(err, file=sys.stderr)


def apply_delete(diff: LabelDiff, yes: bool = False, report=None):
    for label in diff.extra:
        if report is not None:
            report(diff, "delete", label)
        if not yes:
            if not _confirm():
                continue
        (response, err) = github_api.delete_label(
            diff.namespace,
            diff.repository,
            label["name"],
        )

        if err is not None:
            print(err, file=sys.stderr)


def apply_modify(diff: LabelDiff, yes: bool = False, report=None):
    for label in diff.diff:
        if report is not None:
            report(diff, "modify", label)
        if not yes:
            if not _confirm():
                continue

        color = label["truth"]["color"] if "color" in label["delta"] else None
        description = (
            label["truth"]["description"]
            if "description" in label["delta"]
            else None
        )

        (response, err) = github_api.update_label(
            diff.namespace,
            diff.repository,
            label["actual"]["name"],
            description=description,
            color=color,
        )

        if err is not None:
            print(err, file=sys.stderr)
