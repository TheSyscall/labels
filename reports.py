import json

from label_diff import LabelDiff


def createJsonReport(diff: LabelDiff):
    return json.dumps(
        {
            "valid": diff.valid,
            "missing": diff.missing,
            "extra": diff.extra,
            "diff": diff.diff,
        },
    )


def _createMarkdownTableHeader(columns: dict) -> str:
    out = _createMarkdownTableRow(columns, {key: key for key in columns})

    for column, length in columns.items():
        out += "|" + "-" * (length + 2)

    out += "|\n"

    return out


def _createMarkdownTableRow(columns: dict, row: dict) -> str:
    out = ""

    for column, length in columns.items():
        content = str(row[column]) if column in row else ""
        content = content.rjust(length)
        out += "| " + content + " "

    out += "|\n"

    return out


def _createMarkdownTable(rows: list):
    columns = {}

    for row in rows:
        for key, value in row.items():
            if key not in columns:
                columns[key] = len(key)
            value_length = len(str(value))

            if value_length > columns[key]:
                columns[key] = value_length

    out = _createMarkdownTableHeader(columns)
    for row in rows:
        out += _createMarkdownTableRow(columns, row)

    return out


def createMarkdownTableReport(diffs: list[LabelDiff]):
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

    return _createMarkdownTable(rows)


def createMarkdownReport(diff: LabelDiff):
    out = f"## Repository: {diff.repository}\n"

    if not diff.isChange():
        out += "\nNothing to change!\n"
        return out

    if len(diff.missing) > 0:
        out += "\n### Missing Labels (Create)\n\n"
        for label in diff.missing:
            out += f" - {label['name']}"
            if "description" in label and label["description"] != "":
                out += f": {label['description']}"
            out += "\n"

    if len(diff.extra) > 0:
        out += "\n### Extra Labels (Delete)\n\n"
        for label in diff.extra:
            out += f" - {label['name']}"
            if "description" in label and label["description"] != "":
                out += f": {label['description']}"
            out += "\n"

    if len(diff.diff) > 0:
        out += "\n### Different Labels (Modify)\n\n"
        for label in diff.diff:
            out += f" - {label['truth']['name']}\n"
            if "color" in label["delta"]:
                out += f"   - Change color from '{label['actual']['color']}' to '{label['truth']['color']}'\n"
            if "description" in label["delta"]:
                out += f"   - Change description from '{label['actual']['description']}' to '{label['truth']['description']}'\n"
            if "name" in label["delta"]:
                out += f"   - Rename from '{label['actual']['name']}' to '{label['truth']['name']}'\n"

    return out


def terminalPrint(diff: LabelDiff, action: str, label: dict):
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
                f"change color of '{name}' from '{label['actual']['color']}' to '{label['truth']['color']}'",
            )
        if "description" in label["delta"]:
            changes.append(
                f"change description of '{name}' from '{label['actual']['description']}' to '{label['truth']['description']}'",
            )
        if "name" in label["delta"]:
            changes.append(
                f"rename from '{name}' to '{label['truth']['name']}'",
            )
        print(", ".join(changes))
