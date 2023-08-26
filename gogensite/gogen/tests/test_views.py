from gogen.models import *
from datetime import datetime, timedelta
from selenium import webdriver
from django.test import Client
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementClickInterceptedException
from ..helpers import test_helper


def login_user(selenium_driver, live_server_url, username, password):
    User.objects.create_user(username=username, password=password)
    selenium_driver.get(f"{live_server_url}/login")
    username_input = selenium_driver.find_element(By.NAME, "username")
    username_input.send_keys("testuser")
    password_input = selenium_driver.find_element(By.NAME, "password")
    password_input.send_keys("testpassword")
    login_button = selenium_driver.find_element(By.NAME, "login_button")
    login_button.click()


class RegisterLoginPageCase(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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

    def test_can_load_register(self):
        self.selenium.get(f"{self.live_server_url}/register")
        self.assertEqual(self.selenium.title, "Gogen Register")

    def test_can_load_login(self):
        self.selenium.get(f"{self.live_server_url}/login")
        self.assertEqual(self.selenium.title, "Gogen Login")

    def test_can_register_user(self):
        self.selenium.get(f"{self.live_server_url}/register")
        username_input = self.selenium.find_element(By.NAME, "username")
        username_input.send_keys("testuser")
        password_input = self.selenium.find_element(By.NAME, "password1")
        password_input.send_keys("testpassword")
        confirm_password_input = self.selenium.find_element(By.NAME, "password2")
        confirm_password_input.send_keys("testpassword")
        register_button = self.selenium.find_element(By.NAME, "register_button")
        register_button.click()

        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(self.selenium.title, "Daily Uber")

    def test_can_login_and_logout_user(self):
        login_user(self.selenium, self.live_server_url, "testuser", "testpassword")

        self.assertEqual(self.selenium.title, "Daily Uber")

        self.selenium.get(f"{self.live_server_url}/logout")

        self.assertEqual(self.selenium.title, "Gogen Login")



class DailyUberCase(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        # TODO: Test logged in as well and see title?
        client = Client()
        response = client.get('/')

        self.assertEqual(response.status_code, 200)
        
    def test_can_unsucessfully_complete_daily_uber(self): 
        self.selenium.get(f"{self.live_server_url}/")
        letter_input = self.selenium.find_element(By.NAME, "01_letter")
        letter_input.send_keys('A')
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


class PuzzlePageLoggedOutCase(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        placeholder_input = self.selenium.find_element(By.NAME, "01_letter")
        placeholder_input.send_keys('A')
        placeholder_value = placeholder_input.get_attribute("placeholder")

        self.assertEqual(placeholder_value, 'A')

    def test_can_reset(self):
        self.selenium.get(f"{self.live_server_url}/")
        letter_input = self.selenium.find_element(By.NAME, "01_letter")
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

    def test_letters_cross_off(self):
        pass

    def test_words_cross_off(self):
        pass


class PuzzlePageLoggedInCase(StaticLiveServerTestCase):
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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

    def test_can_save_and_load(self):
        login_user(self.selenium, self.live_server_url, "testuser", "testpassword")
        
        self.selenium.get(f"{self.live_server_url}/uber20190120")
        letter_input = self.selenium.find_element(By.NAME, "01_letter")
        letter_input.send_keys('A')
        notes_input = self.selenium.find_element(By.ID, "notes_box")
        notes_input.send_keys("test notes")
        ghost_button = self.selenium.find_element(By.NAME, "ghost_button")
        ghost_button.click()
        placeholder_input = self.selenium.find_element(By.NAME, "03_letter")
        placeholder_input.send_keys('B')
        save_button = self.selenium.find_element(By.NAME, "save_button")
        save_button.click()

        self.selenium.get(f"{self.live_server_url}/uber20190120")
        letter_input = self.selenium.find_element(By.NAME, "01_letter")
        placeholder_input = self.selenium.find_element(By.NAME, "03_letter")
        notes_input = self.selenium.find_element(By.ID, "notes_box")

        self.assertEqual(letter_input.get_attribute("value"), "A")
        self.assertEqual(placeholder_input.get_attribute("placeholder"), "B")
        self.assertEqual(notes_input.get_attribute("value"), "test notes")

    def test_can_next(self):
        login_user(self.selenium, self.live_server_url, "testuser", "testpassword")
        self.selenium.get(f"{self.live_server_url}/uber20190120")
        next_button = self.selenium.find_element(By.NAME, "next_button")
        # No next puzzle so throw not clickable exception
        self.assertRaises(ElementClickInterceptedException, next_button.click)

        self.selenium.get(f"{self.live_server_url}/uber20190121")
        next_button = self.selenium.find_element(By.NAME, "next_button")
        next_button.click()
        self.assertEqual(self.selenium.title, "Uber20190120")


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
