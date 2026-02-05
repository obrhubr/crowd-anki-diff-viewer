"""Command-line interface for crowd-anki diff rendering."""

import click
import sys
from pathlib import Path

from .git_diff import detect_note_changes, get_commit_info
from .html_generator import generate_diff_html
from .media_handler import copy_media_files


@click.command()
@click.option(
    '--repo-path',
    default='.',
    help='Path to crowd-anki repository',
    type=click.Path(exists=True)
)
@click.option(
    '--output',
    default='diff.html',
    help='Output HTML file path',
    type=click.Path()
)
@click.option(
    '--commit',
    default='HEAD',
    help='Commit to diff against (default: HEAD)'
)
@click.option(
    '--deck-path',
    default=None,
    help='Path to specific deck.json file (optional)',
    type=click.Path(exists=True)
)
@click.option(
    '--no-media',
    is_flag=True,
    help='Skip copying media files'
)
@click.option(
    '--verbose',
    '-v',
    is_flag=True,
    help='Verbose output'
)
def main(repo_path, output, commit, deck_path, no_media, verbose):
    """
    Generate HTML diff for crowd-anki deck changes.

    This tool analyzes git commits to detect changes to Anki notes and generates
    a side-by-side HTML comparison showing what changed.

    Examples:

    \b
        # Generate diff for latest commit
        python -m src.cli

    \b
        # Generate diff with custom output path
        python -m src.cli --output my_diff.html

    \b
        # Generate diff for specific commit
        python -m src.cli --commit HEAD~1
    """
    try:
        # Print header
        click.echo(click.style("Crowd-Anki Diff Renderer", fg='blue', bold=True))
        click.echo(click.style("=" * 50, fg='blue'))
        click.echo()

        # Get commit information
        if verbose:
            click.echo(f"Repository: {repo_path}")
            click.echo(f"Commit: {commit}")

        commit_info = get_commit_info(repo_path, commit)

        if verbose:
            click.echo(f"Commit hash: {commit_info['hash']}")
            click.echo(f"Message: {commit_info['message']}")
            click.echo()

        # Detect changes
        click.echo("Detecting note changes...")
        changes = detect_note_changes(repo_path, commit)

        if not changes:
            click.echo(click.style("No note changes detected.", fg='yellow'))
            click.echo()
            click.echo("This could mean:")
            click.echo("  - No deck.json files were modified in this commit")
            click.echo("  - The repository is not a git repository")
            click.echo("  - The commit has no parent to compare against")
            sys.exit(0)

        # Print summary
        change_types = {}
        for change in changes:
            change_types[change.change_type] = change_types.get(change.change_type, 0) + 1

        click.echo(click.style(f"✓ Found {len(changes)} changed note(s)", fg='green'))
        for change_type, count in change_types.items():
            color = {'added': 'green', 'modified': 'yellow', 'deleted': 'red'}.get(change_type, 'white')
            click.echo(f"  - {count} ", nl=False)
            click.echo(click.style(change_type, fg=color))

        # Count cosmetic-only changes
        cosmetic_count = sum(1 for change in changes if change.is_cosmetic_only)
        if cosmetic_count > 0:
            click.echo()
            click.echo(click.style(f"ℹ️  {cosmetic_count} cosmetic-only change(s) will be hidden in the diff", fg='cyan'))

            # Show breakdown
            from .change_classifier import ChangeType
            cosmetic_types = {}
            for change in changes:
                if change.is_cosmetic_only:
                    change_desc = change.content_change_type
                    cosmetic_types[change_desc] = cosmetic_types.get(change_desc, 0) + 1

            for ctype, count in cosmetic_types.items():
                readable_type = ctype.replace('_', ' ').title()
                click.echo(f"  - {count} {readable_type}")

        if verbose:
            click.echo()
            click.echo("Changes by deck:")
            deck_counts = {}
            for change in changes:
                deck_counts[change.deck_path] = deck_counts.get(change.deck_path, 0) + 1
            for deck_path, count in deck_counts.items():
                click.echo(f"  - {deck_path}: {count} note(s)")

        click.echo()

        # Generate HTML
        click.echo("Generating HTML diff...")
        output_path = Path(output)

        generate_diff_html(
            changes=changes,
            output_path=str(output_path),
            commit_info=commit_info
        )

        click.echo(click.style(f"✓ HTML diff generated", fg='green'))

        # Copy media files
        if not no_media:
            click.echo("Copying media files...")

            # Find deck paths
            deck_paths = set()
            for change in changes:
                # Try to find the deck.json file
                # This is a simplified approach - in production might need more logic
                current_path = Path(repo_path)
                for deck_file in current_path.rglob('deck.json'):
                    deck_paths.add(str(deck_file))

            copied_count = 0
            for deck_file_path in deck_paths:
                try:
                    copied = copy_media_files(
                        deck_file_path,
                        str(output_path.parent),
                        changes
                    )
                    copied_count += len(copied)
                except Exception as e:
                    if verbose:
                        click.echo(f"Warning: Failed to copy media from {deck_file_path}: {e}")

            if copied_count > 0:
                click.echo(click.style(f"✓ Copied {copied_count} media file(s)", fg='green'))
            elif verbose:
                click.echo("No media files to copy")

        click.echo()
        click.echo(click.style("Done!", fg='green', bold=True))
        click.echo(f"Output: {output_path.absolute()}")

        # Print URL if it looks like it will be deployed
        if 'diff.html' in str(output_path):
            click.echo()
            click.echo("To view the diff:")
            click.echo(f"  file://{output_path.absolute()}")

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg='red', bold=True), err=True)
        if verbose:
            import traceback
            click.echo(traceback.format_exc(), err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
