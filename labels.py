from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any
from typing import Optional
from typing import Tuple

import jsonschema

import actions
import github_api
import label_diff
import reports
from label_diff import LabelSpec


def validate_json_schema(data: dict[str, Any]) -> bool:
    """
    Validates a JSON object against a predefined schema specified in the file
    "labels-schema.json".

    The function ensures the structure and data types of the given JSON object
    match the expected schema. The schema is loaded from a file named
    "labels-schema.json" located in the same directory as the script.
    The function terminates execution if errors occur while loading or
    validating the schema. If validation is successful, a boolean value
    is returned.

    Parameters:
        data (dict[str, Any]): The JSON object to be validated.

    Returns:
        bool: True if the data adheres to the schema, otherwise the script
            terminates.
    """
    dirname = os.path.dirname(os.path.abspath(__file__))
    path = dirname + "/labels-schama.json"
    schema = None
    try:
        with open(dirname + "/labels-schema.json") as f:
            schema = json.load(f)
    except json.JSONDecodeError as e:
        print(
            f"Error while decoding schema file '{path}' "
            f"in line {e.lineno}: {e.msg}",
        )
        exit(1)
    except Exception as e:
        print(f"Error while schema file '{path}': ", file=sys.stderr, end="")
        if hasattr(e, "message"):
            print(e.message, file=sys.stderr)
        else:
            print(e, file=sys.stderr)
        exit(1)

    if schema is None:
        print("Empty schema!", file=sys.stderr)
        exit(1)

    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.exceptions.ValidationError as e:
        print(
            f"Error while verifying labels schema: {e.message}",
            file=sys.stderr,
        )
        exit(1)

    return True


def read_labels_from_json_file(path: str) -> list[LabelSpec]:
    """
    Reads and processes label specifications from a JSON file located at
    the provided path. The function validates the JSON schema, extracts label
    information, and returns a list of `LabelSpec` objects representing the
    parsed labels. If any errors occur during file reading, JSON parsing,
    or schema validation, the program will output error details and terminate.

    Parameters:
        path (str): The file path to the JSON file containing the label
            specifications.

    Returns:
        list[LabelSpec]: A list of `LabelSpec` objects parsed and validated
            from the input JSON file.

    Raises:
        json.JSONDecodeError: If the JSON file cannot be parsed due to invalid
            JSON structure.
        IOError: If there is an error opening or reading the file.
        SystemExit: If the file path does not exist, is not a file, or any
            unhandled exception occurs during the process.
    """
    if not os.path.exists(path):
        print(f"File not found: {path}", file=sys.stderr)
        exit(1)

    if not os.path.isfile(path):
        print(f"'{path}' is not a file", file=sys.stderr)
        exit(1)

    try:
        data = None
        with open(path, "r") as f:
            data = json.load(f)

        validate_json_schema(data)

        result: list[LabelSpec] = []
        for jdata in data["labels"]:
            result.append(LabelSpec.from_dict(jdata))

        return result
    except json.JSONDecodeError as e:
        print(
            f"Error while decoding json file '{path}' in"
            f" line {e.lineno}: {e.msg}",
        )
        exit(1)
    except IOError as e:
        print(f"Error while opening file '{path}': {e.strerror}")
        exit(1)
    except Exception as e:
        print(f"Error while opening file '{path}': ", file=sys.stderr, end="")
        if hasattr(e, "message"):
            print(e.message, file=sys.stderr)
        else:
            print(e, file=sys.stderr)
        exit(1)


def load_source(source: str) -> list[LabelSpec]:
    """
    Loads label specifications from a specified source.

    This function reads a JSON file containing label specifications and returns
    a list of `LabelSpec` objects. It is responsible for loading the data
    needed for labeling purposes.

    Arguments:
        source (str): The path to the JSON file containing label
            specifications.

    Returns:
        list[LabelSpec]: A list of label specification objects loaded from the
            file.
    """
    return read_labels_from_json_file(source)


def parse_target(target: str) -> Tuple[str, Optional[str]]:
    """
    Parses a target string into two components.

    This function takes a target string and attempts to split it into two parts
    separated by a forward slash ('/'). It expects either one or two components
    to be present. If exactly two components are identified, it returns both.
    If only one component is present, it returns that component along with a
    None value for the second part. If the format of the target string is
    invalid (i.e., it contains more than one slash), the function logs an error
    message to standard error and terminates the program.

    Arguments:
        target (str): A string representing the target to parse. It should be
            in the format "part1" or "part1/part2".

    Returns:
        A tuple containing either:
            - The first part of the target and the second part (if present) as
              a string.
            - The first part of the target and None, if the second part is
              missing.

    Raises:
        SystemExit: If the target has an invalid format (more than one '/').
    """
    parts = target.split("/")

    if len(parts) == 2:
        return parts[0], parts[1]
    elif len(parts) == 1:
        return parts[0], None
    else:
        print("Invalid target format!", file=sys.stderr)
        exit(2)


def parse_arguments() -> Any:
    """
    Parses and processes command-line arguments for managing GitHub repository
    labels.

    This function provides a command-line interface to perform operations such
    as reporting, synchronizing, applying reports, and reformatting label
    information for GitHub repositories. It supports various subcommands with
    configurable options.

    Returns:
        Any: A namespace containing the parsed command-line arguments.

    Raises:
        SystemExit: If required arguments are not provided or invalid arguments
        are passed when executing the script through the command line.
    """
    parser = argparse.ArgumentParser(
        description="Manage labels for a GitHub repository.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    report_parser = subparsers.add_parser(
        "report",
        help="Report the current state of the labels",
    )

    report_parser.add_argument(
        "-T",
        "--token",
        help="GitHub access token (also settable with a GITHUB_ACCESS_TOKEN"
        " environment variable)",
    )

    report_parser.add_argument(
        "target",
        metavar="namespace/repo",
        help="GitHub target in the format namespace/repo or namespace",
    )

    report_parser.add_argument(
        "-s",
        "--source",
        required=True,
        help="Path to the label source (file path)",
    )

    report_parser.add_argument(
        "-a",
        "--alias",
        action="store_true",
        help="List aliases as a modification",
    )

    report_parser.add_argument(
        "-o",
        "--optional",
        action="store_true",
        help="List optional labels as required",
    )

    report_parser.add_argument(
        "-f",
        "--format",
        choices=["markdown", "json", "summary"],
        default="markdown",
        help="Output format (default: markdown)",
    )

    sync_parser = subparsers.add_parser(
        "sync",
        help="Sync labels with a target",
    )

    sync_parser.add_argument(
        "-T",
        "--token",
        help="GitHub access token (also settable with a GITHUB_ACCESS_TOKEN"
        " environment variable)",
    )

    sync_parser.add_argument(
        "target",
        metavar="namespace/repo",
        help="GitHub target in the format namespace/repo or namespace",
    )

    sync_parser.add_argument(
        "-s",
        "--source",
        required=True,
        help="Path to the label source (file path)",
    )

    sync_parser.add_argument(
        "-c",
        "--create",
        action="store_true",
        help="Create labels",
    )

    sync_parser.add_argument(
        "-d",
        "--delete",
        action="store_true",
        help="Delete labels",
    )

    sync_parser.add_argument(
        "-m",
        "--modify",
        action="store_true",
        help="Modify existing labels",
    )

    sync_parser.add_argument(
        "-a",
        "--alias",
        action="store_true",
        help="Rename aliases to the canonical name",
    )

    sync_parser.add_argument(
        "-o",
        "--optional",
        action="store_true",
        help="Modify optional labels",
    )

    sync_parser.add_argument(
        "-y",
        "--assumeyes",
        action="store_true",
        help="Automatically answer yes for all questions",
    )

    apply_parser = subparsers.add_parser(
        "apply",
        help="Apply a report stored as a json file",
    )

    apply_parser.add_argument(
        "source",
        help="The report json file",
    )

    apply_parser.add_argument(
        "-T",
        "--token",
        help="GitHub access token (also settable with a GITHUB_ACCESS_TOKEN"
        "environment variable)",
    )

    apply_parser.add_argument(
        "-c",
        "--create",
        action="store_true",
        help="Create labels",
    )

    apply_parser.add_argument(
        "-d",
        "--delete",
        action="store_true",
        help="Delete labels",
    )

    apply_parser.add_argument(
        "-m",
        "--modify",
        action="store_true",
        help="Modify existing labels",
    )

    apply_parser.add_argument(
        "-y",
        "--assumeyes",
        action="store_true",
        help="Automatically answer yes for all questions",
    )

    reformat_parser = subparsers.add_parser(
        "reformat",
        help="Convert a json report into any of the other formats",
    )

    reformat_parser.add_argument(
        "source",
        help="The report json file",
    )

    reformat_parser.add_argument(
        "-f",
        "--format",
        choices=["markdown", "summary"],
        default="markdown",
        help="Output format (default: markdown)",
    )

    return parser.parse_args()


def filter_repository(repository: dict[str, Any]) -> bool:
    """
    Determines if a repository should be included based on its archived status.

    This function checks the 'archived' key of the given dictionary and
    returns False if the repository is archived, otherwise True. It is
    intended for filtering repositories and relies on the presence of the
    'archived' key in the input dictionary.

    Args:
        repository (dict[str, Any]): A dictionary containing information
        about a repository, with a required 'archived' key indicating
        whether the repository is archived.

    Returns:
        bool: False if the repository is archived, True otherwise.
    """
    if repository["archived"]:
        return False
    return True


def _report(report_format: str, diffs: list[label_diff.LabelDiff]) -> None:
    """
    Generates and prints a report based on the provided format and list of
    label differences. The content of the report varies depending on the format
    and the number of repositories involved.

    Args:
        report_format (str): The desired format of the report.
            Supported formats include

            - "markdown": Outputs a Markdown-styled report.
            - "summary": Outputs a Markdown-styled summary in table format.
            - "json": Outputs a JSON representation of the differences.
            - "none": Produces no output.
        diffs (list[label_diff.LabelDiff]): A list of label differences
            containing changes to be reported.
    """
    is_single_repo = len(diffs) == 1
    if report_format == "markdown":
        if not is_single_repo:
            print(f"# Namespace: {diffs[0].namespace}\n")
            print(reports.create_markdown_table_report(diffs))
        for diff in diffs:
            if is_single_repo or diff.is_change():
                print(reports.create_markdown_report(diff))
    elif report_format == "summary":
        print(reports.create_markdown_table_report(diffs))
    elif report_format == "json":
        # FIXME: Super hacky
        if not is_single_repo:
            data = []
            for diff in diffs:
                data.append(json.loads(reports.create_json_report(diff)))
            print(json.dumps(data))
            return
        print(reports.create_json_report(diffs[0]))
    elif report_format == "none":
        pass  # Nothing to do
    else:
        print(f"Unsupported format '{report_format}'", file=sys.stderr)


def command_report_namespace(
    args: Any,
    namespace: str,
    truth: list[LabelSpec],
) -> None:
    """
    Fetches repositories under a specified namespace, computes label
    differences against a predefined set of label specifications, and generates
    a report
     The function interacts with GitHub API to retrieve repository and label
    information, processes the data, and prints any errors to standard error
    stream if they occur. The function also terminates execution in case of
    critical failure.

    Parameters:
        args (Any): Command-line arguments that control the behavior of the
            report and the comparison process, such as formatting and optional
            parameters.
        namespace (str): The namespace (e.g., organization or user) from which
            repositories are fetched.
        truth (list[LabelSpec]): A predefined list of label specifications
            used as a reference for computing the differences.

    Raises:
        System exit with code 1 on critical errors encountered during
        repository or label data fetching.
    """
    (repos, err) = github_api.fetch_repositories(namespace)
    if err is not None:
        print(err, file=sys.stderr)
        exit(1)

    diffs = []

    for repo in repos:
        if not filter_repository(repo):
            continue
        _namespace = repo["owner"]["login"]
        _repo = repo["name"]

        (repo_lables, err) = github_api.fetch_labels(_namespace, _repo)
        if err is not None:
            print(err, file=sys.stderr)
            exit(1)

        diffs.append(
            label_diff.create_diff(
                truth,
                repo_lables,
                _namespace,
                _repo,
                args.alias,
                args.optional,
            ),
        )

    _report(args.format, diffs)


def command_report_repository(
    args: Any,
    namespace: str,
    repository: str,
    truth: list[LabelSpec],
) -> None:
    """
    Generates a report on differences between the expected and actual labels of
    a given GitHub repository.
    This function fetches the current state of the repository's labels,
    compares them with the expected label specifications, and outputs the
    differences in the specified format.

    Parameters:
        args (Any): Command-line arguments that control the behavior of the
            function, including the output format, alias handling, and optional
            label inclusion.
        namespace (str): The namespace or organization name of the GitHub
            repository.
        repository (str): The name of the repository for which the label report
            is generated.
        truth (list[LabelSpec]): A list of expected label specifications to
            compare against the repository's existing labels.

    Raises:
        System exit with code 1 on critical errors encountered during
        repository or label data fetching.
    """
    (repo, err) = github_api.fetch_labels(namespace, repository)
    if err is not None:
        print(err, file=sys.stderr)
        exit(1)

    diff = label_diff.create_diff(
        truth,
        repo,
        namespace,
        repository,
        args.alias,
        args.optional,
    )

    _report(args.format, [diff])


def command_reformat(args: Any) -> None:
    """
    Reformats the command output based on the specified format and source.

    The function processes a JSON report loaded from a source file, and then
    generates a formatted report as specified by the user.

    Args:
        args: Parsed arguments containing both the source path and the format
              to be used for the report.
    """
    diffs = load_json_report(args.source)
    _report(args.format, diffs)


def _apply(args: Any, diff: label_diff.LabelDiff) -> None:
    """
    Apply the specified changes to labels based on the provided configuration.

    This function serves as an entry point for applying create, delete, or
    modify operations on labels using the given arguments and label differences
    detected.

    Parameters:
        args (Any):
            Arguments indicating the operations to perform, along with
            additional options such as confirmation prompts.
        diff (LabelDiff):
            The computed differences between the current and desired label
            states.
    """
    if args.create:
        actions.apply_create(diff, args.assumeyes, reports.terminal_print)

    if args.delete:
        actions.apply_delete(diff, args.assumeyes, reports.terminal_print)

    if args.modify:
        actions.apply_modify(diff, args.assumeyes, reports.terminal_print)


def command_sync_namespace(
    args: Any,
    namespace: str,
    truth: list[LabelSpec],
) -> None:
    """
    Synchronizes labels of repositories within a given namespace to match the
    specified truth set.

    The function fetches all repositories under the specified namespace,
    applies filters, and synchronizes their label configurations to align with
    the truth set of labels. If there are any errors during API calls, they are
    printed to stderr, and the process exits.

    Parameters:
        args (Any): Command-line argument object containing configurations for
            the synchronization process, such as aliases and optional
            behaviors.
        namespace (str): The GitHub organization or user namespace whose
            repositories  are to be synchronized.
        truth (list[LabelSpec]): A list of LabelSpec objects that defines the
            desired label configuration to be applied to the repositories.

    Raises:
        SystemExit: Exits the program with exit code 1 if any errors occur
        while fetching repositories or labels.
    """
    (repos, err) = github_api.fetch_repositories(namespace)
    if err is not None:
        print(err, file=sys.stderr)
        exit(1)

    for repo in repos:
        if not filter_repository(repo):
            continue
        _namespace = repo["owner"]["login"]
        _repo = repo["name"]

        (repo_lables, err) = github_api.fetch_labels(_namespace, _repo)
        if err is not None:
            print(err, file=sys.stderr)
            exit(1)

        diff = label_diff.create_diff(
            truth,
            repo_lables,
            _namespace,
            _repo,
            args.alias,
            args.optional,
        )

        _apply(args, diff)


def command_sync_repository(
    args: Any,
    namespace: str,
    repository: str,
    truth: list[LabelSpec],
) -> None:
    """
    Synchronizes a GitHub repository's labels with a given "truth" list of
    labels.

    This function fetches the current labels of a specified GitHub repository,
    compares them with a provided "truth" list of expected labels, and applies
    any necessary updates to ensure the repository's labels match the "truth"
    list.
    The comparison process accounts for user-defined alias and optional label
    configurations.

    Parameters:
        args (Any): A structured object containing user-provided command-line
            arguments.
        namespace (str): The GitHub namespace (organization or user) owning the
            repository.
        repository (str): The name of the repository to sync labels for.
        truth (list[LabelSpec]): A list of label specifications representing
            the "truth" state to be reflected in the GitHub repository's
            labels.

    Raises:
        SystemExit: Exits the program with an error code and outputs an error
            message to standard error if fetching the repository labels fails.
    """
    (repo, err) = github_api.fetch_labels(namespace, repository)
    if err is not None:
        print(err, file=sys.stderr)
        exit(1)

    diff = label_diff.create_diff(
        truth,
        repo,
        namespace,
        repository,
        args.alias,
        args.optional,
    )

    _apply(args, diff)


def load_json_report(path: str) -> list[label_diff.LabelDiff]:
    """
    Load a JSON report file and convert its contents into a list of LabelDiff
    objects.

    This function reads a JSON file from the specified path, processes its
    content, and extracts differences, creating a list of LabelDiff objects.
    Each entry in the JSON file should represent a dictionary that can be
    converted into a LabelDiff object.

    Args:
        path: The file path to the JSON report to load.

    Returns:
        A list of LabelDiff objects created from the data in the JSON file.
    """
    diffs = []
    with open(path, "r") as file:
        data = json.load(file)

    for jdiff in data:
        diff = label_diff.LabelDiff.from_dict(jdiff)
        diffs.append(diff)

    return diffs


def command_apply(args: Any) -> None:
    """
    Applies a set of changes described in a JSON report to a target
    destination.
    The function iterates over a collection of differences obtained from a JSON
    report file and utilizes an internal helper function to process and apply
    each difference.

    Parameters:
        args (Any): An object containing the source path to the JSON report and
            other potential configurations required for applying changes.
    """
    for diff in load_json_report(args.source):
        _apply(args, diff)


def check_access_token(required: bool) -> None:
    """
    Checks the existence of the GitHub access token in the environment
    variables.

    This function ensures that a GitHub access token is available in the
    environment.
    If the access token is missing and the `required` parameter is set to True,
    it prints an error message and terminates the program.
    Otherwise, it issues a warning, indicating that only publicly visible data
    will be accessible.

    Parameters:
        required (bool): Indicates whether the access token is mandatory for
            the execution of the program.

    Raises:
        SystemExit: Exits the program with exit code 1 if the access token is
        missing and `required` is set to True.
    """
    if "GITHUB_ACCESS_TOKEN" not in os.environ:
        if required:
            print("Error: No access token defined!", file=sys.stderr)
            exit(1)
        print(
            "Warning: No access token defined. "
            "Only publicly visible data is available!",
            file=sys.stderr,
        )


def check_action_param(args: Any) -> None:
    """
    Checks if at least one action parameter (--create, --delete, --modify) is
    set.

    This function validates the input arguments to ensure that at least one of
    the specified action flags is set. If none of them are provided,
    it prints an error message to standard error and exits the program.

    Args:
        args (Any):
            The arguments object containing the action parameters such as
            --create, --delete, and --modify.
    """
    if not args.create and not args.delete and not args.modify:
        print(
            "At least one of --create, --delete, --modify must be set",
            file=sys.stderr,
        )
        exit(2)


def main() -> None:
    """
    Main entry point of the program. Handles the execution of commands based on
    the parsed arguments. Supports commands for reformatting, application of
    changes, generating reports, and synchronizing data.
    """
    args = parse_arguments()

    if args.command == "reformat":
        command_reformat(args)
        return

    if args.token is not None:
        os.environ["GITHUB_ACCESS_TOKEN"] = args.token

    if args.command == "apply":
        check_access_token(True)
        check_action_param(args)

        command_apply(args)
        return

    truth = load_source(args.source)

    (namespace, repository) = parse_target(args.target)

    if args.command == "report":
        check_access_token(False)

        if repository is None:
            command_report_namespace(args, namespace, truth)
            return

        command_report_repository(args, namespace, repository, truth)
        return

    elif args.command == "sync":
        check_access_token(True)
        check_action_param(args)

        if repository is None:
            command_sync_namespace(args, namespace, truth)
            return

        command_sync_repository(args, namespace, repository, truth)
        return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram terminated by user", file=sys.stderr)
        exit(0)
