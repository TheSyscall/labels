import json
from typing import Any

from label_diff import LabelDiff


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
            if "name" in label["delta"]:
                name += 1
            if "description" in label["delta"]:
                description += 1
            if "color" in label["delta"]:
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
        for label in diff.missing:
            out += f"- {label['name']}"
            if "description" in label and label["description"] != "":
                out += f": {label['description']}"
            out += "\n"

    if len(diff.extra) > 0:
        out += "\n### Extra Labels (Delete)\n\n"
        for label in diff.extra:
            out += f"- {label['name']}"
            if "description" in label and label["description"] != "":
                out += f": {label['description']}"
            out += "\n"

    if len(diff.diff) > 0:
        out += "\n### Different Labels (Modify)\n\n"
        for label in diff.diff:
            out += f"- {label['truth']['name']}\n"
            if "color" in label["delta"]:
                out += (
                    f"  - Change color from '{label['actual']['color']}' "
                    f"to '{label['truth']['color']}'\n"
                )
            if "description" in label["delta"]:
                out += (
                    "  - Change description from "
                    f"'{label['actual']['description']}' to "
                    f"'{label['truth']['description']}'\n"
                )
            if "name" in label["delta"]:
                out += (
                    f"  - Rename from '{label['actual']['name']}' to "
                    f"'{label['truth']['name']}'\n"
                )

    return out


def terminal_print(
    diff: LabelDiff,
    action: str,
    label: dict[str, Any],
) -> None:
    print(f"{diff.namespace}/{diff.repository}: ", end="")
    if action == "delete":
        print(f"delete '{label['name']}'")
    elif action == "create":
        print(f"create '{label['name']}' ({label['description']})")
    elif action == "modify":
        changes = []
        name = label["actual"]["name"]
        if "color" in label["delta"]:
            changes.append(
                f"change color of '{name}' from '{label['actual']['color']}' "
                f"to '{label['truth']['color']}'",
            )
        if "description" in label["delta"]:
            changes.append(
                f"change description of '{name}' from "
                f"'{label['actual']['description']}' to "
                f"'{label['truth']['description']}'",
            )
        if "name" in label["delta"]:
            changes.append(
                f"rename from '{name}' to '{label['truth']['name']}'",
            )
        print(", ".join(changes))
