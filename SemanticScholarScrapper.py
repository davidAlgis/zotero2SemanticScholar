# SemanticScholarScrapper.py

import os
import time
import distance
import random
from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class SemanticScholarScrapper(object):
    """
    A Web Scraper for Semantic Scholar with enhanced stealth capabilities using SeleniumBase and Undetected-Chromedriver.
    """

    def __init__(self,
                 log_file,
                 path,
                 timeout=15,
                 time_between_api_call=0.3,
                 headless=False,
                 site_url='https://www.semanticscholar.org/',
                 site_sign_in_url='https://www.semanticscholar.org/sign-in',
                 email=None,
                 password=None):
        """
        Initializes the SemanticScholarScrapper.

        :param log_file: File object for logging.
        :param path: Path to the driver and other resources.
        :param timeout: Seconds to wait for elements.
        :param time_between_api_call: Delay between API calls.
        :param headless: Run browser in headless mode.
        :param site_url: Base URL for Semantic Scholar.
        :param site_sign_in_url: Sign-in URL for Semantic Scholar.
        :param email: User's email for re-login.
        :param password: User's password for re-login.
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
        self._email = email  # Store email for re-login
        self._password = password  # Store password for re-login

    def _start_browser(self):
        """
        Initialize a stealthy undetected-chromedriver instance using SeleniumBase.
        """
        if not self._driver:
            try:
                # Initialize SeleniumBase Driver with Undetected-Chromedriver
                self._driver = Driver(uc=True, headless=self._headless)

                # Set a custom user-agent for stealth
                custom_user_agent = (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/115.0.0.0 Safari/537.36")
                self._driver.execute_cdp_cmd("Network.setUserAgentOverride",
                                             {"userAgent": custom_user_agent})
                self._driver.execute_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                )

                # Additional stealth configurations
                self._driver.execute_script("""
                    // Overwrite the `plugins` property to use a custom getter.
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5],
                    });
                    """)

                self._driver.execute_script("""
                    // Overwrite the `languages` property to use a custom getter.
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en'],
                    });
                    """)

                # Set page load timeout
                self._driver.set_page_load_timeout(self._timeout)

                # Log the browser setup
                self.log_file.write("Stealth browser initialized.\n")
                print("Stealth browser initialized.")

            except Exception as e:
                self.log_file.write(f"Driver initialization error: {e}\n")
                print(f"Driver initialization error: {e}\n")
                raise

    def _close_browser(self):
        """
        Close the stealth browser.
        """
        if self._driver:
            self._driver.quit()
            self._driver = None
            self.log_file.write("Browser closed successfully.\n")
            print("Browser closed successfully.")

    def _random_sleep(self, min_delay=2, max_delay=5):
        """
        Introduce a random delay to mimic human behavior.

        :param min_delay: Minimum delay in seconds.
        :param max_delay: Maximum delay in seconds.
        """
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)

    def connect_to_account(self, email, passwd) -> bool:
        """
        Log in to a Semantic Scholar account.

        :param email: User's email.
        :param passwd: User's password.
        :return: True if connected successfully, False otherwise.
        """
        self._start_browser()
        try:
            # Navigate to sign-in page
            self._driver.get(self._site_sign_in_url)
            self._random_sleep(3, 6)

            # Find email input
            email_input = self._driver.find_element(By.NAME, "email")
            email_input.send_keys(email)
            self._random_sleep()

            # Find password input
            password_input = self._driver.find_element(
                By.XPATH, "//input[@type='password']")
            password_input.send_keys(passwd)
            self._random_sleep()

            # Find and click the Sign In button
            login_button = self._driver.find_element(
                By.XPATH, "//span[text()='Sign In']")
            self._driver.execute_script("arguments[0].click();", login_button)
            self._random_sleep(5, 10)

            # Verify login by checking for search input presence
            if self._wait_element_by_class_name("search-input__label",
                                                "Unable to sign-in."):
                self.is_connected = True
                self.log_file.write("Logged in successfully.\n")
                print("Logged in successfully.")
                return True
            else:
                self.log_file.write(
                    "Login failed. Please check credentials.\n")
                print("Login failed. Please check credentials.")
                return False

        except NoSuchElementException as e:
            self.log_file.write(f"Login error: {e}\n")
            print(f"Login error: {e}\n")
            return False
        except Exception as e:
            self.log_file.write(f"Unexpected error during login: {e}\n")
            print(f"Unexpected error during login: {e}\n")
            return False

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

        # Use the updated method without unsupported `uc_open_with_reconnect`
        self._search_paper_by_name(str(paper_title))
        has_opened = self._open_first_link_in_search_page()

        if not has_opened:
            return False

        return self._check_paper_page(str(paper_title))

    def _search_paper_by_name(self, paper_title) -> None:
        """
        Navigate to the search results page for the given paper title.

        :param paper_title: The title of the paper to search for.
        """
        try:
            search_url = f"https://www.semanticscholar.org/search?q={paper_title}&sort=relevance"
            self._driver.get(search_url)
            self._random_sleep(3, 6)
            self.log_file.write(f"Search initiated for: {paper_title}\n")
            print(f"Search initiated for: {paper_title}")
        except Exception as e:
            self.log_file.write(
                f"Error during search for {paper_title}: {e}\n")
            print(f"Error during search for {paper_title}: {e}")

    def _open_first_link_in_search_page(self) -> bool:
        """
        On the search page, navigate to the first paper link.
        If a semantic error is encountered, restart the browser and re-log in.
        """
        has_find = self._wait_element_by_class_name(
            'dropdown-filters__result-count', "Waiting for search results.")

        if not has_find:
            # Check for error message
            try:
                error_message = self._driver.find_element(
                    By.CSS_SELECTOR, '#main-content > p.error-message__code')
                print(
                    "Could not find papers. Semantic Scholar returned an error message:",
                    error_message.text,
                    ". You might need to increase the wait time between each paper search, see the readme.md."
                )
                self.log_file.write(
                    "Error Message: " + error_message.text +
                    ". You might need to increase the wait time between each paper search, see the readme.md.\n"
                )

                # Restart the browser and re-login
                self._restart_and_relogin()
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
            # Scroll into view to mimic human behavior
            self._driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});",
                first_paper_link)
            self._random_sleep()

            # Use JavaScript to click to avoid interception
            self._driver.execute_script("arguments[0].click();",
                                        first_paper_link)
            self._random_sleep()
            return True
        except NoSuchElementException as e:
            print("Could not find the first paper link:", str(e))
            self.log_file.write(
                f"Error: Could not find the first paper link: {e}\n")
            # Restart the browser and re-login
            self._restart_and_relogin()
            return False
        except Exception as e:
            print(f"Unexpected error when clicking the first paper link: {e}")
            self.log_file.write(
                f"Unexpected error when clicking the first paper link: {e}\n")
            self._restart_and_relogin()
            return False

    def _check_paper_page(self, paper_title) -> bool:
        """
        Verify if the opened paper page corresponds to the searched title.

        :param paper_title: The title of the paper to verify.
        :return: True if the titles match within a Levenshtein distance of 10, else False.
        """
        if not self._wait_element_by_tag_name('h1',
                                              "Waiting for paper title."):
            return False

        try:
            h1 = self._driver.find_element(
                By.CSS_SELECTOR, 'h1[data-test-id="paper-detail-title"]')
            title = h1.text
            distance_score = distance.levenshtein(str(paper_title), title)
            if not (0 <= distance_score <= 10):
                self.log_file.write(
                    f"{paper_title} does not match the found title {title} (Levenshtein distance: {distance_score}).\n"
                )
                return False
            self.log_file.write(
                f"Title matched: {title} (Levenshtein distance: {distance_score}).\n"
            )
            return True
        except NoSuchElementException as e:
            self.log_file.write(f"Error finding paper title: {e}\n")
            return False
        except Exception as e:
            self.log_file.write(
                f"Unexpected error while verifying paper title: {e}\n")
            return False

    def _wait_element_by_tag_name(self, tag_name, msg="") -> bool:
        """
        Wait until an element with the specified tag name is present.

        :param tag_name: The tag name to wait for.
        :param msg: Optional message for logging.
        :return: True if element is found, False otherwise.
        """
        try:
            for _ in range(self._timeout):
                elements = self._driver.find_elements(By.TAG_NAME, tag_name)
                if elements:
                    return True
                time.sleep(1)
            self.log_file.write(
                f"Error - {msg} Could not find tag {tag_name}\n")
            return False
        except Exception as e:
            self.log_file.write(
                f"Error - {msg} {e} - could not find tag {tag_name}\n")
            return False

    def _wait_element_by_name(self, name, msg="") -> bool:
        """
        Wait until an element with the specified name is present.

        :param name: The name attribute to wait for.
        :param msg: Optional message for logging.
        :return: True if element is found, False otherwise.
        """
        try:
            for _ in range(self._timeout):
                elements = self._driver.find_elements(By.NAME, name)
                if elements:
                    return True
                time.sleep(1)
            self.log_file.write(f"Error - {msg} Could not find name {name}\n")
            return False
        except Exception as e:
            self.log_file.write(
                f"Error - {msg} {e} - could not find name {name}\n")
            return False

    def _wait_element_by_class_name(self, class_name, msg="") -> bool:
        """
        Wait until an element with the specified class name is present.

        :param class_name: The class name to wait for.
        :param msg: Optional message for logging.
        :return: True if element is found, False otherwise.
        """
        try:
            for _ in range(self._timeout):
                elements = self._driver.find_elements(By.CLASS_NAME,
                                                      class_name)
                if elements:
                    return True
                time.sleep(1)
            self.log_file.write(
                f"Error - {msg} Could not find class {class_name}\n")
            return False
        except Exception as e:
            self.log_file.write(
                f"Error - {msg} {e} - could not find class {class_name}\n")
            return False

    def cancel_create_paper_alert(self):
        """
        If the popup for creating a paper alert is open, click the cancel button to dismiss it.
        """
        try:
            # Check if the popup is present
            popup_selector = (
                "html body div#app div.cl-overlay.cl-overlay__content-position--center "
                "div.cl-overlay__content div.flex-row div.cl-modal__content.cl-modal__centered-offset.alert-modal "
                "div.alert-modal__content")
            cancel_button_selector = (
                "html body div#app div.cl-overlay.cl-overlay__content-position--center "
                "div.cl-overlay__content div.flex-row div.cl-modal__content.cl-modal__centered-offset.alert-modal "
                "div.alert-modal__content div.alert-modal__alert-information form.create-alert-content "
                "section.form-buttons button.cl-button.cl-button--no-arrow-divider.cl-button--not-icon-only.cl-button--no-icon.cl-button--has-label.cl-button--font-size-.cl-button--icon-pos-left.cl-button--shape-rectangle.cl-button--size-default.cl-button--type-tertiary.cl-button--density-default "
                "span.cl-button__label")

            # Wait for the popup to appear
            for _ in range(self._timeout):
                try:
                    popup = self._driver.find_element(By.CSS_SELECTOR,
                                                      popup_selector)
                    cancel_button = self._driver.find_element(
                        By.CSS_SELECTOR, cancel_button_selector)
                    self._driver.execute_script("arguments[0].click();",
                                                cancel_button)
                    self.log_file.write(
                        "Alert creation popup canceled successfully.\n")
                    print("Alert creation popup canceled successfully.")
                    self._random_sleep()
                    return
                except NoSuchElementException:
                    time.sleep(1)
            print("No alert creation popup detected.")
            self.log_file.write("No alert creation popup detected.\n")

        except Exception as e:
            self.log_file.write(
                f"Error while canceling alert creation popup: {e}\n")
            print(f"Error while canceling alert creation popup: {e}")

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
            self.log_file.write("Alert is already enabled.\n")
            print("Alert is already enabled.")
            return True
        except NoSuchElementException:
            # Need to enable alert
            alert_texts = ['Activate Alert', 'Create Alert']
            for alert_text in alert_texts:
                try:
                    alert_element = self._driver.find_element(
                        By.XPATH, f"//span[text()='{alert_text}']")
                    self._driver.execute_script("arguments[0].click();",
                                                alert_element)
                    self._random_sleep()
                    self.log_file.write(
                        f"Alert '{alert_text}' added successfully.\n")
                    print(f"Alert '{alert_text}' added successfully.")
                    return True
                except NoSuchElementException:
                    continue

            # If neither alert option is found
            self.log_file.write(
                f"Unable to add alert. Neither 'Activate Alert' nor 'Create Alert' found.\n"
            )
            print(
                "Unable to add alert. Neither 'Activate Alert' nor 'Create Alert' found."
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
            self.log_file.write("Paper is already in library.\n")
            print("Paper is already in library.")
            return True
        except NoSuchElementException:
            # Need to save to library
            try:
                save_button = self._driver.find_element(
                    By.XPATH, "//span[text()='Save to Library']")
                # Use JavaScript to click to avoid interception
                self._driver.execute_script("arguments[0].click();",
                                            save_button)
                self._random_sleep()
                self.log_file.write("Paper saved to library successfully.\n")
                print("Paper saved to library successfully.")
                return True
            except NoSuchElementException as e:
                self.log_file.write(f"Save to Library error: {e}\n")
                print(f"Save to Library error: {e}")
                return False

    def _restart_and_relogin(self):
        """
        Restart the browser and re-log into the Semantic Scholar account.
        """
        try:
            # Close the current browser session
            self._close_browser()

            # Start a new browser session
            self._start_browser()

            # Log in again
            self.log_file.write("Re-logging into Semantic Scholar...\n")
            print("Re-logging into Semantic Scholar...")
            is_connected = self.connect_to_account(self._email, self._password)

            if is_connected:
                self.log_file.write("Re-login successful.\n")
                print("Re-login successful.")
            else:
                self.log_file.write(
                    "Re-login failed. Please check credentials.\n")
                print("Re-login failed. Please check credentials.")
        except Exception as e:
            self.log_file.write(
                f"Error during browser restart and re-login: {e}\n")
            print(f"Error during browser restart and re-login: {e}")
