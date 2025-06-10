import argparse
import json
import os
import sys

import actions
import github_api
import label_diff
import reports


def read_labels_from_json_file(path: str):
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

        labels = data["labels"]

        return labels
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


def load_source(source: str):
    return read_labels_from_json_file(source)


def parse_target(target: str):
    parts = target.split("/")

    if len(parts) == 2:
        return (parts[0], parts[1])
    elif len(parts) == 1:
        return (parts[0], None)
    else:
        print("Invalid target format!", file=sys.stderr)
        exit(2)


def parse_arguments():
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


def filter_repository(repository: dict) -> bool:
    if repository["archived"]:
        return False
    return True


def _report(format: str, diffs: list[label_diff.LabelDiff]):
    if format == "markdown":
        is_single_repo = len(diffs) == 1
        if not is_single_repo:
            print(f"# Namespace: {diffs[0].namespace}\n")
            print(reports.create_markdown_table_report(diffs))
        for diff in diffs:
            if is_single_repo or diff.isChange():
                print(reports.create_markdown_report(diff))
    elif format == "summary":
        print(reports.create_markdown_table_report(diffs))
    elif format == "json":
        # FIXME: Super hacky
        if len(diffs) > 0:
            data = []
            for diff in diffs:
                data.append(json.loads(reports.create_json_report(diff)))
            print(json.dumps(data))
            return
        print(reports.create_json_report(diff))
    elif format == "none":
        pass  # Nothing to do
    else:
        print(f"Unsupported format '{format}'", file=sys.stderr)


def command_report_namespace(args, namespace, truth):
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


def command_report_repository(args, namespace, repository, truth):
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


def command_reformat(args):
    diffs = load_json_report(args.source)
    _report(args.format, diffs)


def _apply(args, diff: label_diff.LabelDiff):
    if args.create:
        actions.apply_create(diff, args.assumeyes, reports.terminal_print)

    if args.delete:
        actions.apply_delete(diff, args.assumeyes, reports.terminal_print)

    if args.modify:
        actions.apply_modify(diff, args.assumeyes, reports.terminal_print)


def command_sync_namespace(args, namespace, truth):
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


def command_sync_repository(args, namespace, repository, truth):
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


def load_json_report(path: str):
    diffs = []
    with open(path, "r") as file:
        data = json.load(file)

    for jdiff in data:
        diff = label_diff.LabelDiff.from_dict(jdiff)
        diffs.append(diff)

    return diffs


def command_apply(args):
    for diff in load_json_report(args.source):
        _apply(args, diff)


def check_access_token(required: bool):
    if "GITHUB_ACCESS_TOKEN" not in os.environ:
        if required:
            print("Error: No access token defined!", file=sys.stderr)
            exit(1)
        print(
            "Warning: No access token defined. "
            "Only publicly visible data is available!",
            file=sys.stderr,
        )


def check_action_param(args):
    if not args.create and not args.delete and not args.modify:
        print(
            "At least one of --create, --delete, --modify must be set",
            file=sys.stderr,
        )
        exit(2)


def main():
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
