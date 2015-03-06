import os
import sys
import csv
import requests

from .spreadsheets import SpreadsheetMunger

columns = ['source', 'destination']
tx_url = '/performance/transactions-explorer/service-details/'
spotlight_url = '/performance/'


def generate(transactions):
    list_of_rows = [columns]
    for transaction in transactions:
        transaction_url = tx_url + transaction['tx_id']
        new_spotlight_transaction_url = "{}{}/{}".format(
            spotlight_url,
            transaction['service']['slug'],
            transaction['slug'])
        # should also check if there is already a redirect to the target?
        if redirect_page(transaction_url, new_spotlight_transaction_url):
            list_of_rows.append(
                [transaction_url, new_spotlight_transaction_url])
    return list_of_rows


def redirect_page(source_url, destination_url):
    """returns False is current page is not 200"""

    def _check_redirect(full_url):
        print('Getting ' + full_url)
        response = requests.get(full_url)
        if response.status_code == 200:
            print("Was 200")
            return True
        elif response.status_code == 404:
            print("Was 404")
            return False
        elif response.status_code == 301:
            print("Was 301")
            return False
        else:
            raise Exception("UNEXPECTED STATUS CODE {} FOR {}".format(
                response.status_code, full_url))
        return True
    full_source_url = 'https://gov.uk' + source_url
    full_destination_url = 'https://gov.uk' + destination_url
    return _check_redirect(full_source_url) and _check_redirect(
        full_destination_url)


def write(list_of_lists):

    def _write_csv(csvfile):
        writer = csv.writer(csvfile)
        for row in list_of_lists:
            writer.writerow(row)

    if sys.version_info >= (3, 0, 0):
        # python 3 produces different output with the newline argument
        with open('redirects.csv', 'w', newline='\r\n') as csvfile:
            _write_csv(csvfile)
    else:
        # python 2 does not support a newline argument
        with open('redirects.csv', 'w') as csvfile:
            _write_csv(csvfile)


if __name__ == '__main__':
    try:
        username = os.environ['GOOGLE_USERNAME']
        password = os.environ['GOOGLE_PASSWORD']
    except KeyError:
        print("Please supply username (GOOGLE_USERNAME)"
            "and password (GOOGLE_PASSWORD) as environment variables")
        sys.exit(1)

    munger = SpreadsheetMunger({
        'names_name': 9,
        'names_slug': 10,
        'names_service_name': 11,
        'names_service_slug': 12,
        'names_tx_id_column': 19,
    })
    results = munger.load(username, password)
    list_of_rows = generate(results)
    write(list_of_rows)