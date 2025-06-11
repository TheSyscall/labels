import json
from typing import Any
from typing import Union

from label_diff import Label
from label_diff import LabelDelta
from label_diff import LabelDeltaType
from label_diff import LabelDiff
from label_diff import LabelSpec


def create_json_report(diff: LabelDiff) -> str:
    """
    Creates a JSON representation of the given LabelDiff object.

    This function serializes a LabelDiff object into a JSON-formatted string,
    providing a structured representation of differences in labels. The
    output includes the namespace, repository, validity status, and
    specific label differences.

    Args:
        diff (LabelDiff): The object containing label comparison data to
        be converted into JSON format.

    Returns:
        str: A JSON-formatted string representing the label differences.
    """
    return json.dumps(
        {
            "namespace": diff.namespace,
            "repository": diff.repository,
            "valid": diff.valid,
            "missing": diff.missing,
            "extra": diff.extra,
            "diff": diff.diff,
        },
    )


def _create_markdown_table_header(columns: dict[str, Any]) -> str:
    """
    Generates a markdown table header string based on provided column names and
    their respective lengths.

    The function creates a header row for a markdown table using the provided
    column names, and it appends a separator line indicating the column widths.
    The first row represents the column titles, and the second row is a
    separator made of dashes to delimit the column headers.

    Parameters:
        columns (dict[str, Any]): A dictionary where keys are the names of the
            table columns, and
        the values represent the column widths.

    Returns:
        str: A string containing the formatted markdown table header, including
            both the column titles row and the separator row.
    """
    out = _create_markdown_table_row(columns, {key: key for key in columns})

    for column, length in columns.items():
        out += "|" + "-" * (length + 2)

    out += "|\n"

    return out


def _create_markdown_table_row(
    columns: dict[str, Any],
    row: dict[str, Any],
) -> str:
    """
    Generates a Markdown table row string by formatting given row data
    according to specified column names and their corresponding lengths.

    Args:
        columns (dict[str, Any]): A dictionary where keys are column names and
            values are the width of each column in characters.
        row (dict[str, Any]): A dictionary representing a single row of data,
            where keys are column names and values are their corresponding cell
            content.

    Returns:
        str: A formatted string representing the Markdown table row.
    """
    out = ""

    for column, length in columns.items():
        content = str(row[column]) if column in row else ""
        content = content.rjust(length)
        out += "| " + content + " "

    out += "|\n"

    return out


def _create_markdown_table(rows: list[dict[str, Any]]) -> str:
    """
    Generates a markdown table string representation from a list of
    dictionaries.

    The function creates a markdown table based on the provided rows, where
    each row is represented as a dictionary. It calculates the necessary column
    widths based on the longest cell value or header in each column, aligns the
    output, and properly formats header and rows to follow markdown table
    conventions.

    Args:
        rows (list[dict[str, Any]]): A list of dictionaries representing rows,
        where each dictionary contains column names as keys and row values as
        values.

    Returns:
        str: A string representation of the markdown table.
    """
    columns = {}

    for row in rows:
        for key, value in row.items():
            if key not in columns:
                columns[key] = len(key)
            value_length = len(str(value))

            if value_length > columns[key]:
                columns[key] = value_length

    out = _create_markdown_table_header(columns)
    for row in rows:
        out += _create_markdown_table_row(columns, row)

    return out


def create_markdown_table_report(diffs: list[LabelDiff]) -> str:
    """
    Generates a markdown table report based on label differences.

    This function processes a list of label differences to compute statistics
    for each repository, including counts of missing, extra, renamed,
    redescribed, and recolored labels. The data is then formatted into a
    markdown table string.

    Args:
        diffs (list[LabelDiff]): The list of label differences to be processed.

    Returns:
        str: A string representation of the markdown table summarizing the
            label differences.
    """
    rows = []

    for diff in diffs:
        name = 0
        description = 0
        color = 0

        for label in diff.diff:
            if LabelDeltaType.NAME in label.delta:
                name += 1
            if LabelDeltaType.DESCRIPTION in label.delta:
                description += 1
            if LabelDeltaType.COLOR in label.delta:
                color += 1

        rows.append(
            {
                "Repository": diff.repository,
                "Valid": len(diff.valid),
                "Missing": len(diff.missing),
                "Delete": len(diff.extra),
                "Rename": name,
                "Redescribe": description,
                "Recolor": color,
            },
        )

    return _create_markdown_table(rows)


def create_markdown_report(diff: LabelDiff) -> str:
    """
    Generates a markdown report summarizing label modifications, additions, and
    deletions based on the provided label difference data.

    The function takes a `LabelDiff` object and constructs a markdown string
    that outlines changes required to synchronize the repository labels with
    the given specifications. The report includes sections for missing labels,
    extra labels, and labels with differences in color, description, or name.

    Arguments:
        diff (LabelDiff): An object that represents the differences between the
            actual repository labels and the desired label specifications.

    Returns:
        str: A markdown-formatted string summarizing the required label
            changes.
    """
    out = f"## Repository: {diff.repository}\n"

    if not diff.is_change():
        out += "\nNothing to change!\n"
        return out

    if len(diff.missing) > 0:
        out += "\n### Missing Labels (Create)\n\n"
        for missing_label in diff.missing:
            out += f"- {missing_label.name}"
            if (
                missing_label.description is not None
                and missing_label.description != ""
            ):
                out += f": {missing_label.description}"
            out += "\n"

    if len(diff.extra) > 0:
        out += "\n### Extra Labels (Delete)\n\n"
        for extra_label in diff.extra:
            out += f"- {extra_label.name}"
            if (
                extra_label.description is not None
                and extra_label.description != ""
            ):
                out += f": {extra_label.description}"
            out += "\n"

    if len(diff.diff) > 0:
        out += "\n### Different Labels (Modify)\n\n"
        for label in diff.diff:
            out += f"- {label.spec.name}\n"
            if LabelDeltaType.COLOR in label.delta:
                out += (
                    f"  - Change color from '{label.actual.color}' "
                    f"to '{label.spec.color}'\n"
                )
            if LabelDeltaType.DESCRIPTION in label.delta:
                out += (
                    "  - Change description from "
                    f"'{label.actual.description}' to "
                    f"'{label.spec.description}'\n"
                )
            if LabelDeltaType.NAME in label.delta:
                out += (
                    f"  - Rename from '{label.actual.name}' to "
                    f"'{label.spec.name}'\n"
                )

    return out


def terminal_print(
    diff: LabelDiff,
    action: str,
    label: Union[Label, LabelSpec, LabelDelta],
) -> None:
    """
    Prints labeled differences between namespaces and repositories, describing
    actions performed such as deleting, creating, or modifying labels.
    The output is displayed in a human-readable format for console or terminal
    visualization.

    Parameters:
        diff (LabelDiff): Represents the difference between labels in terms of
            namespace and repository.
        action (str): Specifies the action performed on the label. Possible
            values include "delete", "create", or "modify".
        label (Union[Label, LabelSpec, LabelDelta]): Represents the label
            affected by the specified action and its associated details.

    Returns:
        None
    """
    print(f"{diff.namespace}/{diff.repository}: ", end="")
    if action == "delete":
        assert isinstance(label, Label)
        print(f"delete '{label.name}'")
    elif action == "create":
        assert isinstance(label, Label)
        print(f"create '{label.name}' ({label.description})")
    elif action == "modify":
        assert isinstance(label, LabelDelta)
        changes = []
        name = label.actual.name
        if LabelDeltaType.COLOR in label.delta:
            changes.append(
                f"change color of '{name}' from '{label.actual.color}' "
                f"to '{label.spec.color}'",
            )
        if LabelDeltaType.DESCRIPTION in label.delta:
            changes.append(
                f"change description of '{name}' from "
                f"'{label.actual.description}' to "
                f"'{label.spec.description}'",
            )
        if LabelDeltaType.NAME in label.delta:
            changes.append(
                f"rename from '{name}' to '{label.spec.name}'",
            )
        print(", ".join(changes))
