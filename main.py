# main.py

import pandas as pd
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter import messagebox
from SemanticScholarScrapper import SemanticScholarScrapper
import os
import threading
import argparse
import time


class MainGUI(object):

    def __init__(self, wait_time=37):

        self.path, filename = os.path.split(os.path.realpath(__file__))
        self.root = tk.Tk()
        self.root.title('Zotero2SemanticScholar')
        self.root.geometry('350x300')
        self.root.protocol("WM_DELETE_WINDOW", self.onClosing)
        # Email entry:
        self.wait_time = wait_time
        self.lblInfo = ttk.Label(self.root,
                                 text='Sign in to Semantic Scholar:')
        self.lblEmail = ttk.Label(self.root, text='Email:')
        self.entryEmail = ttk.Entry(self.root)

        # Password entry:
        self.lblPasswd = ttk.Label(self.root, text='Password:')
        self.entryPasswd = ttk.Entry(self.root, show='*')

        self.buttonSelectFiles = ttk.Button(
            self.root,
            text='Select a CSV file exported by Zotero...',
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
        self.saveFileName = os.path.join(self.path, "saveDataSC.csv")
        self.saveFile = None
        self.logFileName = os.path.join(self.path, "log.txt")
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
                "Found bibliography.csv. It will be used by default if no other file is selected."
            )
            self.fileName = "bibliography.csv"
            self._csvToDataFrame()

    def _initSaveData(self):
        if not os.path.exists(self.saveFileName):
            with open(self.saveFileName,
                      "a",
                      encoding="utf-8",
                      errors='ignore') as f:
                f.write("\"Key\",\"Title\"\n")
            self.saveFileDataFrame = pd.read_csv(self.saveFileName)
        else:
            self.saveFileDataFrame = pd.read_csv(self.saveFileName)

        # Open in append mode
        self.saveFile = open(self.saveFileName,
                             "a",
                             encoding="utf-8",
                             errors='ignore')

    def onClosing(self):
        # if messagebox.askokcancel("Quit", "Do you want to quit?"):
        self.root.destroy()
        if self.saveFile:
            self.saveFile.close()
        if self.logFile:
            self.logFile.close()

    def _pack(self):
        self.lblInfo.pack(anchor='nw', pady=(10, 0))
        self.lblEmail.pack(padx=10, pady=(10, 0))
        self.entryEmail.pack(padx=10, pady=(0, 10))
        self.lblPasswd.pack(padx=10, pady=(0, 0))
        self.entryPasswd.pack(padx=10, pady=(0, 10))
        self.separator.pack(fill='x', pady=10)
        self.buttonSelectFiles.pack(expand=True, fill='both', padx=10, pady=10)
        self.separator.pack(fill='x')
        self.buttonSendData.pack(expand=True, fill='both', padx=10, pady=10)
        self.lblLoading.pack(expand=True, fill='both', padx=10, pady=10)

    def _selectFiles(self):
        filetypes = (('CSV files', '*.csv'), ('All files', '*.*'))

        self.fileName = fd.askopenfilename(title='Open a file',
                                           initialdir=os.path.expanduser("~"),
                                           filetypes=filetypes)
        if self.fileName:
            self._csvToDataFrame()

    def _csvToDataFrame(self):
        self.lblLoading.config(text="Reading library...")
        try:
            self.data = pd.read_csv(self.fileName)
        except Exception as e:
            messagebox.showerror('Error', f'Failed to read CSV file: {e}')
            self.writeInLog(f"Error reading CSV file: {e}\n")
            return

        # Initialize columns for alerts and library additions
        self.data.insert(0, 'Add Alert', True)
        self.data.insert(0, 'Add to Library', True)

        # Filter relevant item types
        relevant_types = [
            'journalArticle', 'conferencePaper', 'bookSection', 'preprint',
            'thesis', 'book'
        ]
        self.data = self.data[self.data['Item Type'].isin(relevant_types)]
        self.hasFile = True
        self.lblLoading.config(text="Library loaded successfully.")
        self.writeInLog("Library loaded successfully.\n")

    def _sendDataToSemanticscholar(self):
        self.lblLoading.config(text="Connecting to SemanticScholar.com...")
        self.writeInLog("Connecting to SemanticScholar.com...")

        self.email = self.entryEmail.get().strip()
        self.passwd = self.entryPasswd.get().strip()
        if not self.email or not self.passwd:
            self.lblLoading.config(text="Please sign in above")
            messagebox.showerror('Error',
                                 'Please fill in the login fields above.')
            self.writeInLog("Error - Login fields are empty.\n")
            return

        if not self.hasFile:
            messagebox.showerror(
                'Error',
                'Please select a CSV file containing your Zotero libraries.')
            self.writeInLog("Error - No CSV file selected.\n")
            return

        messagebox.showinfo(
            'Info',
            'The application may not respond during scraping.\nGo make yourself a coffee; it may take a few minutes.'
        )
        self.writeInLog(
            "Info - Scraping started. The application may not respond during this process.\n"
        )

        # Start scraping in a separate thread
        scrapping_thread = threading.Thread(target=self._scrap_data)
        scrapping_thread.daemon = True  # Allows thread to exit when main program exits
        scrapping_thread.start()

    def _scrap_data(self):
        """
        Perform the scraping logic in a separate thread.
        """
        try:
            scrapper = SemanticScholarScrapper(self.logFile, self.path)
            self.lblLoading.config(text="Logging in...")
            self.writeInLog("Logging in...\n")
            is_connected = scrapper.connect_to_account(self.email, self.passwd)

            if is_connected:
                self.writeInLog("Connected to SemanticScholar.\n")
                self.lblLoading.config(
                    text="Sending data to SemanticScholar...")
            else:
                self.lblLoading.config(
                    text="Unable to connect to SemanticScholar!")
                messagebox.showerror(
                    'Error',
                    'Unable to connect to SemanticScholar!\nPlease check your login information or connection and try again.'
                )
                self.writeInLog(
                    "Error - Unable to connect to SemanticScholar.\n")
                return

            Alert = ""
            self.data.reset_index(drop=True, inplace=True)
            total_items = len(self.data)

            for index, row in self.data.iterrows():
                current_item = index + 1
                title = row['Title']

                if (self.saveFileDataFrame['Key'] == row['Key']).any():
                    self.writeInLog(
                        f"Skip: {title} (Item {current_item}/{total_items})\n")
                    continue

                self.writeInLog(
                    f"Searching: {title} (Item {current_item}/{total_items})\n"
                )
                has_add_paper = scrapper.scrap_paper_by_title(title, False)
                if not has_add_paper:
                    msg = f"Could not add '{title}'. There was an error searching on Semantic Scholar.\n"
                    self.writeInLog(msg)
                    Alert += msg
                    continue
                scrapper.cancel_create_paper_alert()
                add_alert = scrapper.alert()
                save_to_library = scrapper.save_to_library()

                if not add_alert and not save_to_library:
                    msg = f"Could not add alert for '{title}'.\n"
                    self.writeInLog(msg)
                    Alert += msg
                    continue

                if not add_alert:
                    self.writeInLog(
                        f"Could not add alert for '{title}', but added it to library.\n"
                    )
                if not save_to_library:
                    self.writeInLog(
                        f"Could not save '{title}' to library, but added it to alert.\n"
                    )

                # Save to saveDataSC.csv
                sanitized_title = title.replace('"', '""')  # Escape quotes
                self.saveFile.write(
                    f"\"{row['Key']}\", \"{sanitized_title}\"\n")
                self.saveFile.flush()  # Ensure data is written immediately
                self.writeInLog(
                    f"Added '{title}' to save file: {self.saveFileName}\n")

                # Respect time between API calls
                time.sleep(self.wait_time)

            self.lblLoading.config(text="Finished sending data.")
            self.writeInLog("Finished sending data.\n")
            if Alert:
                messagebox.showerror('Scraping Complete', Alert)
        except Exception as e:
            self.writeInLog(f"Unexpected error during scraping: {e}\n")
            messagebox.showerror('Error', f"An unexpected error occurred: {e}")

    def writeInLog(self, msg):
        """
        Write messages to the log file and print them.

        :param msg: Message to log.
        """
        if os.stat(self.logFileName).st_size == 0 and not self.hasWriteIdInLog:
            self.logFile.write(f"id: {self.email}\n")
            self.hasWriteIdInLog = True
        self.logFile.write(msg)
        print(msg)

    def _autoFillID(self):
        """
        Autofill the email field from the log file if available.
        """
        if not os.path.isfile(self.logFileName):
            return

        try:
            with open(self.logFileName, 'r', encoding="utf-8",
                      errors='ignore') as logFile:
                first_line = logFile.readline().strip()
                if first_line.startswith("id: "):
                    id_part = first_line[4:]
                    if id_part:
                        self.entryEmail.insert(0, id_part)
        except Exception as e:
            print(f"Error reading log file for autofill: {e}")

    def MainLoop(self):
        self.root.mainloop()

    def _scrap_directly(self, email, password, input_bibliography):
        """
        Run the scrapping process directly using provided arguments.
        """
        self.logFile = open(self.logFileName,
                            "a",
                            encoding="utf-8",
                            errors='ignore')
        scrapper = SemanticScholarScrapper(self.logFile, self.path)

        try:
            self.logFile.write("Logging in...\n")
            is_connected = scrapper.connect_to_account(email, password)

            if not is_connected:
                print(
                    "Error: Unable to connect to Semantic Scholar. Please check your login information."
                )
                return

            print("Connected to Semantic Scholar.")
            self.logFile.write("Connected to Semantic Scholar.\n")

            if not os.path.isfile(input_bibliography):
                print(
                    f"Error: The file '{input_bibliography}' does not exist.")
                return

            data = pd.read_csv(input_bibliography)
            if data.empty:
                print(f"Error: The file '{input_bibliography}' is empty.")
                return

            # Add default columns if they do not exist
            if 'Title' not in data.columns:
                print("Error: The input file must contain a 'Title' column.")
                return

            total_items = len(data)
            for index, row in data.iterrows():
                title = row['Title']
                print(f"Processing {index + 1}/{total_items}: {title}")
                self.logFile.write(f"Searching {title}...\n")

                # Scrape the paper
                has_add_paper = scrapper.scrap_paper_by_title(
                    title, call_browser=False)
                if not has_add_paper:
                    print(f"Warning: Could not add '{title}'.")
                    continue

                # Add alerts and save to library
                scrapper.alert()
                scrapper.save_to_library()

                print(f"Added '{title}' successfully.")
                self.logFile.write(f"Added {title} successfully.\n")
                time.sleep(self.wait_time)

            print("Scraping completed.")
            self.logFile.write("Scraping completed.\n")

        except Exception as e:
            self.logFile.write(f"Unexpected error during scraping: {e}\n")
            print(f"Error: {e}")

        finally:
            scrapper._close_browser()
            self.logFile.close()


if __name__ == "__main__":
    # Initialize argument parser
    parser = argparse.ArgumentParser(description="Semantic Scholar Scraper")
    parser.add_argument("-l",
                        "--login",
                        type=str,
                        help="Your Semantic Scholar login (email).")
    parser.add_argument("-p",
                        "--password",
                        type=str,
                        help="Your Semantic Scholar password.")
    parser.add_argument("-i",
                        "--input_bibliography",
                        type=str,
                        help="Path to the input bibliography CSV file.")
    parser.add_argument(
        "-w",
        "--wait_time",
        type=int,
        default=37,
        help="Time to wait between API calls (default: 37 seconds).")
    args = parser.parse_args()

    if args.login and args.password and args.input_bibliography:
        # Run in non-GUI mode
        path, _ = os.path.split(os.path.realpath(__file__))
        log_file_name = os.path.join(path, "log.txt")
        save_file_name = os.path.join(path, "saveDataSC.csv")

        main = MainGUI(wait_time=args.wait_time)
        main.path = path
        main.logFileName = log_file_name
        main.saveFileName = save_file_name
        main._scrap_directly(args.login, args.password,
                             args.input_bibliography)
    else:
        # Run GUI mode
        gui = MainGUI()
        gui.MainLoop()
