#!/usr/bin/env python

import argparse
import getpass
import logging
import pytz
import sys
import requests

from bs4 import BeautifulSoup
from datetime import datetime, timedelta


TZ = pytz.timezone('America/New_York')
###############################################################################
# Requirements
#
# pip install beautifulsoup4
# pip install pytz
# pip install requests
#
# Config values:

# Title of the reservation
RESERVATION_TITLE = 'Laser BUS'

# Add as many reservations here as needed
RESERVATIONS = [
    datetime(2024, 10, 26, hour=14, minute=0, tzinfo=TZ),
    # datetime(2024, 10, 29, hour=18, minute=0, tzinfo=TZ),
    # datetime(2024, 11, 6, hour=18, minute=0, tzinfo=TZ),
]

# How long is the reservation
RESERVATION_LENGTH = timedelta(hours=2)

# What to reserve. Valid values: 'laser', 'cnc', 'welding'
RESOURCE = 'laser'

###############################################################################

# Don't change these unless you know what you're doing
URL = 'https://civicrm.fatcatfablab.org'
LOGIN_ENDPOINT = '/node?destination=node'
RESERVE_ENDPOINT = '/node/add/merci-reservation'
RESOURCES = {
    'cnc': '13',
    'laser': '14',
    'welding': '6757',
}

log = logging.getLogger(__name__)


def extract_input_value(soup: BeautifulSoup, name: str):
    for i in soup.find_all('input'):
        if i['name'] == name:
            return i['value']

    raise Exception("form_build_id not found")


def login(s: requests.Session, user: str, passw: str):
    log.debug('retrieving login form')
    r = s.get(f'{URL}')
    r.raise_for_status()

    soup = BeautifulSoup(r.text, 'html.parser')
    form_build_id = extract_input_value(soup, 'form_build_id')

    log.debug('posting login data')
    s.post(
        f'{URL}{LOGIN_ENDPOINT}',
        data={
            'name': user,
            'pass': passw,
            'form_build_id': form_build_id,
            'form_id': 'user_login_block',
            'op': 'Log+in',
        },
    ).raise_for_status()


def make_reservation(s: requests.Session, start: datetime):
    log.debug("getting reservation form")
    r = s.get(f'{URL}{RESERVE_ENDPOINT}')
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': f'{URL}',
        'Priority': 'u=0, i',
        'Referer': f'{URL}{RESERVE_ENDPOINT}',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
    }

    end = start + RESERVATION_LENGTH
    log.debug('making reservation from %s to %s', start, end)
    s.post(f'{URL}{RESERVE_ENDPOINT}', headers=headers, data={
        'title': RESERVATION_TITLE,
        'field_merci_date[und][0][value][date]': start.strftime('%m/%d/%Y'),
        'field_merci_date[und][0][value][time]': start.strftime('%H:%M'),
        'field_merci_date[und][0][value2][date]': end.strftime('%m/%d/%Y'),
        'field_merci_date[und][0][value2][time]': end.strftime('%H:%M'),
        'changed': '',
        'form_build_id': extract_input_value(soup, 'form_build_id'),
        'form_token': extract_input_value(soup, 'form_token'),
        'form_id': 'merci_reservation_node_form',
        'merci_reservation_items[choice_1][merci_item_nid]': RESOURCES[RESOURCE],
        'merci_reservation_items[choice_2][merci_item_nid]': '',
        'merci_reservation_items[choice_3][merci_item_nid]': '',
        'additional_settings__active_tab': '',
        'op': 'Save',
    }).raise_for_status()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', default=False)
    parser.add_argument('user')
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    s = requests.Session()
    login(s, args.user, getpass.getpass())
    for r in RESERVATIONS:
        make_reservation(s, r)

    return 0


if __name__ == '__main__':
    sys.exit(main())
