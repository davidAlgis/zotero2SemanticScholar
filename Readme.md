# Zotero to semantic scholar

Zotero and SemanticScholar are very powerful. I personally use the first to manage my bibliography and generate bibtex for my own notes and the second as an alternative to googleScholar to alert me on the latest papers. 
However, it can be boring to enter his bibliography in each site, even more when it's composed of hundred of different papers ! Therefore, I made this project __to send the bibliography from Zotero to SemanticScholar__.

## How to send data to SemanticScholar

In Zotero export the library in __format CSV__ (File/Export Library), then launch the gui. Filled the login and password input select the csv file you export just before. Finally click on _Send data to SemanticScholar.com..._, wait for a minute... that's it ! :-) 

## Building

- You need to have [python 3](https://www.python.org/downloads/) installed.
- You need the following package : `pandas, csv, tkinter, distance, and selenium`
To install them use this command :
```
pip install pandas, csv, tkinter, distance, selenium
```
- You need the driver firefox for selenium that are available [here](https://github.com/mozilla/geckodriver/releases). Moreover, the folder downloaded here need to be in path. (see https://stackoverflow.com/questions/44272416/how-to-add-a-folder-to-path-environment-variable-in-windows-10-with-screensho) 
- Finally build `main.py` file

I didn't try the project elsewhere than on windows, but I think it could works on linux or macOS, it may require additional installations.

## Issue 

If you have some issue, do not hesitate to put them in [github issue](https://github.com/davidAlgis/zotero2SemanticScholar/issues).

