# Crowd-Anki Diff Rendering

Automatically render changes to crowd-anki repositories as beautiful, side-by-side HTML diffs for easy review.

## Features

- 🎴 **Visual Diff**: Side-by-side comparison of card changes (before/after)
- 🔍 **Smart Detection**: Automatically detects changed notes via git diff
- 🎨 **Multiple Note Types**: Supports cloze, basic, image occlusion, and multi-field cards
- 📊 **Field-by-Field Comparison**: Detailed view of what changed in each field
- 🖼️ **Media Support**: Automatically copies and references media files
- 🤖 **GitHub Actions**: Automated workflow for continuous integration
- 📱 **Responsive Design**: Works on desktop and mobile devices
- 🔗 **GitHub Pages**: Automatically deploy diffs to GitHub Pages

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/crowd-anki-diff-rendering.git
cd crowd-anki-diff-rendering

# Install dependencies
pip install -e .
```

### Local Usage

```bash
# Generate diff for latest commit
python -m src.cli

# Generate diff with custom output
python -m src.cli --output my_diff.html

# Generate diff for specific commit
python -m src.cli --commit HEAD~1

# Verbose output
python -m src.cli --verbose
```

### GitHub Actions Setup

1. **Copy the workflow file** to your crowd-anki repository:
   ```bash
   mkdir -p .github/workflows
   cp .github/workflows/render-diff.yml your-deck-repo/.github/workflows/
   ```

2. **Enable GitHub Pages**:
   - Go to your repository Settings → Pages
   - Set source to "gh-pages" branch
   - Save

3. **Commit and push**:
   ```bash
   git add .github/workflows/render-diff.yml
   git commit -m "Add Anki diff rendering workflow"
   git push
   ```

4. **View diffs**:
   - After push: `https://yourusername.github.io/your-repo/diff.html`
   - Pull requests will get automatic comment with diff link

## Supported Note Types

### ✅ Cloze Deletion Cards
Renders `{{c1::text}}` syntax with proper highlighting.

### ✅ Basic Front/Back Cards
Standard two-sided flashcards.

### ✅ Image Occlusion Cards
Interactive cards with canvas-based shape rendering (rectangles, ellipses).

### ✅ Multi-Field Cards
Complex cards with many fields (e.g., algorithm cards with Name, Runtime, Requirements, etc.).

## Architecture

```
src/
├── models.py              # Pydantic data models
├── parser.py              # Crowd-anki JSON parser
├── git_diff.py            # Git diff detection
├── template_engine.py     # Anki template renderer
├── renderers/             # Note type renderers
│   ├── base.py
│   ├── cloze_renderer.py
│   ├── basic_renderer.py
│   ├── image_occlusion_renderer.py
│   └── multi_field_renderer.py
├── html_generator.py      # HTML diff page generation
├── media_handler.py       # Media file management
└── cli.py                 # Command-line interface
```

## How It Works

1. **Git Diff Detection**: Compares `HEAD` with parent commit to find modified `deck.json` files
2. **Note Parsing**: Parses crowd-anki JSON structure including note models and hierarchy
3. **Change Analysis**: Identifies added, modified, and deleted notes by GUID
4. **Card Rendering**: Renders each card using Anki's template syntax
5. **HTML Generation**: Creates side-by-side comparison with embedded CSS
6. **Media Handling**: Copies referenced images and media files

## Development

### Setup Development Environment

```bash
# Install dev dependencies
pip install -e .[dev]

# Or use requirements-dev.txt
pip install -r requirements-dev.txt
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_parser.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Type checking
mypy src/

# Linting
ruff check src/ tests/
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

### GitHub Actions Workflow

The workflow triggers on:
- Push to `main`/`master` with `deck.json` changes
- Pull requests with `deck.json` changes

Configure by editing `.github/workflows/render-diff.yml`:

```yaml
on:
  push:
    branches: [main, master]
    paths:
      - '**/deck.json'
  pull_request:
    paths:
      - '**/deck.json'
```

## Examples

### Example Output

The generated HTML diff includes:

- **Header**: Commit information, author, date, change summary
- **Table of Contents**: Quick navigation to each changed note
- **Side-by-Side Cards**: Visual comparison of before/after states
- **Field Diffs**: Detailed field-by-field changes
- **Tags**: Note tags for organization

### Example Use Cases

1. **Review Changes**: Before merging, review what changed in your deck
2. **Collaboration**: Team members can see exactly what notes were modified
3. **History**: Track evolution of your deck over time
4. **Documentation**: Generate visual changelog for deck updates

## Troubleshooting

### No changes detected

**Problem**: "No note changes detected" message

**Solutions**:
- Ensure you're in a git repository: `git status`
- Check if `deck.json` was modified: `git diff HEAD~1 HEAD`
- Verify the commit has a parent: `git log --oneline`

### Media files not showing

**Problem**: Images don't appear in diff

**Solutions**:
- Check media files exist in `media/` directory
- Verify paths in note fields: `<img src="filename.jpg">`
- Use `--verbose` flag to see media copy errors
- Ensure media directory is copied alongside HTML

### Import errors

**Problem**: Module import errors when running

**Solutions**:
```bash
# Reinstall in development mode
pip install -e .

# Check installation
python -c "import src; print(src.__version__)"

# Verify dependencies
pip list | grep -E "pydantic|gitpython|jinja2"
```

### GitHub Pages not updating

**Problem**: Diff doesn't appear on GitHub Pages

**Solutions**:
- Check Actions tab for workflow errors
- Verify gh-pages branch exists
- Confirm Pages settings point to gh-pages branch
- Wait a few minutes for deployment to complete

## Contributing

Contributions welcome! Areas for improvement:

- [ ] Additional note type renderers
- [ ] Better LaTeX rendering
- [ ] Sound file support
- [ ] PDF export option
- [ ] Incremental diff (multiple commits)
- [ ] Configuration file support

## License

MIT License - see LICENSE file for details

## Credits

Built with:
- [Pydantic](https://pydantic.dev/) - Data validation
- [GitPython](https://gitpython.readthedocs.io/) - Git operations
- [Jinja2](https://jinja.palletsprojects.com/) - HTML templating
- [Click](https://click.palletsprojects.com/) - CLI framework

Inspired by [CrowdAnki](https://github.com/Stvad/CrowdAnki) for collaborative Anki deck management.

## Support

- 📖 Documentation: [GitHub Wiki](https://github.com/yourusername/crowd-anki-diff-rendering/wiki)
- 🐛 Bug Reports: [GitHub Issues](https://github.com/yourusername/crowd-anki-diff-rendering/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/crowd-anki-diff-rendering/discussions)

---

Made with ❤️ for the Anki community
