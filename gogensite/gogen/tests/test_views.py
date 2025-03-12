from gogen.models import *
from datetime import datetime, timedelta
from selenium import webdriver
from django.test import Client
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.support.wait import WebDriverWait
from ..helpers import test_helper
import time

def login_user(selenium_driver, live_server_url, username, password):
    User.objects.create_user(username=username, password=password)
    selenium_driver.get(f"{live_server_url}/login")
    username_input = selenium_driver.find_element(By.NAME, "username")
    username_input.send_keys("testuser")
    password_input = selenium_driver.find_element(By.NAME, "password")
    password_input.send_keys("testpassword")
    login_button = selenium_driver.find_element(By.NAME, "login_button")
    login_button.click()

    wait_for_title(selenium_driver, "Daily Uber")


def wait_for_title(selenium_driver, title):
    wait = WebDriverWait(selenium_driver, timeout=5)
    wait.until(lambda _ : selenium_driver.title == title)

class RegisterLoginPageCase(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        service = Service("/snap/bin/chromium.chromedriver")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument('--remote-debugging-pipe')
        cls.selenium = webdriver.Chrome(options=chrome_options, service=service)
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()    

    def test_can_load_register(self):
        self.selenium.get(f"{self.live_server_url}/register")
        wait_for_title(self.selenium, "Gogen Register")

        self.assertEqual(self.selenium.title, "Gogen Register")

    def test_can_load_login(self):
        self.selenium.get(f"{self.live_server_url}/login")
        wait_for_title(self.selenium, "Gogen Login")

        self.assertEqual(self.selenium.title, "Gogen Login")

    def test_can_register_user(self):
        self.selenium.get(f"{self.live_server_url}/register")
        wait_for_title(self.selenium, "Gogen Register")

        username_input = self.selenium.find_element(By.NAME, "username")
        username_input.send_keys("testregisteruser")
        password_input = self.selenium.find_element(By.NAME, "password1")
        password_input.send_keys("thisisatestuserpassword")
        confirm_password_input = self.selenium.find_element(By.NAME, "password2")
        confirm_password_input.send_keys("thisisatestuserpassword")
        register_button = self.selenium.find_element(By.NAME, "register_button")
        register_button.click()
        time.sleep(1)

        self.assertEqual(User.objects.count(), 1)

    def test_can_login_and_logout_user(self):
        login_user(self.selenium, self.live_server_url, "testuser", "testpassword")
        wait_for_title(self.selenium, "Daily Uber")

        self.assertEqual(self.selenium.title, "Daily Uber")

        self.selenium.get(f"{self.live_server_url}/logout")

        self.assertEqual(self.selenium.title, "Gogen Login")



class DailyUberCase(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        service = Service("/snap/bin/chromium.chromedriver")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument('--remote-debugging-pipe')
        cls.selenium = webdriver.Chrome(options=chrome_options, service=service)
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    @classmethod
    def complete_daily_uber(self):
        today = datetime.now().strftime('%Y%m%d')
        puzzle = test_helper.get_puzzle("uber", today)

        solution_board = puzzle[5]

        self.selenium.get(f"{self.live_server_url}/")

        wait_for_title(self.selenium, "Daily Uber")

        letter_input = self.selenium.find_elements(By.CLASS_NAME, "letter_input")

        # Go through each input box and put in correct letter
        for item in letter_input:
            item.send_keys(solution_board[int(item.get_attribute("name")[0])][int(item.get_attribute("name")[1])])

        submit_button = self.selenium.find_element(By.NAME, "submit_button")
        submit_button.click()
        wait_for_title(self.selenium, "Daily Uber")
        time.sleep(1)

        status_heading = self.selenium.find_element(By.CLASS_NAME, "fadingHeading")

        return status_heading.text

    def test_can_load_daily_uber(self):
        self.selenium.get(f"{self.live_server_url}/")

        wait_for_title(self.selenium, "Daily Uber")

        self.assertEqual(self.selenium.title, "Daily Uber")
        
    def test_can_unsucessfully_complete_daily_uber(self): 
        self.selenium.get(f"{self.live_server_url}/")
        wait_for_title(self.selenium, "Daily Uber")

        letter_input = self.selenium.find_element(By.NAME, "01_board_letter")
        letter_input.send_keys('A')
        submit_button = self.selenium.find_element(By.NAME, "submit_button")
        submit_button.click()
        wait_for_title(self.selenium, "Daily Uber")
        time.sleep(1)

        status_heading = self.selenium.find_element(By.CLASS_NAME, "fadingHeading")

        self.assertEqual(status_heading.text, "Incorrect!")

    def test_can_sucessfully_complete_daily_uber(self):
        status_heading = self.complete_daily_uber()

        self.assertEqual(status_heading, "Correct!")

    def test_can_sucessfully_complete_daily_uber_logged_in(self):
        login_user(self.selenium, self.live_server_url, "testuser", "testpassword")

        status_heading = self.complete_daily_uber()

        self.assertEqual(status_heading, "Correct!")

        self.selenium.get(f"{self.live_server_url}/")
        submit_button = self.selenium.find_element(By.NAME, "submit_button")
        submit_button.click()
        wait_for_title(self.selenium, "Daily Uber")
        time.sleep(1)

        status_heading = self.selenium.find_element(By.CLASS_NAME, "fadingHeading")
        self.assertEqual(status_heading.text, "Correct!")


class PuzzlePageLoggedOutCase(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        service = Service("/snap/bin/chromium.chromedriver")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument('--remote-debugging-pipe')
        cls.selenium = webdriver.Chrome(options=chrome_options, service=service)
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_can_add_placeholder(self):
        self.selenium.get(f"{self.live_server_url}/")
        wait_for_title(self.selenium, "Daily Uber")

        ghost_button = self.selenium.find_element(By.NAME, "ghost_button")
        ghost_button.click()
        placeholder_input = self.selenium.find_element(By.NAME, "01_board_letter")
        placeholder_input.send_keys('A')
        placeholder_value = placeholder_input.get_attribute("placeholder")

        self.assertEqual(placeholder_value, 'A')

    def test_can_reset(self):
        self.selenium.get(f"{self.live_server_url}/")
        wait_for_title(self.selenium, "Daily Uber")

        letter_input = self.selenium.find_element(By.NAME, "01_board_letter")
        letter_input.send_keys('A')
        notes_input = self.selenium.find_element(By.ID, "notes_box")
        notes_input.send_keys("test notes")
        reset_button = self.selenium.find_element(By.NAME, "reset_button")
        reset_button.click()
        alert = self.selenium.switch_to.alert

        self.assertEqual(alert.text, "Are you sure you want to reset?")

        alert.accept()

        self.assertEqual(letter_input.get_attribute("value"), '')
        self.assertEqual(notes_input.get_attribute("value"), '')


class PuzzlePageLoggedInCase(StaticLiveServerTestCase):
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        service = Service("/snap/bin/chromium.chromedriver")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument('--remote-debugging-pipe')
        cls.selenium = webdriver.Chrome(options=chrome_options, service=service)
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_can_save_and_load(self):
        login_user(self.selenium, self.live_server_url, "testuser", "testpassword")
        self.selenium.get(f"{self.live_server_url}/uber20190120")
        wait_for_title(self.selenium, "Uber20190120")

        letter_input = self.selenium.find_element(By.NAME, "01_board_letter")
        letter_input.send_keys('A')
        notes_input = self.selenium.find_element(By.ID, "notes_box")
        notes_input.send_keys("test notes")
        ghost_button = self.selenium.find_element(By.NAME, "ghost_button")
        ghost_button.click()
        placeholder_input = self.selenium.find_element(By.NAME, "03_board_letter")
        placeholder_input.send_keys('B')
        save_button = self.selenium.find_element(By.NAME, "save_button")
        wait = WebDriverWait(self.selenium, timeout=5)
        save_button.click()

        wait.until(lambda _ : "saved" in save_button.get_attribute("class"))

        self.selenium.get(f"{self.live_server_url}/uber20190120")
        wait_for_title(self.selenium, "Uber20190120")

        letter_input = self.selenium.find_element(By.NAME, "01_board_letter")
        placeholder_input = self.selenium.find_element(By.NAME, "03_board_letter")
        notes_input = self.selenium.find_element(By.ID, "notes_box")

        self.assertEqual(letter_input.get_attribute("value"), "A")
        self.assertEqual(placeholder_input.get_attribute("placeholder"), "B")
        self.assertEqual(notes_input.get_attribute("value"), "test notes")

    # def test_already_existing_puzzlelog(self):
    #     login_user(self.selenium, self.live_server_url, "testuser", "testpassword")

    #     PuzzleLog.objects.create(puzzle_type="uber", puzzle_date="20190120", board=[['V', 'C', 'X', 'H', 'W'], ['F', 'I', 'B', 'O', 'R'], ['T', 'E', 'D', 'Y', 'J'], ['K', 'U', 'G', 'A', 'M'], ['S', 'L', 'Q', 'N', 'P']], placeholders=[], status="C", user=User.objects.get(username="testuser"))
    #     self.selenium.get(f"{self.live_server_url}/uber20190120")
    #     submit_button = self.selenium.find_element(By.NAME, "submit_button")
    #     submit_button.click()

    #     status_heading = self.selenium.find_element(By.CLASS_NAME, "fadingHeading").text
    #     self.assertEqual(status_heading, "Correct!")

    #     self.selenium.get(f"{self.live_server_url}/uber20190120")

    #     submit_button = self.selenium.find_element(By.NAME, "submit_button")
    #     submit_button.click()

    #     status_heading = self.selenium.find_element(By.CLASS_NAME, "fadingHeading").text
    #     self.assertEqual(status_heading, "Correct!")

    def test_can_next(self):
        login_user(self.selenium, self.live_server_url, "testuser", "testpassword")
        self.selenium.get(f"{self.live_server_url}/uber20190120")
        wait_for_title(self.selenium, "Uber20190120")

        next_button = self.selenium.find_element(By.NAME, "next_button")
        # No next puzzle so throw not clickable exception
        self.assertRaises(ElementClickInterceptedException, next_button.click)

        PuzzleLog.objects.create(puzzle_type="uber", puzzle_date="20190121", board=[], placeholders=[], status="C", user=User.objects.get(username="testuser"))
        self.selenium.get(f"{self.live_server_url}/uber20190122")
        next_button = self.selenium.find_element(By.NAME, "next_button")
        next_button.click()
        self.assertEqual(self.selenium.title, "Uber20190120")

    def test_can_next_with_some_solved(self):
        login_user(self.selenium, self.live_server_url, "testuser", "testpassword")
        PuzzleLog.objects.create(puzzle_type="uber", puzzle_date="20190131", board=[], placeholders=[], status="C", user=User.objects.get(username="testuser"))
        PuzzleLog.objects.create(puzzle_type="uber", puzzle_date="20190130", board=[], placeholders=[], status="C", user=User.objects.get(username="testuser"))
        PuzzleLog.objects.create(puzzle_type="uber", puzzle_date="20190129", board=[], placeholders=[], status="I", user=User.objects.get(username="testuser"))

        self.selenium.get(f"{self.live_server_url}/uber20190201")
        wait_for_title(self.selenium, "Uber20190201")

        next_button = self.selenium.find_element(By.NAME, "next_button")
        next_button.click()
        self.assertEqual(self.selenium.title, "Uber20190129")

    def test_can_next_with_gap(self):
        login_user(self.selenium, self.live_server_url, "testuser", "testpassword")
        PuzzleLog.objects.create(puzzle_type="uber", puzzle_date="20190120", board=[], placeholders=[], status="C", user=User.objects.get(username="testuser"))

        self.selenium.get(f"{self.live_server_url}/uber20190122")
        wait_for_title(self.selenium, "Uber20190122")

        next_button = self.selenium.find_element(By.NAME, "next_button")
        next_button.click()
        self.assertEqual(self.selenium.title, "Uber20190121")

    def test_letters_cross_off(self):
        login_user(self.selenium, self.live_server_url, "testuser", "testpassword")
        self.selenium.get(f"{self.live_server_url}/uber20190120")
        wait_for_title(self.selenium, "Uber20190120")

        letter_input = self.selenium.find_element(By.NAME, "01_board_letter")
        letter_input.send_keys('A')
        a_remaining_letter = self.selenium.find_element(By.NAME, "A_remaining_letter")
        self.assertEqual(a_remaining_letter.get_attribute("style"), "text-decoration: line-through; color: rgb(211, 211, 211);")

    def test_words_cross_off(self):
        login_user(self.selenium, self.live_server_url, "testuser", "testpassword")
        self.selenium.get(f"{self.live_server_url}/uber20190120")
        wait_for_title(self.selenium, "Uber20190120")
        
        letter_input = self.selenium.find_element(By.NAME, "10_board_letter")
        letter_input.send_keys('B')
        letter_input = self.selenium.find_element(By.NAME, "11_board_letter")
        letter_input.send_keys('E')
        letter_input = self.selenium.find_element(By.NAME, "12_board_letter")
        letter_input.send_keys('G')
        letter_input = self.selenium.find_element(By.NAME, "13_board_letter")
        letter_input.send_keys('A')
        letter_input = self.selenium.find_element(By.NAME, "14_board_letter")
        letter_input.send_keys('N')

        began_word = self.selenium.find_element(By.NAME, "BEGAN_word")
        self.assertEqual(began_word.get_attribute("style"), "text-decoration: line-through; color: rgb(211, 211, 211);")


class SettingsPageCase(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        service = Service("/snap/bin/chromium.chromedriver")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument('--remote-debugging-pipe')
        cls.selenium = webdriver.Chrome(options=chrome_options, service=service)
        cls.selenium.implicitly_wait(10)
        NoteTemplate.objects.create(name="test name", template="test template")

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_can_load_settings(self):
        login_user(self.selenium, self.live_server_url, "testuser", "testpassword")
        self.selenium.get(f"{self.live_server_url}/settings")
        wait_for_title(self.selenium, "Gogen Settings")

        self.assertEqual(self.selenium.title, "Gogen Settings")

    def test_can_change_settings(self):
        login_user(self.selenium, self.live_server_url, "testuser", "testpassword")
        self.selenium.get(f"{self.live_server_url}/settings")
        wait_for_title(self.selenium, "Gogen Settings")

        test_user = User.objects.get(username="testuser")
        self.assertEqual(test_user.settings.notes_enabled, True)
        notes_input = self.selenium.find_element(By.NAME, "notes_enabled")
        notes_input.click()

        save_button = self.selenium.find_element(By.NAME, "save_button")
        wait = WebDriverWait(self.selenium, timeout=5)
        save_button.click()

        wait.until(lambda _ : "saved" in save_button.get_attribute("class"))
        
        test_user = User.objects.get(username="testuser")
        self.assertEqual(test_user.settings.notes_enabled, False)

    def test_can_change_notes_preset(self):
        login_user(self.selenium, self.live_server_url, "testuser", "testpassword")
        self.selenium.get(f"{self.live_server_url}/settings")
        wait_for_title(self.selenium, "Gogen Settings")

        test_user = User.objects.get(username="testuser")
        self.assertEqual(test_user.settings.preset_notes, None)
        notes_input = self.selenium.find_element(By.NAME, "notes_preset_1")
        notes_input.click()

        save_button = self.selenium.find_element(By.NAME, "save_button")
        wait = WebDriverWait(self.selenium, timeout=5)
        save_button.click()

        wait.until(lambda _ : "saved" in save_button.get_attribute("class"))

        test_user = User.objects.get(username="testuser")
        self.assertEqual(test_user.settings.preset_notes.name, "test name")
        self.assertEqual(test_user.settings.preset_notes.template, "test template")
        
        self.selenium.get(f"{self.live_server_url}/uber20190120")
        wait_for_title(self.selenium, "Uber20190120")

        notes_input = self.selenium.find_element(By.ID, "notes_box")

        self.assertEqual(notes_input.get_attribute("value"), "test template")


class LeaderboardPageCase(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        service = Service("/snap/bin/chromium.chromedriver")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument('--remote-debugging-pipe')
        cls.selenium = webdriver.Chrome(options=chrome_options, service=service)
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_can_load_leaderboard(self):
        login_user(self.selenium, self.live_server_url, "testuser", "testpassword")
        self.selenium.get(f"{self.live_server_url}/leaderboard")
        wait_for_title(self.selenium, "Gogen Leaderboard")
        
        self.assertEqual(self.selenium.title, "Gogen Leaderboard")

    def test_is_leaderboard_sorted(self):
        login_user(self.selenium, self.live_server_url, "testuser", "testpassword")

        test_user = User.objects.get(username="testuser")

        PuzzleLog.objects.create(puzzle_type="uber", puzzle_date="20190120", board=[], placeholders=[], status="C", user=test_user)
        
        test_user2 = User.objects.create_user(username="testuser2", password="testpassword")
        PuzzleLog.objects.create(puzzle_type="uber", puzzle_date="20190120", board=[], placeholders=[], status="C", user=test_user2)
        PuzzleLog.objects.create(puzzle_type="uber", puzzle_date="20190121", board=[], placeholders=[], status="C", user=test_user2)

        self.selenium.get(f"{self.live_server_url}/leaderboard")
        wait_for_title(self.selenium, "Gogen Leaderboard")

        self.assertEqual(self.selenium.title, "Gogen Leaderboard")

        leaderboard_table = self.selenium.find_element(By.NAME, "leaderboard_table")
        table_rows = leaderboard_table.find_elements(By.TAG_NAME, "tr")

        self.assertEqual(table_rows[1].find_elements(By.TAG_NAME, "td")[1].text, "testuser2")
        self.assertEqual(table_rows[2].find_elements(By.TAG_NAME, "td")[1].text, "testuser")


class PuzzleListPageCase(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        service = Service("/snap/bin/chromium.chromedriver")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument('--remote-debugging-pipe')
        cls.selenium = webdriver.Chrome(options=chrome_options, service=service)
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_can_load_puzzle_list(self):
        login_user(self.selenium, self.live_server_url, "testuser", "testpassword")
        self.selenium.get(f"{self.live_server_url}/puzzlelist/uber")
        wait_for_title(self.selenium, "Uber Puzzle List")

        self.assertEqual(self.selenium.title, "Uber Puzzle List")

        self.selenium.get(f"{self.live_server_url}/puzzlelist/ultra")
        wait_for_title(self.selenium, "Ultra Puzzle List")

        self.assertEqual(self.selenium.title, "Ultra Puzzle List")

        self.selenium.get(f"{self.live_server_url}/puzzlelist/hyper")
        wait_for_title(self.selenium, "Hyper Puzzle List")

        self.assertEqual(self.selenium.title, "Hyper Puzzle List")

    def test_can_click_on_puzzle(self):
        login_user(self.selenium, self.live_server_url, "testuser", "testpassword")
        self.selenium.get(f"{self.live_server_url}/puzzlelist/uber")
        wait_for_title(self.selenium, "Uber Puzzle List")

        puzzle_table = self.selenium.find_element(By.NAME, "puzzle_table")
        puzzle_link = puzzle_table.find_elements(By.TAG_NAME, "a")[0]
        uber_name = puzzle_link.text

        puzzle_link.click()
        self.assertEqual(self.selenium.title, f"Uber{uber_name}")

    def test_can_change_page_by_button(self):
        login_user(self.selenium, self.live_server_url, "testuser", "testpassword")
        self.selenium.get(f"{self.live_server_url}/puzzlelist/uber")
        wait_for_title(self.selenium, "Uber Puzzle List")

        self.assertEqual(self.selenium.title, "Uber Puzzle List")
        page_button = self.selenium.find_element(By.NAME, "2_page_button")

        page_button.click()

        self.assertEqual(self.selenium.title, "Uber Puzzle List")
        self.assertEqual(self.selenium.current_url, f"{self.live_server_url}/puzzlelist/uber?page=2")

    def test_can_change_page_by_input(self):
        login_user(self.selenium, self.live_server_url, "testuser", "testpassword")
        self.selenium.get(f"{self.live_server_url}/puzzlelist/uber")
        wait_for_title(self.selenium, "Uber Puzzle List")

        page_input = self.selenium.find_element(By.NAME, "page")

        page_input.send_keys("2")

        submit_button = self.selenium.find_element(By.ID, "submit_button")
        submit_button.click()
        wait_for_title(self.selenium, "Uber Puzzle List")
        time.sleep(1)

        self.assertEqual(self.selenium.title, "Uber Puzzle List")
        self.assertEqual(self.selenium.current_url, f"{self.live_server_url}/puzzlelist/uber?page=2")

    def test_cannot_go_to_invalid_page(self):
        login_user(self.selenium, self.live_server_url, "testuser", "testpassword")
        self.selenium.get(f"{self.live_server_url}/puzzlelist/uber?page=9999")
        wait_for_title(self.selenium, "Uber Puzzle List")

        self.assertEqual(self.selenium.title, "Uber Puzzle List")
        self.assertEqual(self.selenium.current_url, f"{self.live_server_url}/puzzlelist/uber")

    def test_complete_puzzles_are_ticked_off(self):
        login_user(self.selenium, self.live_server_url, "testuser", "testpassword")
        self.selenium.get(f"{self.live_server_url}/puzzlelist/uber")
        wait_for_title(self.selenium, "Uber Puzzle List")

        puzzle_table = self.selenium.find_element(By.NAME, "puzzle_table")
        uber_name = puzzle_table.find_elements(By.TAG_NAME, "a")[0]
        puzzle_status = puzzle_table.find_elements(By.TAG_NAME, "td")[1]
        self.assertEqual(puzzle_status.text, "-")

        PuzzleLog.objects.create(puzzle_type="uber", puzzle_date=uber_name.text, board=[], placeholders=[], status="C", user=User.objects.get(username="testuser"))

        self.selenium.get(f"{self.live_server_url}/puzzlelist/uber")
        wait_for_title(self.selenium, "Uber Puzzle List")

        puzzle_table = self.selenium.find_element(By.NAME, "puzzle_table")
        puzzle_status = puzzle_table.find_elements(By.TAG_NAME, "td")[1]

        self.assertEqual(puzzle_status.text, "✓")

