import json
import logging
from typing import Final
import time

import requests
from requests.exceptions import ConnectionError, HTTPError, RequestException
from http import HTTPStatus
from bs4 import BeautifulSoup
from datetime import date, timedelta

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s", level=logging.INFO
)

DAY_INTERVAL: Final = "d"
HOUR_INTERVAL: Final = "h"
FIFTEEN_MINUTE_INTERVAL: Final = "mi"

def get_past_date(days_back: int = 1) -> date:
    """
    Get a date based on a number of days back from today
    :rtype: date
    :param days_back: The number of days back to get the date for
    :return: The date in the past
    """
    return date.today() - timedelta(days=days_back)

day_before_yesterday = get_past_date(2)
yesterday = get_past_date(1)
today = date.today()

class Evergy:
    def __init__(self, username, password):
        self.logged_in = False
        self.session = None
        self.username = username
        self.password = password
        self.usage_data = None
        self.dashboard_data = None
        self.account_number = None
        self.premise_id = None
        self.login_url = "https://www.evergy.com/log-in"
        self.logout_url = "https://www.evergy.com/logout"
        self.account_summary_url = (
            "https://www.evergy.com/sc-api/account/getaccountpremiseselector?isWidgetPage=false&hasNoSelector=false"
        )
        self.account_dashboard_url = "https://www.evergy.com/api/account/{accountNum}/dashboard/current"
        self.usageDataUrl = "https://www.evergy.com/api/report/usage/{premise_id}?interval={interval}&from={start}&to={end}"

    def get_response(self,
                     url: str = None) -> requests.Response:
        # handle connection/timeout exceptions/request errors
        usage_response = None
        nb_tries = 5
        retry_codes = [
            HTTPStatus.TOO_MANY_REQUESTS,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            HTTPStatus.BAD_GATEWAY,
            HTTPStatus.SERVICE_UNAVAILABLE,
            HTTPStatus.GATEWAY_TIMEOUT,
        ]
        not_logged_in_codes = [
            HTTPStatus.BAD_REQUEST,
            HTTPStatus.UNAUTHORIZED,
            HTTPStatus.FORBIDDEN,
            HTTPStatus.METHOD_NOT_ALLOWED,
            ]

        for n in range(nb_tries):
            try:
                usage_response = self.session.get(url)
                usage_response.raise_for_status()
                break

            except ConnectionError as e:
                logging.info("Connection Error: {}. Sleeping for {} seconds and try again.".format(e, n))
                sleep(n)

                continue

            # A 403 is return if the user got logged out from inactivity
            except HTTPError as e:
                code = e.response.status_code
                if code in retry_codes:
                    logging.info("Received HTTP {}, try again in {} seconds".format(code,n))
                    sleep(n)
                elif code in not_logged_in_codes:
                    logging.info("Received HTTP {}, logging in again".format(code))
                    self.login()
                else:
                    logging.error("Unhandled Http Error. Response code: {}".format(code))
                    usage_response = None
                    break

                continue

            except RequestException as e:
                logging.error("Received Invalid Request. Response code: {}".format(e))
                usage_response = None
                break

        return usage_response

    def login(self):
        self.session = requests.Session()
        logging.info("Logging in with username: " + self.username)
        login_form = self.get_response(self.login_url)
        if login_form.status_code != 200:
            logging.info(f"Web Status Code: {login_form.status_code}, Evergy Webservice Unavailable!")
            self.logged_in = False
        else:
            login_form_soup = BeautifulSoup(login_form.text, "html.parser")
            csrf_token = login_form_soup.select(".login-form > input")[0]["value"]
            csrf_token_name = login_form_soup.select(".login-form > input")[0]["name"]
            login_payload = {
                "Username": str(self.username),
                "Password": str(self.password),
                csrf_token_name: csrf_token,
            }
            r = self.session.post(
                url=self.login_url, data=login_payload, allow_redirects=False
            )
            logging.debug("Login response: " + str(r.status_code))
            r = self.get_response(self.account_summary_url)
            account_data = r.json()
            if len(account_data) == 0:
                self.logged_in = False
            else:
                self.account_number = account_data[0]['accountNumber']
                self.dashboard_data = self.get_response(
                    self.account_dashboard_url.format(accountNum=self.account_number)
                ).json()
                self.premise_id = self.dashboard_data["addresses"][0]["premiseId"]
                self.logged_in = (
                    self.account_number is not None and self.premise_id is not None
                )

    def logout(self):
        logging.info("Logging out")
        return_data = self.get_response(url=self.logout_url)
        self.session = None
        self.logged_in = False

    def get_usage(self, days: int = 1, interval: str = DAY_INTERVAL) -> [dict]:
        """
        Gets the energy usage for previous days up until today. Useful for getting the most recent data.
        :rtype: [dict]
        :param days: The number of back to get data for.
        :param interval: The time period between each data element in the returned data. Default is days.
        :return: A list of usage elements. The number of elements will depend on the `interval` argument.
        """
        return self.get_usage_range(get_past_date(days_back=days - 1), get_past_date(0), interval=interval)

    def get_usage_range(self, start: date = get_past_date(0), end: date = get_past_date(0),
                        interval: str = DAY_INTERVAL) -> [dict]:
        """
        Gets a specific range of historical usage. Could be useful for reporting.
        :param start: The date to begin getting data for (inclusive)
        :param end: The last date to get data for (inclusive)
        :param interval: The time period between each data element in the returned data. Default is days.
        :return: A list of usage elements. The number of elements will depend on the `interval` argument.
        """
        if not self.logged_in:
            self.login()
        if start > end:
            logging.error("'start' date can't be after 'end' date")
            raise Exception("'start' date can't be after 'end' date")
        url = self.usageDataUrl.format(
            premise_id=self.premise_id, interval=interval, start=start, end=end
        )
        logging.info("Fetching {}".format(url))
        usage_response = self.get_response(url)
        # all errors handled above
        if usage_response == None:
            self.usage_data = None
            return None
        else:
            self.usage_data = usage_response.json()["data"]
            return {"usage": self.usage_data , "dashboard": self.dashboard_data}

