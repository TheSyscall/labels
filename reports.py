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


def createMarkdownReport(diff: LabelDiff):
    out = f"## Repository: {diff.repository}\n\n"

    if len(diff.missing) == 0 and len(diff.extra) == 0 and len(diff.diff) == 0:
        out += "Nothing to change!\n"

    if len(diff.missing) > 0:
        out += "\n### Missing Labels (Create)\n\n"
        for label in diff.missing:
            out += f" - {label['name']}: {label['description']}\n"

    if len(diff.extra) > 0:
        out += "\n### Extra Labels (Delete)\n\n"
        for label in diff.extra:
            out += f" - {label['name']}: {label['description']}\n"

    if len(diff.diff) > 0:
        out += "\n### Different Labels (Modify)\n\n"
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
