import datetime
import os
import time

import DrissionPage.errors

from .MySqlDBModel import MySQLDatabaseModel
from ..config.project_variables import create_page
from ..errors import OlxTimeoutError, OlxAccountError, OlxPageError
from ..models.SaveAd import AdDataExtractor
from ..models.PostgresDBModel import PostgresDatabaseModel
from ..utils.data_loader import load_account_data
from ..utils.network_listener_for_db import capture_network_response


class OlxAdReposter:
    def __init__(self):
        self.page = create_page()
        self.date_run_script = datetime.datetime.today().replace(second=0, microsecond=0).date()
        self.time_run_script = datetime.datetime.today().replace(second=0, microsecond=0).time()

    async def write_to_db(self, index, source_email: str, source_password: str, database: str):
        try:
            self._authenticate_user(source_email, source_password)
            data = capture_network_response(self.page,
                                            'https://production-graphql.eu-sharedservices.olxcdn.com/graphql')
            if database == 'postgres':
                await PostgresDatabaseModel().store_ad(index, data, self.date_run_script, self.time_run_script)
            else:
                await MySQLDatabaseModel().store_ad(index, data, self.date_run_script, self.time_run_script)
        except Exception as e:
            self.page.close()
            print(e)
            raise OlxAccountError(f"An error occurred while processing the account {source_email}: {e}")

    async def transfer_ad_between_accounts(self, ad_id: int, source_email: str, source_password: str,
                                           target_email: str, target_password: str, database: str):
        try:
            if database == 'postgres':
                ad_id_in_db = await PostgresDatabaseModel().check_ad_in_db(ad_id)
            else:
                ad_id_in_db = await MySQLDatabaseModel().check_ad_in_db(ad_id)
            self._authenticate_user(source_email, source_password)
            AdDataExtractor.extract_and_save_ad_data(self.page, ad_id_in_db)
            self._authenticate_user(target_email, target_password, True)
            self._publish_saved_ad()
            if database == 'postgres':
                await PostgresDatabaseModel.update_is_transferred_field_in_transfer_db(ad_id)
            else:
                await MySQLDatabaseModel.update_is_transferred_field_in_transfer_db(ad_id)
        except DrissionPage.errors.PageDisconnectedError:
            raise OlxPageError("The page either did not load or was closed. Please try again.")
        except DrissionPage.errors.WaitTimeoutError:
            raise OlxTimeoutError("The element was not found within the timeout period.")

    def _authenticate_user(self, email: str, password: str, is_second_account: bool = False):
        self.page.clear_cache()
        self.page.get('https://www.olx.pl/')
        self.page.wait.eles_loaded('xpath://a[@data-testid="myolx-link"]')
        if self.page.ele('xpath://*[@id="onetrust-accept-btn-handler"]'):
            self.page.ele('xpath://*[@id="onetrust-accept-btn-handler"]').click()
        if is_second_account:
            self.page.get('https://www.olx.pl/adding/')
        else:
            self.page.get(
                'http://www.olx.pl/konto/?ref[0][params][url]=http%3A%2F%2Fwww.olx.pl%2F&ref[0][action]=redirector&ref[0][method]=index')

        self.page.ele('xpath://*[@id="username"]').input(email)
        self.page.ele('xpath://*[@id="password"]').input(password)
        self.page.ele('xpath://*[@id="Login"]').click()

    def _publish_saved_ad(self):
        data = load_account_data()

        self.page.ele('xpath://*[@id="title"]', timeout=20).input(data['title'])
        self.page.ele('xpath://button[@class="css-7svm16"]/span[text()="Zmień"]').click()
        self.page.ele('xpath://input[@placeholder="Szukaj"]').input(data['category_label'])
        self.page.ele(f'xpath://div[@class="css-1msmb8o"]/button/span/p[text()="{data["category_label"]}"]').click()
        if self.page.ele('xpath://*[@id="posting-form"]/main/div[2]/div/button'):
            self.page.ele('xpath://*[@id="posting-form"]/main/div[2]/div/button').click()
        for index, image_path in enumerate(data['images']):
            self.page.ele(f'xpath://*[@id="{index}"]').input(image_path)

        self.page.ele('xpath://*[@id="parameters.price.price"]').input(data['price'])
        self.page.scroll.down(800)
        time.sleep(10)
        self.page.wait.eles_loaded(
            locators='xpath://input[@class="n-textinput-input" and @placeholder="Wybierz"]',
            timeout=30)
        for index, param in enumerate(data['params']):
            self.page.eles(
                f"xpath://input[@class='n-textinput-input' and @placeholder='Wybierz']",
                timeout=30)[index].click()
            self.page.ele(f'xpath://a[text()="{param}"]').click()
            time.sleep(2)
        time.sleep(5)
        self.page.scroll.down(800)
        self.page.ele('xpath://*[@id="description"]').clear().input(data['description'])

        for shipping_option in data['shipping']:
            self.page.ele(f'xpath://p[text()="{shipping_option["type"]}"]').click()
            self.page.ele(f'xpath://input[@data-testid="checkbox-{shipping_option["id"]}"]').click()

        self.page.scroll.down(1100)

        if self.page.ele('xpath://*[@id="firstName"]', timeout=5):
            self.page.ele('xpath://*[@id="firstName"]').input(os.getenv('FIRST_NAME'))
            self.page.ele('xpath://*[@id="lastName"]').input(os.getenv('LAST_NAME'))
            self.page.ele('xpath://*[@id="consent"]').click()
        self.page.scroll.to_bottom()

        self.page.ele('xpath://input[@name="city_id"]').input(data['location'])

        self.page.ele('xpath://button[@data-testid="submit-btn"]').click()
        if self.page.ele('xpath://button[@data-cy="purchase-dont-promote"]'):
            self.page.ele('xpath://button[@data-cy="purchase-dont-promote"]').click()
            self.page.ele('xpath://div[@class="css-1buxhyn"]//button[@data-button-variant="primary"]').click()
        else:
            raise OlxAccountError("The trial period for this account has ended. Please create a new one.")

    def page_close(self):
        try:
            self.page.close()
        except DrissionPage.errors.PageDisconnectedError:
            pass
        return
