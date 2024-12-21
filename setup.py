import sys
from cx_Freeze import setup, Executable
from setuptools import find_packages

# Load README and requirements
with open("README.md", "r", encoding="utf-8") as fh:
    readme = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

# Dependencies to be included
build_exe_options = {
    "packages": [
        "os", "seleniumbase", "undetected_chromedriver", "distance",
        "Levenshtein"
    ],
    "include_files": ["SemanticScholarScrapper.py", "requirements.txt"],
    "excludes": ["tkinter.test"],
}

# Main setup configuration
setup(
    name="Zotero2SemanticScholar",
    version="0.1",
    author="David Algis",
    author_email="david.algis@tutamail.com",
    description=
    "A package to send Zotero library entries to Semantic Scholar and add alerts for them.",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/davidAlgis/zotero2SemanticScholar",
    packages=find_packages(),
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            script="main.py",  # Your main Python file
            base=None,
            target_name="Zotero2SemanticScholar.exe",  # Name of the executable
            icon=None,  # Add an icon path here if you have one
        )
    ],
)
