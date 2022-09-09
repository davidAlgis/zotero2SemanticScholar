from setuptools import setup, find_packages

with open("README.md", "r") as readme_file:
    readme = readme_file.read()

requirements = ["pandas>=1.3", "selenium>=4", "Distance>=0.1"]

setup(
    name="Zotero2SemanticScholar",
    version="0.1",
    author="David Algis",
    author_email="david.algis@tutamail.com",
    description="A package to send zotero libraby to semantic scholar and add alert on them",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/davidAlgis/zotero2SemanticScholar",
    packages=find_packages(),
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
)