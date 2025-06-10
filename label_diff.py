class LabelDiff:
    def __init__(self, namespace, repository, valid, missing, extra, diff):
        self.namespace = namespace
        self.repository = repository
        self.valid = valid
        self.missing = missing
        self.extra = extra
        self.diff = diff

    def is_change(self):
        return (
            len(self.missing) > 0 or len(self.extra) > 0 or len(self.diff) > 0
        )

    @classmethod
    def from_dict(cls, dict: dict):
        return cls(
            dict["namespace"],
            dict["repository"],
            dict["valid"],
            dict["missing"],
            dict["extra"],
            dict["diff"],
        )


def get_by_name(list: dict, name: str):
    for label in list:
        if label["name"] == name:
            return label
    return None


def get_by_alias(true_list: dict, actual_label: dict):
    for true_label in true_list:
        if "alias" not in true_label:
            continue
        if actual_label["name"] in true_label["alias"]:
            return true_label
    return None


def get_by_alias_reverse(actual_list: dict, true_label: dict):
    if "alias" not in true_label:
        return None
    for alias in true_label["alias"]:
        for actual in actual_list:
            if actual["name"] == alias:
                return actual
    return None


def create_diff(
    truth: dict,
    actual: dict,
    namespace: str,
    repository: str,
    rename_alias: bool = False,
    require_optional: bool = False,
):
    valid = []
    missing = []
    extra = []
    diff = []

    for true_label in truth:
        found_label = get_by_name(actual, true_label["name"])
        if found_label is None:
            found_label = get_by_alias_reverse(actual, true_label)

        if found_label is None:
            if (
                not require_optional
                and "optional" in true_label
                and true_label["optional"]
            ):
                continue

            missing.append(true_label)
            continue

        delta = []
        if "description" in true_label:
            true_description = (
                true_label["description"]
                if true_label["description"] is not None
                else ""
            )
            if true_description != found_label["description"]:
                delta.append("description")

        if "color" in true_label and true_label["color"] is not None:
            if true_label["color"] != found_label["color"]:
                delta.append("color")

        if rename_alias:
            if true_label["name"] != found_label["name"]:
                delta.append("name")

        if len(delta) > 0:
            diff.append(
                {
                    "truth": true_label,
                    "actual": found_label,
                    "delta": delta,
                },
            )
            continue
        if true_label["name"] != found_label["name"]:
            found_label["resolved_alias"] = true_label["name"]
        valid.append(found_label)

    for actual_label in actual:
        found_label = get_by_name(truth, actual_label["name"])
        if found_label is None:
            found_label = get_by_alias(truth, actual_label)

        if found_label is None:
            extra.append(actual_label)

    return LabelDiff(namespace, repository, valid, missing, extra, diff)
