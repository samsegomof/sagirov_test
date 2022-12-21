import os
import time 
import sqlite3
import datetime
import aiohttp

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver import FirefoxOptions
from webdriver_manager.firefox import GeckoDriverManager


from telegram_part import send_screenshot


SCREENSHOT_DIR = ''  # Desired directory for screenshots

# Default screenshot folder #
if SCREENSHOT_DIR == '':
    try:
        os.mkdir('screenshots/')
    except FileExistsError:
        pass

    SCREENSHOT_DIR = 'screenshots/'


class DatabaseCommunication:
    """This class is for database SQL commands"""

    def __init__(self):
        self.con = sqlite3.connect('forms') # Connection
        self.cur = self.con.cursor() # Cursor

    def get_request(self):
        """Gets request data from 'forms' database and returns it"""
        earliest_request = self.cur.execute("SELECT * FROM forms ORDER BY form_time LIMIT 1").fetchone()
        return earliest_request

    def delete_request(self):
        """Deletes the previous request from DB after every cycle"""
        self.cur.execute("DELETE FROM forms ORDER BY form_time LIMIT 1")
        self.con.commit()


class Selenium():
    """This class is for any selenium automatic work functions"""

    def __init__(self):

        self.opts = FirefoxOptions()
        self.opts.add_argument("--headless")
        self.browser = webdriver.Firefox(executable_path=GeckoDriverManager().install(), options=self.opts)
        self.browser.get('https://b24-iu5stq.bitrix24.site/backend_test/')
        self.browser.maximize_window()

    def fill_first_page(self, first_name, last_name):
        """Fills first page input fields NAME, LASTNAME and clicks continue"""

        # Clear fields #
        self.browser.find_element(By.NAME, 'name').clear()
        self.browser.find_element(By.NAME, 'lastname').clear()

        # Fill fields #
        self.browser.find_element(By.NAME, 'name').send_keys(first_name)
        self.browser.find_element(By.NAME, 'lastname').send_keys(last_name)

        # Click continue #
        self.browser.find_element(
            By.XPATH,
            '/html/body/main/div/section/div/div/div/div/div/div/div/div/div[2]/form/div[3]/div/button'
            ).click()

    def fill_second_page(self, email, phone):
        """Fills second page input fields EMAIL, PHONE and clicks continue"""

        # Clear fields #
        self.browser.find_element(By.NAME, "email").clear()
        self.browser.find_element(By.NAME, "phone").clear()

        # Fill fields #
        self.browser.find_element(By.NAME, "email").send_keys(email)
        self.browser.find_element(By.NAME, "phone").send_keys(phone)

        # Click continue #
        self.browser.find_element(
            By.XPATH,
            '/html/body/main/div/section/div/div/div/div/div/div/div/div/div[2]/form/div[3]/div[2]/button'
            ).click()

    def fill_third_page(self, birth_date):
        """Fills third page input dropdown and clicks send"""

        # Open dropdown table #
        self.browser.find_element(
            By.XPATH, 
            '/html/body/main/div/section/div/div/div/div/div/div/div/div/div[2]/form/div[2]/div/div/div/div/div[1]/input'
            ).click()
        
        # Select year #
        Select(self.browser.find_element( 
            By.XPATH, 
            '/html/body/main/div/section/div/div/div/div/div/div/div/div/div[2]/form/div[2]/div/div/ \
            div/div/div[2]/div/div[2]/div/div/header/div/div[2]/select'
            )).select_by_value(birth_date[0])

        # Select month #
        Select(self.browser.find_element( 
            By.XPATH, 
            '/html/body/main/div/section/div/div/div/div/div/div/div/div/div[2]/form/div[2]/div/div/ \
            div/div/div[2]/div/div[2]/div/div/header/div/div[1]/select'
            )).select_by_value(str(int(birth_date[1]) - 1))

        # Select day from cells #
        self.browser.find_element(By.CLASS_NAME, 'vdpCell').find_element(
            By.XPATH, f"//div[text()='{int(birth_date[2])}']").click()
        self.browser.find_element(
            By.XPATH,
            '/html/body/main/div/section/div/div/div/div/div/div/div/div/div[2]/form/div[4]/div[2]/button'
            ).click()

    def make_screenshot(self, user_id):
        """Simply makes a screenshot in the desired folder SCREENSHOT_DIR"""
        screenshot_time = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M_') # Screenshot time for naming
        screenshot_name = os.path.join(SCREENSHOT_DIR, f"{screenshot_time}<{user_id}>.png")
        self.browser.get_screenshot_as_file(screenshot_name) # Makes screenshot
        return screenshot_name

    def update_page(self):
        """Updates page"""
        self.browser.refresh()


class Async:
    """Class for running cycle"""

    def __init__(self):
        self.selenium_bot = Selenium()
        self.database_controller = DatabaseCommunication()

    async def run(self):
        """Starts selenium bot infinity cycle"""
        while True:
            try:
                request_data = self.database_controller.get_request()
                first_name, last_name, email, phone, birth_date, user_id, form_time = request_data

                birth_date = birth_date.split('-')
                
                self.selenium_bot.fill_first_page(first_name, last_name)
                time.sleep(1)
                self.selenium_bot.fill_second_page(email, phone)
                time.sleep(1)
                self.selenium_bot.fill_third_page(birth_date)
                time.sleep(5)

                screenshot = self.selenium_bot.make_screenshot(user_id)
                await send_screenshot(chat_id=user_id, screenshot=screenshot)
                
            except TypeError as typeer: # TypeError happens here if there's no data in DB (didn't see other Type events fn)
                print(typeer)
                print('Нет заявок')
            
            except aiohttp.ClientConnectorError:
                print('Проблема с подключением к Telegram')
                continue
            except Exception as exc:  # Any other exception is about wrong data
                print(exc)
                print('Данные недействительны')
                
            finally: # happens anyway
                self.database_controller.delete_request()  # delete request from bd
                time.sleep(600)  # 10 min timeout
                self.selenium_bot.update_page()  # updating page
        

thread = Async()  # Create cycle object



    
    
    


