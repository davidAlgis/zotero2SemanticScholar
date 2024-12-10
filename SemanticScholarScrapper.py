# SemanticScholarScrapper.py

import os
import time
import distance
from seleniumbase import Driver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By


class SemanticScholarScrapper(object):
    """
    A Web Scrapper for Semantic Scholar using SeleniumBase.
    """

    def __init__(self,
                 log_file,
                 path,
                 timeout=15,
                 time_between_api_call=0.3,
                 headless=False,
                 site_url='https://www.semanticscholar.org/',
                 site_sign_in_url='https://www.semanticscholar.org/sign-in'):
        """
        Initializes the SemanticScholarScrapper.

        :param log_file: File object for logging.
        :param path: Path to the driver and other resources.
        :param timeout: Seconds to wait for elements.
        :param time_between_api_call: Delay between API calls.
        :param headless: Run browser in headless mode.
        :param site_url: Base URL for Semantic Scholar.
        :param site_sign_in_url: Sign-in URL for Semantic Scholar.
        """
        self._site_url = site_url
        self._site_sign_in_url = site_sign_in_url
        self._driver = None
        self._path = path

        self._timeout = timeout
        self._time_between_api_call = time_between_api_call
        self._headless = headless
        self.is_connected = False
        self.log_file = log_file

    def scrap_paper_list_by_title(self, paper_title_list: list) -> dict:
        """
        Given a list of paper titles, retrieve their data from Semantic Scholar.

        :param paper_title_list: A list of paper titles.
        :return: A dictionary containing paper data.
        """
        self._start_browser()
        papers_dict = dict()

        for paper_name in paper_title_list:
            try:
                paper_dict = self.scrap_paper_by_title(str(paper_name),
                                                       call_browser=False)
                if paper_dict:
                    paper_id = paper_dict.get('paperId')
                    if paper_id:
                        papers_dict[paper_id] = paper_dict
            except KeyError:
                pass

        self._close_browser()
        return papers_dict

    def scrap_paper_by_title(self,
                             paper_title: str,
                             call_browser=True) -> bool:
        """
        Given a paper title, retrieve its data from Semantic Scholar.

        :param paper_title: A paper title.
        :param call_browser: Start the browser if not already started.
        :return: True if successful, False otherwise.
        """
        if call_browser:
            self._start_browser()

        self._search_paper_by_name(str(paper_title))
        has_opened = self._open_first_link_in_search_page()

        if not has_opened:
            return False

        return self._check_paper_page(str(paper_title))

    def cancel_create_paper_alert(self):
        """
        If the popup for creating a paper alert is open, click the cancel button to dismiss it.
        """
        try:
            # Check if the popup is present
            popup_selector = "html body div#app div.cl-overlay.cl-overlay__content-position--center div.cl-overlay__content div.flex-row div.cl-modal__content.cl-modal__centered-offset.alert-modal div.alert-modal__content"
            cancel_button_selector = (
                "html body div#app div.cl-overlay.cl-overlay__content-position--center "
                "div.cl-overlay__content div.flex-row div.cl-modal__content.cl-modal__centered-offset.alert-modal "
                "div.alert-modal__content div.alert-modal__alert-information form.create-alert-content "
                "section.form-buttons button.cl-button.cl-button--no-arrow-divider.cl-button--not-icon-only.cl-button--no-icon.cl-button--has-label.cl-button--font-size-.cl-button--icon-pos-left.cl-button--shape-rectangle.cl-button--size-default.cl-button--type-tertiary.cl-button--density-default "
                "span.cl-button__label")

            # Wait for the popup to appear
            if self._wait_element_by_css_selector(popup_selector,
                                                  "Waiting for alert popup"):
                # Locate and click the cancel button
                cancel_button = self._driver.find_element(
                    By.CSS_SELECTOR, cancel_button_selector)
                cancel_button.click()
                print("Alert creation popup canceled successfully.")
            else:
                print("No alert creation popup detected.")
        except Exception as e:
            self.log_file.write(
                f"Error while canceling alert creation popup: {e}\n")
            print(f"Error while canceling alert creation popup: {e}")

    def _open_first_link_in_search_page(self) -> bool:
        """
        On the search page, navigate to the first paper link.
        """
        has_find = self._wait_element_by_class_name(
            'dropdown-filters__result-count')

        if not has_find:
            # Check for error message
            try:
                error_message = self._driver.find_element(
                    By.CSS_SELECTOR, '.error-message__main-text')
                print(
                    "Could not find papers. Semantic Scholar returned an error message:",
                    error_message.text)
                self.log_file.write("Error Message: " + error_message.text +
                                    "\n")
            except NoSuchElementException:
                print(
                    "Could not find papers. No specific error message was returned."
                )
                self.log_file.write(
                    "Error: Could not find papers. No specific error message was returned.\n"
                )
            return False

        try:
            papers_div = self._driver.find_element(By.CLASS_NAME,
                                                   'result-page')
            first_paper_link = papers_div.find_element(By.CLASS_NAME,
                                                       'cl-paper-title')
            first_paper_link.click()
            return True
        except NoSuchElementException as e:
            print("Could not find the first paper link:", str(e))
            self.log_file.write(
                f"Error: Could not find the first paper link: {e}\n")
            return False

    def _check_paper_page(self, paper_title) -> bool:
        """
        Verify if the opened paper page corresponds to the searched title.

        :param paper_title: The title of the paper to verify.
        :return: True if the titles match within a Levenshtein distance of 10, else False.
        """
        if not self._wait_element_by_tag_name('h1'):
            return False

        try:
            h1 = self._driver.find_element(
                By.CSS_SELECTOR, 'h1[data-test-id="paper-detail-title"]')
            title = h1.text
            if not (0 <= distance.levenshtein(str(paper_title), title) <= 10):
                self.log_file.write(
                    f"{paper_title} does not match the found title {title}.\n")
                return False
            return True
        except NoSuchElementException as e:
            self.log_file.write(f"Error finding paper title: {e}\n")
            return False

    def _search_paper_by_name(self, paper_title) -> None:
        """
        Navigate to the search results page for the given paper title.

        :param paper_title: The title of the paper to search for.
        """
        search_url = f"https://www.semanticscholar.org/search?q={paper_title}&sort=relevance"
        self._driver.get(search_url)
        self._driver.set_page_load_timeout(self._timeout)

    def _wait_element_by_tag_name(self, tag_name, msg="") -> bool:
        """
        Wait until an element with the specified tag name is present.

        :param tag_name: The tag name to wait for.
        :param msg: Optional message for logging.
        :return: True if element is found, False otherwise.
        """
        try:
            self._driver.wait_for_element_present(tag_name,
                                                  by=By.TAG_NAME,
                                                  timeout=self._timeout)
        except Exception as e:
            self.log_file.write(
                f"Error - {msg} {e} - could not find tag {tag_name}\n")
            return False
        return True

    def _wait_element_by_name(self, name, msg="") -> bool:
        """
        Wait until an element with the specified name is present.

        :param name: The name attribute to wait for.
        :param msg: Optional message for logging.
        :return: True if element is found, False otherwise.
        """
        try:
            self._driver.wait_for_element_present(name,
                                                  by=By.NAME,
                                                  timeout=self._timeout)
        except Exception as e:
            self.log_file.write(
                f"Error - {msg} {e} - could not find name {name}\n")
            return False
        return True

    def _wait_element_by_class_name(self, class_name, msg="") -> bool:
        """
        Wait until an element with the specified class name is present.

        :param class_name: The class name to wait for.
        :param msg: Optional message for logging.
        :return: True if element is found, False otherwise.
        """
        try:
            self._driver.wait_for_element_present(class_name,
                                                  by=By.CLASS_NAME,
                                                  timeout=self._timeout)
        except Exception as e:
            self.log_file.write(
                f"Error - {msg} {e} - could not find class {class_name}\n")
            return False
        return True

    def _close_browser(self):
        """
        Close the SeleniumBase driver.
        """
        if self._driver:
            self._driver.quit()

    def connect_to_account(self, email, passwd) -> bool:
        """
        Log in to a Semantic Scholar account.

        :param email: User's email.
        :param passwd: User's password.
        :return: True if connected successfully, False otherwise.
        """
        self._start_browser()
        self._driver.get(self._site_sign_in_url)
        self._driver.set_page_load_timeout(self._timeout)
        id_email = 'email'
        has_find = self._wait_element_by_name(
            id_email, "Could not connect to the login page.")

        if not has_find:
            return False

        try:
            email_input_box = self._driver.find_element(By.NAME, id_email)
            email_input_box.send_keys(email)

            passwd_input_box = self._driver.find_element(
                By.XPATH, "//input[@type='password']")
            passwd_input_box.send_keys(passwd)

            login_button = self._driver.find_element(
                By.XPATH, "//span[text()='Sign In']")
            login_button.click()

            has_find = self._wait_element_by_class_name(
                "search-input__label", "Unable to sign-in.")
            if not has_find:
                return False

            self.is_connected = True
            return True
        except NoSuchElementException as e:
            self.log_file.write(f"Login error: {e}\n")
            return False

    def alert(self) -> bool:
        """
        Add an alert on the current article page.

        :return: True if alert added or already present, False otherwise.
        """
        try:
            # Check if 'Disable Alert' exists
            self._driver.find_element(By.XPATH,
                                      "//span[text()='Disable Alert']")
            # Alert is already enabled
            return True
        except NoSuchElementException:
            # Need to enable alert
            alert_texts = ['Activate Alert', 'Create Alert']
            for alert_text in alert_texts:
                try:
                    alert_element = self._driver.find_element(
                        By.XPATH, f"//span[text()='{alert_text}']")
                    alert_element.click()
                    return True
                except NoSuchElementException:
                    continue

            # If neither alert option is found
            self.log_file.write(
                f"Unable to add alert. Neither 'Activate Alert' nor 'Create Alert' found.\n"
            )
            return False

    def save_to_library(self) -> bool:
        """
        Save the current article to the library.

        :return: True if saved successfully or already in library, False otherwise.
        """
        try:
            # Check if already in library
            self._driver.find_element(By.XPATH, "//span[text()='In Library']")
            # Already in library
            return True
        except NoSuchElementException:
            # Need to save to library
            try:
                save_button = self._driver.find_element(
                    By.XPATH, "//span[text()='Save to Library']")
                # Use JavaScript to click to avoid interception
                self._driver.execute_script("arguments[0].click();",
                                            save_button)
                return True
            except NoSuchElementException as e:
                self.log_file.write(f"Save to Library error: {e}\n")
                return False

    def _start_browser(self):
        """
        Initialize the SeleniumBase driver with desired options for Firefox.
        """
        if not self._driver:
            options = {"headless": self._headless}
            try:
                # Initialize the SeleniumBase driver
                self._driver = Driver(browser="firefox", **options)

                # Set the custom user-agent via JavaScript execution
                custom_user_agent = (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/58.0.3029.110 Safari/537.3")
                self._driver.execute_script(
                    f"Object.defineProperty(navigator, 'userAgent', {{get: () => '{custom_user_agent}'}});"
                )

                # Set page load timeout
                self._driver.set_page_load_timeout(self._timeout)

            except TypeError as e:
                self.log_file.write(f"Driver initialization error: {e}\n")
                print(f"Driver initialization error: {e}\n")
                raise
