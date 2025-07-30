# Labels is a CLI tool to audit, sync, and manage Repository labels.
#
# Copyright (C) 2025 TheSyscall
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; If not, see <http://www.gnu.org/licenses/>.
import sys
from typing import Callable
from typing import Optional
from typing import Union

import github_api
from label_diff import Label
from label_diff import LabelDelta
from label_diff import LabelDiff


def _confirm() -> bool:
    """
    Checks user confirmation by prompting for input.

    This function continuously prompts the user to confirm an action by typing
    "y", "n", or pressing Enter. A response of "y" or an empty input (Enter)
    indicates confirmation, while "n" expresses denial.
    The function returns a boolean value based on the user's input.

    Returns:
        bool: True if the user confirms (input is "y" or empty), False if the
        user denies (input is "n").
    """
    while True:
        selection = input("Is this ok [Y/n]: ").lower()
        if selection == "n":
            return False
        elif selection == "y" or selection == "":
            return True


report_function = Callable[[LabelDiff, str, Union[Label, LabelDelta]], None]


def apply_create(
    diff: LabelDiff,
    yes: bool = False,
    report: Optional[report_function] = None,
) -> None:
    """
    Apply all create statements in the diff

    Arguments:
        diff (LabelDiff): the generated diff containing the actions
        yes (bool): did the user agree to all actions beforehand
        report (report_function): a report function that displays the actions
            to the user
    """
    for label in diff.missing:
        if report is not None:
            report(diff, "create", label)
        if not yes:
            if not _confirm():
                continue
        (response, err) = github_api.create_label(
            diff.namespace,
            diff.repository,
            label.name,
            label.description,
            label.color,
        )

        if err is not None:
            print(err, file=sys.stderr)


def apply_delete(
    diff: LabelDiff,
    yes: bool = False,
    report: Optional[report_function] = None,
) -> None:
    """
    Apply all delete statements in the diff

    Arguments:
        diff (LabelDiff): the generated diff containing the actions
        yes (bool): did the user agree to all actions beforehand
        report (report_function): a report function that displays the actions
         to the user
    """
    for label in diff.extra:
        if report is not None:
            report(diff, "delete", label)
        if not yes:
            if not _confirm():
                continue
        (response, err) = github_api.delete_label(
            diff.namespace,
            diff.repository,
            label.name,
        )

        if err is not None:
            print(err, file=sys.stderr)


def apply_modify(
    diff: LabelDiff,
    yes: bool = False,
    report: Optional[report_function] = None,
) -> None:
    """
    Apply all modify statements in the diff

    Arguments:
        diff (LabelDiff): the generated diff containing the actions
        yes (bool): did the user agree to all actions beforehand
        report (report_function): a report function that displays the actions
        to the user
    """
    for label in diff.diff:
        if report is not None:
            report(diff, "modify", label)
        if not yes:
            if not _confirm():
                continue

        color = label.spec.color
        description = label.spec.description

        (response, err) = github_api.update_label(
            diff.namespace,
            diff.repository,
            label.actual.name,
            description=description,
            color=color,
        )

        if err is not None:
            print(err, file=sys.stderr)
