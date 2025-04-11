# Zotero to Semantic Scholar

Zotero and Semantic Scholar are very powerful tools. I personally use the first one to manage my bibliography and generate BibTeX for my own notes, and the second one as an alternative to Google Scholar to alert me about newly published papers.  
However, it can be tedious to manually enter your bibliography into each site, especially when it consists of hundreds of different papers! Therefore, I created this project __to send the bibliography from Zotero to Semantic Scholar and to add alerts on articles__.

## How to Send Data to Semantic Scholar

In Zotero, export your library in __CSV format__ (File > Export Library).

Download and extract the [`ZoteroToSemanticScholar.zip`](https://github.com/davidAlgis/zotero2SemanticScholar/releases/tag/v0.2) file, then open the executable `ZoteroToSemanticScholar.exe`. Some antivirus software may quarantine the executable for unknown reasons, but as the open-source code in this repository shows, this software contains nothing malicious.

In the interface, complete the login and password fields with your Semantic Scholar account information. Select the CSV file you exported earlier. If you don't select a CSV file, it will look by default for a `bibliography.csv` file in the current folder. Finally, click on _Send data to SemanticScholar.com..._, wait a few minutes... and that's it! 🙂 

Since Semantic Scholar appears to have added bot detection systems, I had to implement methods to remain undetected, which unfortunately slows down the software significantly.

The software includes a save system to keep track of which papers have been sent to Semantic Scholar. Therefore, if you need to send a new portion of your library to Semantic Scholar, it will only send the new articles. Likewise, if the application crashes, your progress will be saved.

## Console Mode

Users who prefer to use the terminal rather than the graphical interface can use the following commands:

- **`-l, --login`**: Your Semantic Scholar login email.
- **`-i, --input_bibliography`**: Path to the input bibliography CSV file exported from Zotero.

For example:
```bash
python main.py -l user@example.com -i bibliography.csv
```

You will be asked for your password afterward.

## Manual Execution (Advanced Users)

If you don't want to use the executable or want to generate it yourself:

1. Ensure you have [Python 3](https://www.python.org/downloads/) installed.
2. Install the packages listed in `requirements.txt` using this command:
```bash
pip install -r requirements.txt
```
3. You might need to download Google Chrome to enable scraping.

4. Finally, execute the `main.py` file:
```bash
python .\main.py
```

### Build Executable

If you want to build the executable manually, follow these steps:
1. Create a dedicated environment to avoid including unnecessary dependencies:
```bash
python -m venv env
env\Scripts\activate
```

2. Install the dependencies:
```bash
pip install -r requirements.txt
```

3. Finally call the build process with:
```bash
python setup.py build
```

## Notes

- I haven't tested the project on platforms other than Windows, but it should work on Linux or macOS with possible additional installations.
- Currently, the application only processes Zotero items of these types: `journalArticle`, `conferencePaper`, `bookSection`, `preprint`, `thesis`, or `book`. If you want to include other types, modify the method `_csvToDataList` of `main.py`.

If you encounter any issues with the application, feel free to report them on [GitHub Issues](https://github.com/davidAlgis/zotero2SemanticScholar/issues).
