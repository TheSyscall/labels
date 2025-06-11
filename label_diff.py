from __future__ import annotations

from enum import auto
from enum import Enum
from typing import Any
from typing import cast
from typing import Optional


class Label:
    """
    Represents a label with a name, optional description, and color.

    This class provides a structure to handle labels which may include a name,
    a description, and a color. It also allows instantiation from a dictionary
    representation through a class method. Labels have an optional resolved
    alias that can be associated with them.

    Attributes:
        name: The name of the label, which is required.
        description: An optional description of the label providing additional
            details.
        color: An optional color associated with the label.
        resolved_alias: An optional resolved alias of type LabelSpec.
    """

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
        """
        Construct a `Label` instance from a dictionary object. The dictionary
        should contain keys corresponding to the attributes required to
        initialize the `Label` object. This method simplifies the creation of
        `Label` objects when data is available as a dictionary.

        Parameters:
            dict: A dictionary containing keys and values for initializing a
                `Label`. Expected to contain the following keys:
                    - name (str): The name of the label. This key is mandatory.
                    - description (Optional[str]): A brief description of the
                      label. This key is optional.
                    - color (Optional[str]): A string representing the color of
                      the label. This key is optional.

        Returns:
            Label: An instance of `Label` initialized with the values provided
                in the dictionary.
        """
        return cls(
            dict["name"],
            dict.get("description"),
            dict.get("color"),
        )


class LabelSpec(Label):
    """
    Represents a specified label with additional attributes.

    The LabelSpec class extends the basic label functionality by providing
    additional attributes, including whether the label is optional and a list
    of aliases. It can also be initialized directly from a dictionary, making
    it suitable for data-driven use cases.

    Attributes:
        optional (bool): Indicates if the label is optional.
        alias (list[str]): A list of aliases for the label.
    """

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
        """
        A factory method to create a LabelSpec instance from a dictionary.

        Given a dictionary containing the necessary fields for a LabelSpec,
        this method creates and returns a new instance of the LabelSpec class.

        Args:
            dict (dict[str, Any]): A dictionary containing fields such as
                "name", "description", "color", "optional", and "alias".
                These fields are used to populate the attributes of the
                LabelSpec instance. The "optional" field is set to False if not
                provided, and the "alias" field defaults to an empty list if
                not included in the dictionary.

        Returns:
            LabelSpec: A new instance of LabelSpec created with values from the
            input dictionary.
        """
        return cls(
            dict["name"],
            dict.get("description"),
            dict.get("color"),
            dict["optional"] if "optional" in dict else False,
            dict["alias"] if "alias" in dict else [],
        )


class LabelDeltaType(Enum):
    """
    Enumeration class representing different types of label modifications.
    """

    NAME = auto()
    DESCRIPTION = auto()
    COLOR = auto()


class LabelDelta:
    """
    Represents a label delta, containing a specification, an actual label,
    and the differences between them.

    This class encapsulates the relationship and differences between a
    specified label and an actual label based on a predefined delta type.
    It is used to manage and identify discrepancies between expected and
    observed label data.
    """

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
    """
    Represents a comparison or difference analysis of repository labels.

    This class encapsulates the results of a label diff in a repository
    context. It includes details about valid labels, missing labels, extra
    labels, and any specific differences. Used for analyzing label consistency
    in a repository namespace.

    Attributes:
        namespace: The namespace where the repository is located.
        repository: The specific repository being analyzed for label
            differences.
        valid: A list of labels that are valid and match the expected criteria.
        missing: A list of label specifications that are required but missing
            in the repository.
        extra: A list of labels present in the repository but not expected.
        diff: A list of label differences, showing specific changes between
            expected and existing labels.
    """

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
        """
        Create a LabelDiff instance from a dictionary.

        This method is used to create an instance of the LabelDiff class
        by extracting the relevant fields from a dictionary object. It
        allows for easy reconstruction of LabelDiff objects from serialized
        or stored data.

        Parameters:
            dict (dict[str, Any]): A dictionary containing the keys required
                                   to initialize the LabelDiff instance.
                                   The keys include:
                                       - "namespace" (str)
                                       - "repository" (str)
                                       - "valid"
                                       - "missing"
                                       - "extra"
                                       - "diff"

        Returns:
            LabelDiff: An instantiated LabelDiff object populated with the
                       data from the provided dictionary.
        """
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
    """
    Searches for a label with a specific name in a given list of labels.

    This function iterates through a list of Label objects and returns the
    first Label object whose name matches the given name.
    If no matching label is found, the function returns None.

    Args:
        list: A list of Label objects to search within.
        name: The name of the Label to search for.

    Returns:
        The matching Label object if found, or None if no match exists.
    """
    for label in list:
        if label.name == name:
            return label
    return None


def get_by_alias(
    true_list: list[LabelSpec],
    actual_label: Label,
) -> Optional[Label]:
    """
    This function retrieves a specific label from a list of label
    specifications when the provided actual label's name matches one of the
    aliases within a label specification. If no match is found, it returns
    None.

    Parameters:
    true_list (list[LabelSpec]): A list of LabelSpec objects, where each object
        contains a list of alias names.
    actual_label (Label): An actual label object to be checked against the list
        of aliases in the provided LabelSpec objects.

    Returns:
    Optional[Label]: The LabelSpec object matching the provided actual label's
        name within its alias list, or None if no match is found.
    """
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
    """
    Find and return an item from a list matching alias names.

    This function searches through a list of `Label` objects to find an object
    whose name matches any alias specified in a `LabelSpec` object. The first
    matching object found will be returned. If no alias matches any of the
    objects in the list, the function returns `None`.

    Arguments:
        actual_list: list[Label]
            A list of `Label` objects to search for a match.
        true_label: LabelSpec
            A `LabelSpec` object containing alias names to match against the
            `Label` objects in the list.

    Returns:
        Optional[Label]: The `Label` object that matches one of the aliases, or
        `None` if no match is found.
    """
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
    """
    Create a diff between the expected labels and actual labels in a
    repository.

    This function compares a list of expected labels (`truth`) with a list of
    actual labels (`actual`) to determine differences. It identifies labels
    that are missing, extra, or have differences such as mismatched
    descriptions, color changes, or name changes.

    Arguments:
        truth (list[LabelSpec]): A list of expected label specifications to
            compare against.
        actual (list[Label]): A list of actual labels retrieved to compare to
            the expected list.
        namespace (str): The namespace of the repository where labels are
            managed.
        repository (str): The repository where the comparison is performed.
        rename_alias (bool): A flag to include label name mismatches due to
            aliases in the diff.
        require_optional (bool): A flag to enforce consideration of optional
            labels.

    Returns:
        LabelDiff: An object that contains detailed results of the comparison,
        including valid labels, missing labels, extra labels, and detected
        differences.
    """
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
