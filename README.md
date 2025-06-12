# GitHub Label Manager

A command-line tool to manage labels in GitHub repositories.
This tool allows you to generate reports, apply label specifications,
sync repositories, and convert reports between formats.

## ✨ Features

- Generate label reports comparing current GitHub state to specification files
- Apply or sync label changes (create, modify, delete)
- Handle optional labels and aliases
- Output in multiple formats: JSON, Markdown, Summary
- Automate workflows with non-interactive execution

## 🚀 Installation

Clone the repository and run the script using Python 3:

```bash
git clone https://github.com/thesyscall/labels.git
cd labels
pip install -r requirements.txt
```

## 🔑 Authentication

A GitHub Personal Access Token (PAT) is required for most operations.
You can read about how you can create one
[here](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens).

You can provide it via:

- `--token` or `-T` option
- GITHUB_ACCESS_TOKEN environment variable

## 🛠 Usage

### Generate Reports (report)

Compares a repository's labels with one or more specification files.

```bash
python label.py report \
    ariess-labels-test/repoA \
    --source github-default.json \
    --format markdown > report.md
```

Options:

- `--source`, `-s`: Path to label specification file
(required, can be repeated)
- `--format`, `-f`: Output format (markdown, json, summary) (default: markdown)
- `--optional`, `-o`: Include optional labels as required
- `--alias`, `-a`: Treat aliases as modifications

### Apply a Report (apply)

Executes changes described in a previously generated JSON report.

```bash
python label.py apply \
    report.json \
    -cmd
```

Options:

- `--create`, `-c`: Create missing labels
- `--modify`, `-m`: Modify existing labels (description, color, aliases)
- `--delete`, `-d`: Delete labels not in the spec
- `--assumeyes`, `-y`: Automatically confirm all actions

### Sync Labels (sync)

Performs the same steps as report + apply in a single command.

```bash
python label.py sync \
    ariess-labels-test/repoA \
    --source github-default.json \
    -cmd -y
```

Options:

Same as report + apply.

### Convert Report Format (reformat)

Converts an existing JSON report to another format for display or sharing.

```bash
python label.py reformat \
    report.json \
    --format markdown > report.md
```

Options:

- `--format`, `-f`: Output format (markdown, summary) (default: markdown)

## 📄 Label Specification Format

The foundation of the tool’s functionality is a label specification file.
This is a JSON file that defines which labels should exist in a repository,
and what their properties should be.

A label definition includes:

- name (required): The label's name
- description (optional): A description of the label
- color (optional): The label's color (hex format without #)

### Basic Example

```json
{
  "labels": [
    {
      "name": "bug",
      "description": "Something isn't working",
      "color": "d73a4a"
    }
  ]
}
```

If description or color are omitted, they are not enforced.
However, name is always required, and the label must exist
(or it will be created if missing).

```json
{
  "labels": [
    {
      "name": "low priority"
    }
  ]
}
```

### Optional Labels

If a label should be treated as optional - meaning it is not required to
exist - you can set the optional flag to true.

If the optional label exists, its defined properties (description, color, etc.)
must still match the specification.

```json
{
  "labels": [
    {
      "name": "put on hold",
      "description": "Don't merge until the linked milestone is actively worked on",
      "color": "ffffff",
      "optional": true
    }
  ]
}
```

### Aliases

To support label renaming or mapping different label names to a standard one,
you can define an alias list.

When using the --alias flag during reporting or syncing, labels with alias
names will be recognized and treated as the canonical name, enabling seamless
migrations without losing issue associations.

```json
{
  "labels": [
    {
      "name": "needs confirmation",
      "description": "Report waiting on confirmation of reproducibility",
      "color": "ff9225",
      "alias": [
        "unconfirmed",
        "status: unconfirmed"
      ]
    }
  ]
}
```

## 🧪 Testing with Dry Runs

Run report without applying changes for safe previews.
Use `--format` summary or markdown to inspect the results.
