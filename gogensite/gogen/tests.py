import psycopg
from gogen.models import *
from datetime import datetime, timedelta
from selenium import webdriver
from django.conf import settings
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


def get_puzzle(puzzle_type, puzzle_date):

    url = f"http://www.puzzles.grosse.is-a-geek.com/images/gog/puz/{puzzle_type}/{puzzle_type}{puzzle_date}puz.png"
    
    # Pull the puzzle from the database
    with psycopg.connect(settings.PG_CONNECTION) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM {puzzle_type} WHERE puzzle_url = '{url}';")
            puzzle = cur.fetchone()
            if puzzle is None:
                cur.execute(f"SELECT * FROM {puzzle_type} ORDER BY puzzle_name DESC LIMIT 1;")
                puzzle = cur.fetchone()

    return puzzle


class PostgresTestCase(TestCase):
    test_puzzle_type = "uber"
    test_puzzle_date = "20190120"

    def test_can_get_puzzle_from_db(self):
        puzzle = get_puzzle(self.test_puzzle_type, self.test_puzzle_date)

        name = puzzle[0]
        puz_url = puzzle[1]
        sol_url = puzzle[2]
        words = puzzle[3]
        board = puzzle[4]
        solution_board = puzzle[5]
        
        self.assertEqual(name, "uber20190120")
        self.assertEqual(puz_url, "http://www.puzzles.grosse.is-a-geek.com/images/gog/puz/uber/uber20190120puz.png")
        self.assertEqual(sol_url, "http://www.puzzles.grosse.is-a-geek.com/images/gog/puz/uber/uber20190120sol.png")
        self.assertEqual(words, ["BEGAN", "DOXIE", "FETUS", "GAMP", "GAMY", "GLUED", "GYBED", "GYRO", "JAY", "KUDO", "RHODIC", "ROW", "VIED"])
        self.assertEqual(board, [['V', '', 'X', '', 'W'], ['', '', '', '', ''], ['T', '', 'D', '', 'J'], ['', '', '', '', ''], ['S', '', 'Q', '', 'P']])
        self.assertEqual(solution_board, [['V', 'C', 'X', 'H', 'W'], ['F', 'I', 'B', 'O', 'R'], ['T', 'E', 'D', 'Y', 'J'], ['K', 'U', 'G', 'A', 'M'], ['S', 'L', 'Q', 'N', 'P']])


class PuzzleLogTestCase(TestCase):

    def setUp(self):
        self.test_puzzle_type = "uber"
        self.test_puzzle_date = "20190120"
        self.test_status = "I"
        self.test_board = [['V', '*', 'X', 'H', 'W'], ['*', 'I', 'B', 'O', 'R'], ['T', 'E', 'D', 'Y', 'J'], ['K', 'U', 'G', 'A', 'M'], ['S', 'L', 'Q', 'N', 'P']]
        self.test_placeholders = [['A', 'B', '', '', ''], ['', 'C', '', 'D', ''], ['', '', 'E', '', ''], ['', '', 'F', '', ''], ['', '', 'G', '', '']]
        self.test_notes = "test notes"
        self.test_user = User.objects.create(username="testuser", password="testpassword")
        PuzzleLog.objects.create(
            puzzle_type=self.test_puzzle_type,
            puzzle_date=self.test_puzzle_date,
            status=self.test_status,
            board=self.test_board, 
            placeholders=self.test_placeholders,
            notes=self.test_notes,
            user=self.test_user
        )

    def test_can_complete_puzzle(self):
        user_puzzle_log = PuzzleLog.objects.filter(puzzle_type=self.test_puzzle_type, puzzle_date=self.test_puzzle_date, user=self.test_user)

        user_puzzle_log.update(
            board=[['V', 'C', 'X', 'H', 'W'], ['F', 'I', 'B', 'O', 'R'], ['T', 'E', 'D', 'Y', 'J'], ['K', 'U', 'G', 'A', 'M'], ['S', 'L', 'Q', 'N', 'P']], 
            placeholders = [['', '', '', '', ''], ['', '', '', '', ''], ['', '', '', '', ''], ['', '', '', '', ''], ['', '', '', '', '']],
            status='C',
            notes="test notes with more"
        )

        self.assertEqual(user_puzzle_log[0].board, [['V', 'C', 'X', 'H', 'W'], ['F', 'I', 'B', 'O', 'R'], ['T', 'E', 'D', 'Y', 'J'], ['K', 'U', 'G', 'A', 'M'], ['S', 'L', 'Q', 'N', 'P']])
        self.assertEqual(user_puzzle_log[0].placeholders, [['', '', '', '', ''], ['', '', '', '', ''], ['', '', '', '', ''], ['', '', '', '', ''], ['', '', '', '', '']])
        self.assertEqual(user_puzzle_log[0].status, 'C')
        self.assertEqual(user_puzzle_log[0].notes, "test notes with more")


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
        puzzle = get_puzzle("uber", yesterday)

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


class PuzzleFunctionalityCase(StaticLiveServerTestCase):

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
