# Zotero to Semantic Scholar

Zotero and Semantic Scholar are very powerful. I personally use the first one to manage my bibliography and generate bibtex for my own notes and the second one as an alternative to Google Scholar to alert me on the papers published. 
However, it can be boring to enter your bibliography in each site, even more when it's composed of hundred of different papers ! Therefore, I made this project __to send the bibliography from Zotero to Semantic Scholar and to add alert on articles__.

## How to send data to Semantic Scholar

In Zotero, export the library in __format CSV__ (File/Export Library), then launch the gui. Complete the login and password fields with your semanticscholar account informations. Select the csv file you exported just before. Finally, click on _Send data to SemanticScholar.com..._, wait a minute... that's it ! 🙂 

There is a save system, to know which papers has been sent to Semantic Scholar. Therefore, if you need to send a new part of your library to Semantic Scholar it will only send the new articles. Likewise, if the application crash, your progression will be saved.

## Building

1. You need to have [python 3](https://www.python.org/downloads/) installed.
2. You need the following package : `pandas, csv, tkinter, distance, and selenium`
To install them use this command in the project folder :
```
pip install -r requirements_dev.txt
```
For windows os skip to step 4. 
3. You need the driver firefox for selenium that are available [here](https://github.com/mozilla/geckodriver/releases). Moreover, the folder downloaded here need to be in path.
4. Finally build `main.py` file.

I didn't try the project elsewhere than on windows, but I think it could works on linux or macOS, it may requires additional installations.

## Potential improvements

- Test it on other OS than Windows.
- Make a script to automatize the installation.
- Package the script in an executable.
- Switching from an external gui to a zotero add-on integrated directly in zotero.

## Issues

If you have some issue with the application, do not hesitate to put them in [github issue](https://github.com/davidAlgis/zotero2SemanticScholar/issues).

