import pandas as pd
import csv
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter import messagebox
from SemanticScholarScrapper import *
import os


class MainGUI(object):

    def __init__(self):

        self.path, filename = os.path.split(os.path.realpath(__file__))
        self.root = tk.Tk()
        self.root.title('Zotero2SemanticScholar')
        self.root.geometry('350x250')
        self.root.protocol("WM_DELETE_WINDOW", self.onClosing)
        # Email entry:
        self.lblInfo = ttk.Label(self.root, text='Sign in SemanticScholar:')
        self.lblEmail = ttk.Label(self.root, text='Email:')
        self.entryEmail = ttk.Entry(self.root)

        # Password entry:
        self.lblPasswd = ttk.Label(self.root, text='Password:')
        self.entryPasswd = ttk.Entry(self.root, show='*')

        self.buttonSelectFiles = ttk.Button(
            self.root,
            text='Select a csv file exported by zotero...',
            command=self._selectFiles)

        self.separator = ttk.Separator(self.root, orient='horizontal')

        self.buttonSendData = ttk.Button(
            self.root,
            text='Send data to SemanticScholar.com...',
            command=self._sendDataToSemanticscholar)

        self.lblLoading = ttk.Label(
            self.root, text='Waiting for a file to be selected...')

        self.fileName = ""
        self.data = pd.DataFrame()
        self.email = ""
        self.passwd = ""
        self.hasFile = False
        self._pack()
        self.saveFileName = self.path + "//saveDataSC.csv"
        self.saveFile = None
        self.logFileName = self.path + "//log.txt"
        self.saveFileDataFrame = pd.DataFrame()
        self._initSaveData()
        self.logFile = open(self.logFileName,
                            "a",
                            encoding="utf-8",
                            errors='ignore')
        self.hasAlreadySaveFile = False
        self._autoFillID()
        self.hasWriteIdInLog = False

        if os.path.isfile("bibliography.csv"):
            print(
                "Has found bibliography.csv, it will be used by default, if no other file will be send"
            )
            self.fileName = "bibliography.csv"
            self._csvToDataFrame()

    def _initSaveData(self):
        if (os.path.exists(self.saveFileName) == False):
            self.saveFile = open(self.saveFileName,
                                 "a",
                                 encoding="utf-8",
                                 errors='ignore')
            self.saveFile.write("\"Key\",\"Title\"\n")
            self.saveFile.close()
            self.saveFileDataFrame = pd.read_csv(self.saveFileName)
            self.saveFile = open(self.saveFileName,
                                 "a",
                                 encoding="utf-8",
                                 errors='ignore')

        else:
            self.saveFile = open(self.saveFileName,
                                 "a",
                                 encoding="utf-8",
                                 errors='ignore')
            self.hasAlreadySaveFile = True
            self.saveFileDataFrame = pd.read_csv(self.saveFileName)

    def onClosing(self):
        # if messagebox.askokcancel("Quit", "Do you want to quit?"):
        self.root.destroy()
        self.saveFile.close()
        self.logFile.close()

    def _pack(self):
        self.lblInfo.pack(anchor='nw')
        self.lblEmail.pack()
        self.entryEmail.pack()
        self.lblPasswd.pack()
        self.entryPasswd.pack()
        self.separator.pack(fill='x', pady=10)
        self.buttonSelectFiles.pack(expand=True, fill='both', padx=10, pady=10)
        self.separator.pack(fill='x')
        self.buttonSendData.pack(expand=True, fill='both', padx=10, pady=10)
        self.lblLoading.pack(expand=True, fill='both')

    def _selectFiles(self):
        filetypes = (('csv files', '*.csv'), ('All files', '*.*'))

        self.fileName = fd.askopenfilename(title='Open a file',
                                           initialdir='C://Users',
                                           filetypes=filetypes)
        self._csvToDataFrame()

    def _csvToDataFrame(self):
        self.lblLoading.config(text="Reading library...")
        self.data = pd.read_csv(self.fileName)
        val = []
        for i in range(len(self.data.index)):
            val.append(True)

        self.data.insert(0, 'Ajouter une alarme', val)
        self.data.insert(0, 'Ajouter dans la librairie', val)

        self.data = self.data[[
            'Ajouter une alarme', 'Ajouter dans la librairie', 'Key', 'Title',
            'Author', 'Item Type', 'Publication Year'
        ]]
        self.data = self.data.loc[self.data['Item Type'].isin([
            'journalArticle', 'conferencePaper', 'bookSection', 'preprint',
            'thesis', 'book'
        ])]
        self.hasFile = True
        # for index, row in self.saveFileDataFrame.iterrows():

    def _sendDataToSemanticscholar(self):
        self.lblLoading.config(text="Connecting to SemanticScholar.com...")
        self.writeInLog("Connecting to SemanticScholar.com...")

        self.email = self.entryEmail.get()
        self.passwd = self.entryPasswd.get()
        if not self.email or not self.passwd:
            self.lblLoading.config(text="Please sign in above")
            messagebox.showerror('Error', 'Please fill the login field above')
            self.writeInLog("Error - Please fill the login field above")
            return

        if not self.hasFile:
            messagebox.showerror(
                'Error',
                'Please select a csv file containing your Zotero libraries')
            self.writeInLog(
                "Error - Please select a csv file containing your Zotero libraries"
            )
            return

        messagebox.showinfo(
            'Info',
            'The application may not responding during scrapping.\n Go make yourself a coffee, it may take a few minutes.'
        )
        self.writeInLog(
            "The application may not responding during scrapping. Go make yourself a coffee, it may take a few minutes."
        )
        scrapper = SemanticScholarScrapper(self.logFile, self.path)
        self.lblLoading.config(text="Logging in...")
        self.writeInLog("Logging in...")
        isConnected = scrapper.connect_to_account(self.email, self.passwd)

        if scrapper.is_connected:
            self.writeInLog("Connected.")
            self.lblLoading.config(text="Sending data to SemanticScholar...")
        else:
            self.lblLoading.config(
                text="Unable to connect to SemanticScholar!")
            messagebox.showerror(
                'Error',
                'Unable to connect to SemanticScholar!\nPlease check your login information or connection and try again.'
            )
            self.writeInLog(
                "Error - Unable to connect to SemanticScholar!\nPlease check your login information or connection and try again."
            )
            return

        Alert = ""
        self.data.reset_index(drop=True, inplace=True)
        total_items = len(self.data)
        for index, row in self.data.iterrows():
            current_item = index + 1
            if (self.saveFileDataFrame['Key'] == row['Key']).any():
                self.writeInLog(
                    f"Skip: {row['Title']} (Item {current_item}/{total_items})\n"
                )
                continue

            self.writeInLog(
                f"Searching {row['Title']} (Item {current_item}/{total_items})\n"
            )
            hasAddPaper = scrapper.scrap_paper_by_title(row['Title'], False)
            if not hasAddPaper:
                msg = f"Could not add {row['Title']} there was an error when searching on semantic scholar\n"
                self.writeInLog(msg)
                Alert += msg
                continue

            addAlert = scrapper.alert()
            saveToLibrary = scrapper.save_to_library()
            if not addAlert and not saveToLibrary:
                msg = f"Could not add alert for {row['Title']}\n"
                self.writeInLog(msg)
                Alert += msg
                continue

            if not addAlert:
                self.writeInLog(
                    f"Could not add alert for {row['Title']}, but added it to library.\n"
                )
            if not saveToLibrary:
                self.writeInLog(
                    f"Could not save {row['Title']} in library, but added it to alert.\n"
                )

            title = row['Title'].replace(',', '')
            self.saveFile.write(f"\"{row['Key']}\", \"{title}\"\n")
            self.writeInLog(
                f"Added {row['Title']} to save file: {self.saveFileName}\n")

        self.lblLoading.config(text="Finished sending data.")
        self.writeInLog("Finished sending data.")
        if Alert:
            messagebox.showerror('Scraping complete', Alert)

    def writeInLog(self, msg):
        if os.stat(self.logFileName
                   ).st_size == 0 and self.hasWriteIdInLog == False:
            print("write id")
            self.logFile.write("id : " + self.email + "\n")
            self.hasWriteIdInLog = True
        print("\n")
        print(msg)
        self.logFile.write(msg)

    def _autoFillID(self):
        with open(self.logFileName, 'r', encoding="utf-8",
                  errors='ignore') as logFile:
            # Read the first line
            first_line = logFile.readline().strip()
            # Extract the part after "id :"
            if (first_line[0:5] != "id : "):
                return
            else:
                id_part = first_line[5:]
                if (id_part != ''):
                    self.entryEmail.insert(0, id_part)

    def MainLoop(self):
        self.root.mainloop()


if __name__ == "__main__":
    gui = MainGUI()
    gui.MainLoop()
