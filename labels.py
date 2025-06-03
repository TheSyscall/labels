import sys
import json
import github_api
import actions
import reports
import label_diff
import argparse


def readFromFile(path: str):
    data = None
    with open(path, 'r') as f:
        data = json.load(f)

    labels = data['labels']

    return labels


def loadSource(source: str):
    return readFromFile(source)


def parseTarget(target: str):
    parts = target.split('/')

    if len(parts) == 2:
        return (parts[0], parts[1])
    elif len(parts) == 1:
        return (parts[0], None)
    else:
        print("Invalid target format!", file=sys.stderr)
        exit(2)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Manage labels for a GitHub repository.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    report_parser = subparsers.add_parser(
        "report",
        help="Report the current state of the labels")

    report_parser.add_argument(
        "target",
        metavar="namespace/repo",
        help="GitHub target in the format namespace/repo or namespace")

    report_parser.add_argument(
        "-s",
        "--source",
        required=True,
        help="Path to the label source (file path)")

    report_parser.add_argument(
        "-f",
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown)")

    sync_parser = subparsers.add_parser(
        "sync",
        help="Sync labels with a target")

    sync_parser.add_argument(
        "target",
        metavar="namespace/repo",
        help="GitHub target in the format namespace/repo or namespace")

    sync_parser.add_argument(
        "-s",
        "--source",
        required=True,
        help="Path to the label source (file path)")

    sync_parser.add_argument(
        "-c",
        "--create",
        action="store_true",
        help="Automatically create labels")

    sync_parser.add_argument(
        "-d",
        "--delete",
        action="store_true",
        help="Automatically delete labels")

    sync_parser.add_argument(
        "-m",
        "--modify",
        action="store_true",
        help="Automatically modify existing labels")

    sync_parser.add_argument(
        "-y",
        "--assumeyes",
        action="store_true",
        help="Automatically answer yes for all questions")

    sync_parser.add_argument(
        "-f",
        "--format",
        choices=["markdown", "json", "none"],
        default="none",
        help="Output format (default: none)")

    return parser.parse_args()


def _report(format: str, diff: label_diff.LabelDiff):
    if format == "markdown":
        print(reports.createMakrdownReport(diff))
    elif format == "json":
        print(reports.createJsonReport(diff))
    elif format == "none":
        pass  # Nothing to do
    else:
        print(f"Unsupported format '{format}'", file=sys.stderr)


def main():
    args = parse_arguments()

    if args.command == 'report':
        truth = loadSource(args.source)

        (namespace, repository) = parseTarget(args.target)

        if repository is None:
            print("Generting reports for namespaces isn't supported yet",
                  file=sys.stderr)
            exit(1)

        (repo, err) = github_api.fetchLabels(namespace, repository)
        if err is not None:
            print(err, file=sys.stderr)
            exit(1)

        diff = label_diff.createDiff(truth, repo, namespace, repository)

        _report(args.format, diff)

    elif args.command == 'sync':
        truth = loadSource(args.source)

        (namespace, repository) = parseTarget(args.target)

        if repository is None:
            print("Syncing labels for namespaces isn't supported yet",
                  file=sys.stderr)
            exit(1)

        (repo, err) = github_api.fetchLabels(namespace, repository)
        if err is not None:
            print(err, file=sys.stderr)
            exit(1)

        diff = label_diff.createDiff(truth, repo, namespace, repository)

        if not args.create and not args.delete and not args.modify:
            print("At least one of --create, --delete, --modify must be set",
                  file=sys.stderr)
            exit(2)

        if args.create:
            actions.applyAllCreate(diff, args.assumeyes, reports.terminalPrint)

        if args.delete:
            actions.applyAllDelete(diff, args.assumeyes, reports.terminalPrint)

        if args.modify:
            actions.applyAllModify(diff, args.assumeyes, reports.terminalPrint)

        _report(args.format, diff)


if __name__ == '__main__':
    main()
