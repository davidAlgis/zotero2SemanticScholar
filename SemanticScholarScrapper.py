# code based on https://github.com/dnasc/semantic-scholar-scrapper/blob/master/main.py
# great re
import os
import sys
import time

import distance
from collections import deque

import selenium
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from tkinter import messagebox


class SemanticScholarScrapper(object):
    """
    A Web Scrapper for Semantic Scholar.
    """
    # _web_driver = webdriver.Firefox()

    def __init__(self, log_file, path, timeout=15, time_between_api_call=0.3, headless=True,
                 site_url='https://www.semanticscholar.org/',
                 site_sign_in_url='https://www.semanticscholar.org/sign-in'):
        """

        :param timeout: Number of seconds the web driver should wait before raising a timeout error.
        :param time_between_api_call: Time in seconds between api calls.
        :param headless: If set to be true, the web driver launches a browser (chrome) in silent mode.
        :param site_url: Home for semantic scholar search engine.
        """
        self._site_url = site_url
        self._site_sign_in_url = site_sign_in_url
        self._web_driver: webdriver.Firefox = None
        self._path = path

        self._timeout = timeout
        self._time_between_api_call = time_between_api_call
        self._headless = headless
        self.is_connected = False
        self.log_file = log_file

    def scrap_paper_list_by_title(self, paper_title_list: list) -> dict:
        """
        Given a list of paper titles, this method retrieves their associated data from semantic scholar.

        :param paper_title_list: A list of paper titles.

        :return: A dictionary of dictionaries containing papers data.
        """

        self._start_browser()
        papers_dict = dict()

        for paper_name in tqdm.tqdm(paper_title_list):
            try:
                paper_dict = self.scrap_paper_by_title(
                    str(paper_name), call_browser=False)
                paper_id = paper_dict['paperId']
                papers_dict[paper_id] = paper_dict
            except KeyError:
                pass

        self._close_browser()

        return papers_dict

    def scrap_paper_by_title(self, paper_title: str, call_browser=True) -> bool:
        """
        Given a paper title, this method retrieves its associated data from semantic scholar.

        :param paper_title: A paper title.
        :param call_browser: True when web browser hasn't be started yet.

        return:
        """
        if call_browser:
            self._start_browser()
        self._search_paper_by_name(str(paper_title))
        hasOpenFirstLink = self._open_first_link_in_search_page()
        if (hasOpenFirstLink == False):
            return False
        return self._check_paper_page(str(paper_title))

    def _open_first_link_in_search_page(self) -> bool:
        """
        Given the browser is on a search page, go to the first paper link.
        """

        hasFind = self._wait_element_by_class_name(
            'dropdown-filters__result-count')

        if (hasFind == False):
            return False

        papers_div = self._web_driver.find_element(By.CLASS_NAME,
                                                   'result-page')
        first_paper_link = papers_div.find_element(
            By.CLASS_NAME, 'cl-paper-title')

        first_paper_link.click()
        return True

    def _check_paper_page(self, paper_title) -> bool:
        """
        Check if opened paper web page is indeed related to paper title.

        :param paper_title: A paper title.

        :return: true if the paper result and search seems to corresponds, else false
        """

        self._wait_element_by_tag_name('h1')

        h1 = self._web_driver.find_element(
            By.CSS_SELECTOR, 'h1[data-test-id="paper-detail-title"]')
        title = h1.text
        if not 0 <= distance.levenshtein(str(paper_title), title) <= 10:
            print(str(paper_title) + " seems to not corresponds to the first title " +
                  title + " that has been found on semantic scholar")
            return False
        return True

    def _search_paper_by_name(self, paper_title) -> None:
        """
        Go to the search page for 'paper_name'.
        """
        self._web_driver.get(str(
            "https://www.semanticscholar.org/search?q=" + str(paper_title) + "&sort=relevance"))

    def _wait_element_by_tag_name(self, tag_name, msg="") -> bool:
        """
        Make driver wait while web browser loads tags with specific name.
        """

        try:
            element_present = expected_conditions.presence_of_element_located(
                (By.TAG_NAME, tag_name))
            WebDriverWait(self._web_driver, self._timeout).until(
                element_present)
        except TimeoutException:
            print("Error - " + msg +
                  "\nTimeoutException - could not find "+class_name)
            self.log_file.write(
                "Error - " + msg + "\nTimeoutException - could not find "+class_name)
            return False
            # raise
        return True

    def _wait_element_by_name(self, name, msg="") -> bool:
        """
        Make driver wait while browser loads elements with specific name.
        """

        try:
            element_present = expected_conditions.presence_of_element_located(
                (By.NAME, name))
            WebDriverWait(self._web_driver, self._timeout).until(
                element_present)
        except TimeoutException:
            print("Error - " + msg +
                  "\nTimeoutException - could not find "+class_name)
            self.log_file.write(
                "Error - " + msg + "\nTimeoutException - could not find "+class_name)
            return False
            # raise
        return True

    def _wait_element_by_class_name(self, class_name, msg="") -> bool:
        """
        Make driver wait while browser loads elements with specific class name.
        """

        try:
            element_present = expected_conditions.presence_of_element_located(
                (By.CLASS_NAME, class_name))
            WebDriverWait(self._web_driver, self._timeout).until(
                element_present)
        except TimeoutException:
            print("Error - " + msg +
                  "\nTimeoutException - could not find "+class_name)
            self.log_file.write(
                "Error - " + msg + "\nTimeoutException - could not find "+class_name)
            return False
            # raise
        return True

    def _close_browser(self):
        self._web_driver.close()

    def connect_to_account(self, email, passwd) -> bool:
        """
        Connect with the given email and password to a SemanticScholar account 
        wait until it has been connected
        """
        self._start_browser()
        self._web_driver.get(self._site_sign_in_url)
        id_email = 'email'
        hasFind = self._wait_element_by_name(
            id_email, "Could not connect to the login page.")

        if (hasFind == False):
            return False
        email_input_box = self._web_driver.find_element("name", id_email)
        email_input_box.send_keys(email)

        passwd_input_box = self._web_driver.find_element(
            By.XPATH, "//input[@type='password']")
        passwd_input_box.send_keys(passwd)
        login_button_class = "cl-button__label"

        login_button = self._web_driver.find_element(
            By.XPATH, "//span[text()='Sign In']")
        login_button.click()

        hasFind = self._wait_element_by_class_name(
            "search-input__label", "Unable to sign-in.")
        if (hasFind == False):
            return False

        self.is_connected = True
        return True

    def alert(self):
        """
        Add an alert on an article. Make sure to be in the page 
        of the article, before calling this function
        """
        disableAlert = False
        try:
            self._web_driver.find_element(
                By.XPATH, "//span[text()='Disable Alert']")
        except NoSuchElementException:
            disableAlert = True

        if (disableAlert == False):
            return True

        alertText = 'Activate Alert'
        try:
            self._web_driver.find_element(
                By.XPATH, str("//span[text()='"+alertText+"']"))
        except NoSuchElementException:
            alertText = 'Create Alert'
            try:
                self._web_driver.find_element(
                    By.XPATH, str("//span[text()='"+alertText+"']"))
            except NoSuchElementException:
                if (disableAlert):
                    print("Unable to add alert")
                    return False

        try:
            self._web_driver.find_element(By.XPATH, str(
                "//span[text()='"+alertText+"']")).click()
        except Exception as e:
            print(f"Unable to click on alert text...: {e}")
            return False
        return True

    def save_to_library(self) -> bool:
        """
        Save an article to library. Make sure to be in the page 
        of the article, before calling this function
        """
        inLibrary = False
        try:
            self._web_driver.find_element(
                By.XPATH, "//span[text()='In Library']")
        except NoSuchElementException:
            inLibrary = True

        if (inLibrary == False):
            return True

        try:
            element = self._web_driver.find_element(
                By.XPATH, "//span[text()='Save to Library']")
        except NoSuchElementException:
            if (inLibrary):
                print("Could not find the library button")
                return False

        # Use JavaScript to click the element, avoiding potential 
        # ElementClickInterceptedException error
        self._web_driver.execute_script("arguments[0].click();", element)

        return True

    def _start_browser(self):

        options = webdriver.FirefoxOptions()
        options.add_argument("-headless")  # Here
        if os.name == 'nt':
            driverService = Service(self._path + "//driver//geckodriver.exe")
            self._web_driver = webdriver.Firefox(
                service=driverService, options=options)
        else:
            self._web_driver = webdriver.Firefox(options=options)
