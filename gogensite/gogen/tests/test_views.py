from gogen.models import *
from datetime import datetime, timedelta
from selenium import webdriver
from django.test import Client, RequestFactory
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from ..helpers import test_helper


class RegisterLoginPageCase(StaticLiveServerTestCase):

    # test that register page loads
    # test that login page loads
    # consider adding the following as methods in test_helper.py:
    # test that can register
    # test that can login
    # test that can logout
    pass

class DailyUberCase(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()
        service = Service("/usr/bin/chromedriver")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        cls.selenium = webdriver.Chrome(options=chrome_options, service=service)
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_can_load_daily_uber(self):
        # TODO: Test logged in as well
        client = Client()
        response = client.get('/')

        self.assertEqual(response.status_code, 200)
        
    def test_can_unsucessfully_complete_daily_uber(self): 
        self.selenium.get(f"{self.live_server_url}/")
        letter_input = self.selenium.find_element(By.NAME, "01_letter")
        letter_input.send_keys('Z')
        submit_button = self.selenium.find_element(By.NAME, "submit_button")
        submit_button.click()
        status_heading = self.selenium.find_element(By.CLASS_NAME, "fadingHeading").text

        self.assertEqual(status_heading, "Incorrect!")

    def test_can_sucessfully_complete_daily_uber(self):
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
        puzzle = test_helper.get_puzzle("uber", yesterday)

        solution_board = puzzle[5]

        self.selenium.get(f"{self.live_server_url}/")

        letter_input = self.selenium.find_elements(By.CLASS_NAME, "form-control")

        # Go through each input box and put in correct letter
        for item in letter_input:
            item.send_keys(solution_board[int(item.get_attribute("name")[0])][int(item.get_attribute("name")[1])])

        submit_button = self.selenium.find_element(By.NAME, "submit_button")
        submit_button.click()
        status_heading = self.selenium.find_element(By.CLASS_NAME, "fadingHeading").text

        self.assertEqual(status_heading, "Correct!")


class PuzzlePageCase(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()
        service = Service("/usr/bin/chromedriver")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        cls.selenium = webdriver.Chrome(options=chrome_options, service=service)
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_can_add_placeholder(self):
        self.selenium.get(f"{self.live_server_url}/")
        ghost_button = self.selenium.find_element(By.NAME, "ghost_button")
        ghost_button.click()
        letter_input = self.selenium.find_element(By.NAME, "01_letter")
        letter_input.send_keys('Z')
        placeholder_value = letter_input.get_attribute("placeholder")

        self.assertEqual(placeholder_value, 'Z')

    def test_can_reset(self):
        self.selenium.get(f"{self.live_server_url}/")
        letter_input = self.selenium.find_element(By.NAME, "01_letter")
        letter_input.send_keys('Z')
        notes_input = self.selenium.find_element(By.ID, "notes_box")
        notes_input.send_keys("test notes")
        reset_button = self.selenium.find_element(By.NAME, "reset_button")
        reset_button.click()
        alert = self.selenium.switch_to.alert

        self.assertEqual(alert.text, "Are you sure you want to reset?")

        alert.accept()

        self.assertEqual(letter_input.get_attribute("value"), '')
        self.assertEqual(notes_input.get_attribute("value"), '')

    def test_can_save(self):
        # Don't need to check if data actually in DB, that's for models testing.
        # Just check a successful response
        pass

    def test_can_load(self):
        # Check letters, placeholders and notes all load
        pass

    def test_can_next(self):
        pass

    def test_letters_cross_off(self):
        pass

    def test_words_cross_off(self):
        pass


class SettingsPageCase(StaticLiveServerTestCase):

    # test that settings page loads
    # test that submit button works and return succesful response in each case.
    # test each settings does what it should.
    pass


class LeaderboardPageCase(StaticLiveServerTestCase):

    # test that leaderboard loads
    # test that leaderboard is sorted correctly
    pass


class PuzzleListPageCase(StaticLiveServerTestCase):

    # test that puzzle lists load
    # test that puzzle lists are sorted correctly
    pass
