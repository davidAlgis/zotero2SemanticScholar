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
            command=self._selectFiles
        )

        self.separator = ttk.Separator(self.root, orient='horizontal')

        self.buttonSendData = ttk.Button(
            self.root,
            text='Send data to SemanticScholar.com...',
            command=self._sendDataToSemanticscholar
        )

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
        self.logFile = open(self.logFileName, "a", encoding="utf-8")
        self.hasAlreadySaveFile = False

        if os.path.isfile("bibliography.csv"):
            print(
                "Has found bibliography.csv, it will be used by default, if no other file will be send")
            self.fileName = "bibliography.csv"
            self._csvToDataFrame()

    def _initSaveData(self):
        if (os.path.exists(self.saveFileName) == False):
            self.saveFile = open(self.saveFileName, "a", encoding="utf-8")
            self.saveFile.write("\"Key\",\"Title\"\n")
        else:
            self.saveFile = open(self.saveFileName, "a", encoding="utf-8")
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
        self.buttonSelectFiles.pack(expand=True,
                                    fill='both', padx=10, pady=10)
        self.separator.pack(fill='x')
        self.buttonSendData.pack(expand=True,
                                 fill='both', padx=10, pady=10)
        self.lblLoading.pack(expand=True,
                             fill='both')

    def _selectFiles(self):
        filetypes = (
            ('csv files', '*.csv'),
            ('All files', '*.*')
        )

        self.fileName = fd.askopenfilename(
            title='Open a file',
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

        self.data = self.data[['Ajouter une alarme', 'Ajouter dans la librairie',
                               'Key', 'Title', 'Author', 'Item Type', 'Publication Year']]
        self.data = self.data.loc[self.data['Item Type'].isin([
            'journalArticle', 'conferencePaper', 'bookSection', 'preprint', 'thesis'])]
        self.hasFile = True
        # for index, row in self.saveFileDataFrame.iterrows():
        #     if((self.data['Key'] == row['Key']).any()):
        #         self.data = self.data.drop(self.data.loc(self.data['Key'] == row['Key']))
        # print(data)

    def _sendDataToSemanticscholar(self):
        self.lblLoading.config(text="Connection to semanticScholar.com...")

        self.email = self.entryEmail.get()
        self.passwd = self.entryPasswd.get()
        if(self.email == '' or self.passwd == ''):
            self.lblLoading.config(text="Please sign-in above")
            messagebox.showerror('Error', 'Please fill the login field above')
            return
        if(self.hasFile == False):
            messagebox.showerror(
                'Error', 'Please select a csv file containing your zotero librairies')
            return
        messagebox.showinfo(
            'Info', 'The application may not responding during scrapping.\n Go make yourself a coffee, it may take a few minutes.')
        scrapper = SemanticScholarScrapper(self.logFile, self.path)
        self.lblLoading.config(text="Login in progress...")
        isConnected = scrapper.connect_to_account(self.email, self.passwd)
        if(scrapper.is_connected == True):
            self.lblLoading.config(text="Sending data to semanticScholar...")
        else:
            self.lblLoading.config(
                text="Unable to connect to SemanticScholar !")
            messagebox.showerror(
                'Error', 'Unable to connect to SemanticScholar !\nPlease check you login information or you connection and try again.')
            return
        Alert = ""
        for index, row in self.data.iterrows():
            if((self.saveFileDataFrame['Key'] == row['Key']).any()):
                print("skip : " + row['Title'])
                continue
            print("searching " + row['Title'])
            hasAddPaper = scrapper.scrap_paper_by_title(
                row['Title'], False)
            if(hasAddPaper == False):
                msg = "Could not add " + row['Title']+"\n"
                self.writeInLog(msg)
                Alert += msg
                continue
            addAlert = scrapper.alert()
            saveToLibrary = scrapper.save_to_library()
            if(addAlert == False and saveToLibrary == False):
                msg = "Could not add alert on " + row['Title']+"\n"
                self.writeInLog(
                    msg)
                Alert += msg
                continue
            if(addAlert == False):
                self.writeInLog(
                    "Could not add alert on " + row['Title'] + ", but add it to library.\n")
            if(saveToLibrary == False):
                self.writeInLog(
                    "Could not save " + row['Title'] + "in library, but add it to alert.\n")
            title = row['Title'].replace(',', '')
            self.saveFile.write("\""+row['Key']+"\", \""+title+"\"\n")
            self.writeInLog("add " + row['Title'] + " to save file.\n")
            print(self.saveFileName)

        self.lblLoading.config(text="Finish sending data.")

        if(Alert != ''):
            messagebox.showerror('Scrapping is over', Alert)

    def writeInLog(self, msg):
        print(msg)
        self.logFile.write(msg)

    def MainLoop(self):
        self.root.mainloop()


if __name__ == "__main__":
    gui = MainGUI()
    gui.MainLoop()
