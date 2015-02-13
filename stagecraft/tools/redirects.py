import csv
import requests

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
    with open('redirects.csv', 'w') as csvfile:
        writer = csv.writer(csvfile)
        for row in list_of_lists:
            writer.writerow(row)
