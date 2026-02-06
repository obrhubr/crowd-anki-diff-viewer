# Crowd-Anki Diff Rendering

Quick vibe-coded diff renderer for [CrowdAnki](https://github.com/Stvad/CrowdAnki) that can be run in Github Actions to make changes more readable.

## Quick Start

### Installation

```bash
pip install -e .
```

### Local Usage

```bash
# Generate diff for latest commit
crowd-anki-diff

# Generate diff with custom output
crowd-anki-diff --output my_diff.html

# Generate diff for specific commit
crowd-anki-diff --commit HEAD~1

# Verbose output
crowd-anki-diff --verbose
```

## Configuration

### CLI Options

```
Options:
  --repo-path PATH   Path to crowd-anki repository (default: .)
  --output PATH      Output HTML file path (default: diff.html)
  --commit TEXT      Commit to diff against (default: HEAD)
  --deck-path PATH   Path to specific deck.json file (optional)
  --no-media         Skip copying media files
  --verbose, -v      Verbose output
  --help             Show this message and exit
```