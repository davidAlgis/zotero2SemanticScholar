# main.py
import os
import threading
import argparse
import csv
import time
import queue
import getpass
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter import messagebox

from SemanticScholarScrapper import SemanticScholarScrapper


def get_base_directory():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        # Running normally as a script
        current_directory = os.path.abspath(os.path.dirname(__file__))
        return os.path.abspath(os.path.join(current_directory, os.pardir))


class MainGUI(object):

    def __init__(self):
        self.path = get_base_directory()
        self.root = tk.Tk()
        self.root.title('Zotero2SemanticScholar')
        self.root.geometry('400x400')  # Increased height for progress bar
        self.root.protocol("WM_DELETE_WINDOW", self.onClosing)

        # Initialize queue for thread-safe communication
        self.queue = queue.Queue()

        # Email entry:
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

        # Progress bar and labels
        self.progress = ttk.Progressbar(self.root,
                                        orient='horizontal',
                                        length=300,
                                        mode='determinate')
        self.lblProgress = ttk.Label(self.root, text='Progress: 0/0')
        self.lblTimeRemaining = ttk.Label(self.root,
                                          text='Estimated time remaining: 0s')

        self.fileName = ""
        # We'll store CSV rows in a list of dictionaries (instead of using pandas)
        self.data = []
        self.email = ""
        self.passwd = ""
        self.hasFile = False
        self._pack()

        # We will store "Key" values that have already been saved in a set
        # to replicate the "has it already been saved?" logic from pandas
        self.saveFileName = os.path.join(self.path, "saveDataSC.csv")
        self.saveFile = None
        self.logFileName = os.path.join(self.path, "log.txt")
        self.savedKeys = set()
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
            self._csvToDataList()

        # Start the queue processing
        self.root.after(100, self._process_queue)

    def _initSaveData(self):
        """
        Initialize the 'saveDataSC.csv' file and read existing saved keys into a set.
        """
        file_exists = os.path.exists(self.saveFileName)

        if not file_exists:
            # Create the file with a header
            with open(self.saveFileName, "w", encoding="utf-8",
                      newline='') as f:
                writer = csv.writer(f, quoting=csv.QUOTE_ALL)
                writer.writerow(["Key", "Title"])
        else:
            # Read existing keys from saveFileName into a set
            with open(self.saveFileName,
                      "r",
                      encoding="utf-8",
                      errors='ignore') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Collect the keys that have already been saved
                    if 'Key' in row and row['Key']:
                        self.savedKeys.add(row['Key'])

        # Open in append mode so we can write new entries later
        self.saveFile = open(self.saveFileName,
                             "a",
                             encoding="utf-8",
                             errors='ignore',
                             newline='')
        self.saveWriter = csv.writer(self.saveFile, quoting=csv.QUOTE_ALL)

    def onClosing(self):
        self.root.destroy()
        if self.saveFile:
            self.saveFile.close()
        if self.logFile:
            self.logFile.close()

    def _pack(self):
        padding_options = {'padx': 10}
        self.lblInfo.pack(anchor='nw', pady=(10, 0), **padding_options)
        self.lblEmail.pack(anchor='nw', **padding_options)
        self.entryEmail.pack(fill='x', padx=10, pady=(0, 10))
        self.lblPasswd.pack(anchor='nw', **padding_options)
        self.entryPasswd.pack(fill='x', padx=10, pady=(0, 10))
        self.separator.pack(fill='x', pady=10, padx=10)
        self.buttonSelectFiles.pack(expand=True, fill='both', padx=10, pady=10)
        self.separator.pack(fill='x', padx=10, pady=(10, 0))
        self.buttonSendData.pack(expand=True, fill='both', padx=10, pady=10)
        self.lblLoading.pack(expand=True, fill='both', padx=10, pady=10)

        # Pack progress bar and labels
        self.progress.pack(pady=(20, 5))
        self.lblProgress.pack()
        self.lblTimeRemaining.pack()

    def _selectFiles(self):
        filetypes = (('CSV files', '*.csv'), ('All files', '*.*'))

        self.fileName = fd.askopenfilename(title='Open a file',
                                           initialdir=os.path.expanduser("~"),
                                           filetypes=filetypes)
        if self.fileName:
            self._csvToDataList()

    def _csvToDataList(self):
        """
        Read the selected CSV into a list of dictionaries, filter relevant types, and set flags.
        """
        self.lblLoading.config(text="Reading library...")
        try:
            with open(self.fileName, 'r', encoding="utf-8",
                      errors='ignore') as f:
                reader = csv.DictReader(f)
                # Convert to a list of dicts
                data_list = list(reader)

        except Exception as e:
            messagebox.showerror('Error', f'Failed to read CSV file: {e}')
            self.writeInLog(f"Error reading CSV file: {e}\n")
            return

        # Add default columns to each row
        for row in data_list:
            row['Add Alert'] = True
            row['Add to Library'] = True

        # Filter relevant item types
        relevant_types = [
            'journalArticle', 'conferencePaper', 'bookSection', 'preprint',
            'thesis', 'book'
        ]
        filtered_data_list = [
            row for row in data_list if row.get('Item Type') in relevant_types
        ]

        self.data = filtered_data_list
        self.hasFile = True
        self.lblLoading.config(text="Library loaded successfully.")
        self.writeInLog("Library loaded successfully.\n")

    def _sendDataToSemanticscholar(self):
        self.lblLoading.config(text="Connecting to SemanticScholar.com...")
        self.writeInLog("Connecting to SemanticScholar.com...\n")

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
            total_items = len(self.data)
            start_time = time.time()
            processed_items = 0
            self._update_progress(processed_items, total_items, start_time)

            scrapper = SemanticScholarScrapper(self.logFile,
                                               self.path,
                                               email=self.email,
                                               password=self.passwd)
            self.queue.put(("status", "Logging in..."))
            self.writeInLog("Logging in...\n")
            start_time = time.time()

            is_connected = scrapper.connect_to_account(self.email, self.passwd)
            if is_connected:
                self.writeInLog("Connected to SemanticScholar.\n")
                self.queue.put(
                    ("status", "Sending data to SemanticScholar..."))
            else:
                self.queue.put((
                    "error",
                    "Unable to connect to SemanticScholar! Please check your login information or connection and try again."
                ))
                self.writeInLog(
                    "Error - Unable to connect to SemanticScholar.\n")
                return

            Alert = ""

            for index, row in enumerate(self.data):
                current_item = index + 1
                title = row.get('Title', '')

                # Skip if the 'Key' is already in the saved set
                row_key = row.get('Key', '')
                if row_key in self.savedKeys:
                    self.writeInLog(
                        f"Skip: {title} (Item {current_item}/{total_items}), because it has already been saved.\n"
                    )
                    processed_items += 1
                    self._update_progress(processed_items, total_items,
                                          start_time)
                    continue

                self.writeInLog(
                    f"Searching: {title} (Item {current_item}/{total_items})\n"
                )
                has_add_paper = scrapper.scrap_paper_by_title(title, False)
                if not has_add_paper:
                    msg = f"Could not add '{title}'. There was an error searching on Semantic Scholar.\n"
                    self.writeInLog(msg)
                    Alert += msg
                    processed_items += 1
                    self._update_progress(processed_items, total_items,
                                          start_time)
                    continue

                # Attempt to add alert and library
                scrapper.cancel_create_paper_alert()
                add_alert = scrapper.alert()
                save_to_library = scrapper.save_to_library()

                if not add_alert and not save_to_library:
                    msg = f"Could not add alert for '{title}'.\n"
                    self.writeInLog(msg)
                    Alert += msg
                    processed_items += 1
                    self._update_progress(processed_items, total_items,
                                          start_time)
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
                # We also keep track of the 'Key' so we won't add it again
                sanitized_key = row_key.replace('"', '""')
                sanitized_title = title.replace('"', '""').replace(',', ' ')
                self.saveFile.write(
                    f"\"{sanitized_key}\", \"{sanitized_title}\"\n")
                self.saveFile.flush()  # Ensure data is written immediately
                self.savedKeys.add(row_key)  # Mark this key as saved

                self.writeInLog(
                    f"Added '{title}' to save file: {self.saveFileName}\n")

                processed_items += 1
                self._update_progress(processed_items, total_items, start_time)

            self.lblLoading.config(text="Finished sending data.")
            self.writeInLog("Finished sending data.\n")

            if Alert:
                self.queue.put(("error", Alert))
            else:
                self.queue.put(
                    ("complete", "Scraping completed successfully."))

        except Exception as e:
            self.writeInLog(f"Unexpected error during scraping: {e}\n")
            self.queue.put(("error", f"An unexpected error occurred: {e}"))

    def _update_progress(self, processed, total, start_time):
        """
        Calculate progress and send it to the queue.
        """
        elapsed_time = time.time() - start_time
        if processed == 0:
            avg_time = 0
        else:
            avg_time = elapsed_time / processed
        remaining = avg_time * (total - processed)
        self.queue.put(("progress", processed, total, remaining))

    def _process_queue(self):
        """
        Process items in the queue and update the GUI accordingly.
        """
        try:
            while True:
                item = self.queue.get_nowait()
                if item[0] == "status":
                    self.lblLoading.config(text=item[1])
                elif item[0] == "progress":
                    processed, total, remaining = item[1], item[2], item[3]
                    progress_percent = (processed /
                                        total) * 100 if total else 0
                    self.progress['value'] = progress_percent
                    self.lblProgress.config(
                        text=f"Progress: {processed}/{total}")
                    remaining_str = self._format_time(remaining)
                    if processed == 0:
                        self.lblTimeRemaining.config(
                            text=f"Estimated time remaining: Unknown")
                    else:
                        self.lblTimeRemaining.config(
                            text=f"Estimated time remaining: {remaining_str}")
                elif item[0] == "error":
                    self.lblLoading.config(
                        text="Scraping completed with errors.")
                    messagebox.showerror('Scraping Complete', item[1])
                elif item[0] == "complete":
                    self.lblLoading.config(text=item[1])
                    messagebox.showinfo('Scraping Complete', item[1])
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._process_queue)

    def _format_time(self, seconds):
        """
        Format time in seconds to H:M:S.
        """
        seconds = int(seconds)
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        if h > 0:
            return f"{h}h {m}m {s}s"
        elif m > 0:
            return f"{m}m {s}s"
        else:
            return f"{s}s"

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

    def _scrap_directly(self, email, password, input_bibliography):
        """
        Run the scraping process directly using provided arguments in CLI mode.
        (Non-GUI usage)
        """
        self.logFile = open(self.logFileName,
                            "a",
                            encoding="utf-8",
                            errors="ignore")
        scrapper = SemanticScholarScrapper(self.logFile,
                                           self.path,
                                           email=email,
                                           password=password)

        # We'll also open saveFile for writing new data in non-GUI mode
        if not os.path.exists(self.saveFileName):
            with open(self.saveFileName, "w", encoding="utf-8",
                      newline='') as f:
                writer = csv.writer(f, quoting=csv.QUOTE_ALL)
                writer.writerow(["Key", "Title"])
        else:
            # Populate savedKeys
            with open(self.saveFileName,
                      "r",
                      encoding="utf-8",
                      errors='ignore') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'Key' in row and row['Key']:
                        self.savedKeys.add(row['Key'])

        self.saveFile = open(self.saveFileName,
                             "a",
                             encoding="utf-8",
                             errors='ignore',
                             newline='')

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

            # Read the CSV in non-GUI mode
            with open(input_bibliography,
                      'r',
                      encoding='utf-8',
                      errors='ignore') as f:
                reader = csv.DictReader(f)
                data = list(reader)

            if len(data) == 0:
                print(f"Error: The file '{input_bibliography}' is empty.")
                return

            # Check if 'Title' column exists
            if len(data) > 0 and 'Title' not in data[0]:
                print("Error: The input file must contain a 'Title' column.")
                return

            total_items = len(data)
            processed_items = 0
            start_time = time.time()

            for index, row in enumerate(data):
                title = row.get('Title', '')
                row_key = row.get('Key', '')

                print(f"Processing {index + 1}/{total_items}: {title}")
                self.logFile.write(f"Searching {title}...\n")

                if row_key in self.savedKeys:
                    print(
                        f"Skipping '{title}' because it has already been saved."
                    )
                    self.logFile.write(
                        f"Skipping '{title}' because it has already been saved.\n"
                    )
                    processed_items += 1
                    self._print_progress(processed_items, total_items,
                                         start_time)
                    continue

                # Scrape the paper
                has_add_paper = scrapper.scrap_paper_by_title(
                    title, call_browser=False)
                if not has_add_paper:
                    print(f"Warning: Could not add '{title}'.")
                    self.logFile.write(f"Warning: Could not add '{title}'.\n")
                    processed_items += 1
                    self._print_progress(processed_items, total_items,
                                         start_time)
                    continue

                # Add alerts and save to library
                scrapper.cancel_create_paper_alert()
                add_alert = scrapper.alert()
                save_to_library = scrapper.save_to_library()

                if not add_alert and not save_to_library:
                    msg = f"Could not add alert for '{title}'.\n"
                    self.logFile.write(msg)
                    print(msg)
                elif not add_alert:
                    self.logFile.write(
                        f"Could not add alert for '{title}', but added it to library.\n"
                    )
                    print(
                        f"Could not add alert for '{title}', but added it to library.\n"
                    )
                elif not save_to_library:
                    self.logFile.write(
                        f"Could not save '{title}' to library, but added it to alert.\n"
                    )
                    print(
                        f"Could not save '{title}' to library, but added it to alert.\n"
                    )
                else:
                    self.logFile.write(f"Added '{title}' successfully.\n")
                    print(f"Added '{title}' successfully.")

                # Write to saveFile
                sanitized_key = row_key.replace('"', '""')
                sanitized_title = title.replace('"', '""').replace(',', ' ')
                self.saveFile.write(
                    f"\"{sanitized_key}\", \"{sanitized_title}\"\n")
                self.saveFile.flush()
                self.savedKeys.add(row_key)

                self.logFile.write(
                    f"Added '{title}' to save file: {self.saveFileName}\n")
                print(f"Added '{title}' to save file: {self.saveFileName}")

                processed_items += 1
                self._print_progress(processed_items, total_items, start_time)

            print("Scraping completed.")
            self.logFile.write("Scraping completed.\n")
            print("All data processed successfully.")

        except Exception as e:
            self.logFile.write(f"Unexpected error during scraping: {e}\n")
            print(f"Error: {e}")

        finally:
            scrapper._close_browser()
            self.saveFile.close()
            self.logFile.close()

    def _process_queue(self):
        """
        Overridden queue processor for the GUI.
        This method is duplicated at the bottom of the file,
        so it needs a unique name (or we unify them).
        """
        try:
            while True:
                item = self.queue.get_nowait()
                if item[0] == "status":
                    self.lblLoading.config(text=item[1])
                elif item[0] == "progress":
                    processed, total, remaining = item[1], item[2], item[3]
                    progress_percent = (processed /
                                        total) * 100 if total else 0
                    self.progress['value'] = progress_percent
                    self.lblProgress.config(
                        text=f"Progress: {processed}/{total}")
                    remaining_str = self._format_time(remaining)
                    self.lblTimeRemaining.config(
                        text=f"Estimated time remaining: {remaining_str}")
                elif item[0] == "error":
                    self.lblLoading.config(
                        text="Scraping completed with errors.")
                    messagebox.showerror('Scraping Complete', item[1])
                elif item[0] == "complete":
                    self.lblLoading.config(text=item[1])
                    messagebox.showinfo('Scraping Complete', item[1])
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._process_queue)

    def _format_time(self, seconds):
        """
        Overridden time formatting for the GUI.
        """
        seconds = int(seconds)
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        if h > 0:
            return f"{h}h {m}m {s}s"
        elif m > 0:
            return f"{m}m {s}s"
        else:
            return f"{s}s"

    def _print_progress(self, processed, total, start_time):
        """
        Print CLI-mode progress and estimated time.
        """
        elapsed_time = time.time() - start_time
        if processed == 0:
            avg_time = 0
        else:
            avg_time = elapsed_time / processed
        remaining = avg_time * (total - processed)

        # Format time
        remaining_str = self._format_time(remaining)
        elapsed_str = self._format_time(elapsed_time)

        # Print progress
        print(
            f"Progress: {processed}/{total} - Elapsed Time: {elapsed_str} - Estimated Remaining Time: {remaining_str}",
            end="\r",
        )

    def MainLoop(self):
        self.root.mainloop()


if __name__ == "__main__":
    # Initialize argument parser
    parser = argparse.ArgumentParser(description="Semantic Scholar Scraper")
    parser.add_argument("-l",
                        "--login",
                        type=str,
                        help="Your Semantic Scholar login (email).")
    parser.add_argument("-i",
                        "--input_bibliography",
                        type=str,
                        help="Path to the input bibliography CSV file.")
    args = parser.parse_args()

    if args.login and args.input_bibliography:
        # Prompt for the password securely
        password = getpass.getpass(
            prompt="Enter your Semantic Scholar password: ")

        # Run in non-GUI mode
        path = get_base_directory()
        log_file_name = os.path.join(path, "log.txt")
        save_file_name = os.path.join(path, "saveDataSC.csv")

        main = MainGUI()
        main.path = path
        main.logFileName = log_file_name
        main.saveFileName = save_file_name
        main._scrap_directly(args.login, password, args.input_bibliography)
    else:
        # Run GUI mode
        gui = MainGUI()
        gui.MainLoop()
