from __future__ import annotations

from enum import auto
from enum import Enum
from typing import Any
from typing import cast
from typing import Optional


class Label:
    def __init__(
        self,
        name: str,
        description: Optional[str],
        color: Optional[str],
    ):
        self.name: str = name
        self.description: Optional[str] = description
        self.color: Optional[str] = color
        self.resolved_alias: Optional[LabelSpec] = None

    @classmethod
    def from_dict(cls, dict: dict[str, Any]) -> Label:
        return cls(
            dict["name"],
            dict.get("description"),
            dict.get("color"),
        )


class LabelSpec(Label):
    def __init__(
        self,
        name: str,
        description: Optional[str],
        color: Optional[str],
        optional: bool = False,
        alias: list[str] = [],
    ):
        super().__init__(name, description, color)
        self.optional: bool = optional
        self.alias: list[str] = alias

    @classmethod
    def from_dict(cls, dict: dict[str, Any]) -> LabelSpec:
        return cls(
            dict["name"],
            dict.get("description"),
            dict.get("color"),
            dict["optional"] if "optional" in dict else False,
            dict["alias"] if "alias" in dict else [],
        )


class LabelDeltaType(Enum):
    NAME = auto()
    DESCRIPTION = auto()
    COLOR = auto()


class LabelDelta:
    def __init__(
        self,
        spec: LabelSpec,
        actual: Label,
        delta: list[LabelDeltaType],
    ):
        self.spec: Label = spec
        self.actual: Label = actual
        self.delta: list[LabelDeltaType] = delta


class LabelDiff:
    def __init__(
        self,
        namespace: str,
        repository: str,
        valid: list[Label],
        missing: list[LabelSpec],
        extra: list[Label],
        diff: list[LabelDelta],
    ):
        self.namespace: str = namespace
        self.repository: str = repository
        self.valid: list[Label] = valid
        self.missing: list[LabelSpec] = missing
        self.extra: list[Label] = extra
        self.diff: list[LabelDelta] = diff

    def is_change(self) -> bool:
        return (
            len(self.missing) > 0 or len(self.extra) > 0 or len(self.diff) > 0
        )

    @classmethod
    def from_dict(cls, dict: dict[str, Any]) -> LabelDiff:
        return cls(
            dict["namespace"],
            dict["repository"],
            dict["valid"],
            dict["missing"],
            dict["extra"],
            dict["diff"],
        )


def get_by_name(
    list: list[Label],
    name: str,
) -> Optional[Label]:
    for label in list:
        if label.name == name:
            return label
    return None


def get_by_alias(
    true_list: list[LabelSpec],
    actual_label: Label,
) -> Optional[Label]:
    for true_label in true_list:
        if len(true_label.alias) == 0:
            continue
        if actual_label.name in true_label.alias:
            return true_label
    return None


def get_by_alias_reverse(
    actual_list: list[Label],
    true_label: LabelSpec,
) -> Optional[Label]:
    for alias in true_label.alias:
        for actual in actual_list:
            if actual.name == alias:
                return actual
    return None


def create_diff(
    truth: list[LabelSpec],
    actual: list[Label],
    namespace: str,
    repository: str,
    rename_alias: bool = False,
    require_optional: bool = False,
) -> LabelDiff:
    valid = []
    missing = []
    extra = []
    diff = []

    for true_label in truth:
        found_label = get_by_name(actual, true_label.name)
        if found_label is None:
            found_label = get_by_alias_reverse(actual, true_label)

        if found_label is None:
            if not require_optional and true_label.optional:
                continue

            missing.append(true_label)
            continue

        delta = []
        if true_label.description is not None:
            if true_label.description != found_label.description:
                delta.append(LabelDeltaType.DESCRIPTION)

        if true_label.color is not None:
            if true_label.color != found_label.color:
                delta.append(LabelDeltaType.COLOR)

        if rename_alias:
            if true_label.name != found_label.name:
                delta.append(LabelDeltaType.NAME)

        if len(delta) > 0:
            diff.append(LabelDelta(true_label, found_label, delta))
            continue
        if true_label.name != found_label.name:
            found_label.resolved_alias = true_label
        valid.append(found_label)

    for actual_label in actual:
        found_label = get_by_name(cast(list[Label], truth), actual_label.name)
        if found_label is None:
            found_label = get_by_alias(truth, actual_label)

        if found_label is None:
            extra.append(actual_label)

    return LabelDiff(namespace, repository, valid, missing, extra, diff)
