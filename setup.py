"""Setup configuration for crowd-anki-diff-rendering."""

from setuptools import find_packages, setup
from pathlib import Path

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = requirements_file.read_text(encoding="utf-8").strip().split("\n")

setup(
    name="crowd-anki-diff-rendering",
    version="0.1.0",
    description="Automatically render crowd-anki deck changes for easy diff viewing",
    include_package_data=True,
    packages=find_packages(),
    package_data={
        "src": ["templates/*.html", "templates/*.jinja2", "templates/*.css"],
    },
    install_requires=requirements,
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "crowd-anki-diff=src.cli:main",
        ],
    },
    keywords="anki crowd-anki diff git visualization",
)
