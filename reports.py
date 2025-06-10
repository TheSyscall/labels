import json
from typing import Any
from typing import Union

from label_diff import Label
from label_diff import LabelDelta
from label_diff import LabelDeltaType
from label_diff import LabelDiff
from label_diff import LabelSpec


def create_json_report(diff: LabelDiff) -> str:
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
    out = _create_markdown_table_row(columns, {key: key for key in columns})

    for column, length in columns.items():
        out += "|" + "-" * (length + 2)

    out += "|\n"

    return out


def _create_markdown_table_row(
    columns: dict[str, Any],
    row: dict[str, Any],
) -> str:
    out = ""

    for column, length in columns.items():
        content = str(row[column]) if column in row else ""
        content = content.rjust(length)
        out += "| " + content + " "

    out += "|\n"

    return out


def _create_markdown_table(rows: list[dict[str, Any]]) -> str:
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
