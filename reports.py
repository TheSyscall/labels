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


def createMakrdownReport(diff: LabelDiff):
    out = f"## Repository: {diff.repository}\n\n"

    out += "### Valid Labels\n\n"
    if len(diff.valid) == 0:
        out += "<!-- no valid labels -->\n"
    else:
        out += f"Count: {len(diff.valid)}\n\n"
        for label in diff.valid:
            out += f" - {label['name']}"
            if "resolved_alias" in label:
                out += f" ({label['resolved_alias']})"
            if "description" in label and label["description"] != "":
                out += f": {label['description']}"
            out += "\n"

    out += "\n### Missing Labels (Create)\n\n"
    if len(diff.missing) == 0:
        out += "<!-- no missing labels -->\n"
    else:
        out += f"Count: {len(diff.missing)}\n\n"
        for label in diff.missing:
            out += f" - {label['name']}: {label['description']}\n"

    out += "\n### Extra Labels (Delete)\n\n"
    if len(diff.extra) == 0:
        out += "<!-- no extra labels -->\n"
    else:
        out += f"Count: {len(diff.extra)}\n\n"
        for label in diff.extra:
            out += f" - {label['name']}: {label['description']}\n"

    out += "\n### Different Labels (Modify)\n\n"
    if len(diff.diff) == 0:
        out += "<!-- no different labels -->\n"
    else:
        out += f"Count: {len(diff.diff)}\n\n"
        for label in diff.diff:
            out += f" - {label['truth']['name']}\n"
            if "color" in label["delta"]:
                out += f"   - Change color from: '{label['actual']['color']}' to '{label['truth']['color']}'\n"
            if "description" in label["delta"]:
                out += f"   - Change description from: '{label['actual']['description']}' to '{label['truth']['description']}'\n"
            if "name" in label["delta"]:
                out += f"   - Rename from: '{label['actual']['name']}' to '{label['truth']['name']}'\n"

    return out


def terminalPrint(diff: LabelDiff, action: str, label: dict):
    print(f"{diff.namespace}/{diff.repository}: ", end="")
    if action == "delete":
        print(f"delete '{label['name']}'")
    elif action == "create":
        print(f"create '{label['name']}' ({label['description']})")
    elif action == "modify":
        changes = []
        if "color" in label["delta"]:
            changes.append(
                f"change color of '{label['actual']['name']}' from '{label['actual']['color']}' to '{label['truth']['color']}'",
            )
        if "description" in label["delta"]:
            changes.append(
                f"change description of '{label['actual']['name']}' from '{label['actual']['description']}' to '{label['truth']['description']}'",
            )
        if "name" in label["delta"]:
            changes.append(
                f"rename from '{label['actual']['name']}' to '{label['truth']['name']}'",
            )
        print(", ".join(changes))
