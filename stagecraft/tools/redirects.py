import argparse
import sys
import csv
import requests
from stagecraft.tools import get_credentials_or_die

from stagecraft.tools.spreadsheets import SpreadsheetMunger

columns = ['Source', 'Destination']
tx_url = '/performance/transactions-explorer/service-details/'
spotlight_url = '/performance/'


def generate(transactions, new_slugs=True):
    list_of_rows = []
    for transaction in transactions:
        transaction_url = tx_url + transaction['tx_id']
        try:
            if new_slugs:
                new_spotlight_transaction_url = "{}{}/{}".format(
                    spotlight_url,
                    transaction['service']['slug'],
                    transaction['slug'])
            else:
                new_spotlight_transaction_url = "{}{}".format(
                    spotlight_url,
                    transaction['tx_id'])
            if redirect_page(transaction_url, new_spotlight_transaction_url):
                list_of_rows.append(
                    [transaction_url, new_spotlight_transaction_url])
        except KeyError:
            print("Not enough information to generate redirect for {}".format(
                transaction['tx_id']))
    return [columns] + sorted(list_of_rows, key=lambda row: row[0])


def redirect_page(source_url, destination_url):
    """returns False is current page is not 200"""

    def _check_redirect(full_url):
        print('Getting ' + full_url)
        response = requests.get(full_url, allow_redirects=False)
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
    full_source_url = 'https://www.gov.uk' + source_url
    full_destination_url = 'https://www.gov.uk' + destination_url
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
    client_email, private_key = get_credentials_or_die()

    parser = argparse.ArgumentParser()
    parser.add_argument("--new_slugs",
                        help="Generate redirects to new style slugs. "
                             "Will fail if these are not yet supported",
                        action="store_true")
    args = parser.parse_args()

    new_slugs = False
    if args.new_slugs:
        new_slugs = True

    munger = SpreadsheetMunger({
        'names_transaction_name': 11,
        'names_transaction_slug': 12,
        'names_service_name': 9,
        'names_service_slug': 10,
        'names_tx_id': 19,
        'names_other_notes': 17,
        'names_description': 8
    })
    results = munger.load(client_email, private_key)
    list_of_rows = generate(results, new_slugs)
    write(list_of_rows)
