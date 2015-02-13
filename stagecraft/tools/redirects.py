import csv
import requests

columns = ['source', 'destination']
txUrl = '/performance/transactions-explorer/service-details/'
spotlightUrl = '/performance/'


def generate(transactions):
    list_of_rows = [columns]
    for transaction in transactions:
        transaction_url = txUrl + transaction['tx_id']
        new_spotlight_transaction_url = "{}{}/{}".format(
            spotlightUrl,
            transaction['service']['slug'],
            transaction['slug'])
        if redirect_page(transaction_url):
            list_of_rows.append(
                [transaction_url, new_spotlight_transaction_url])
    return list_of_rows


def redirect_page(existing_url):
    """returns False is current page is not 200"""
    print 'calling with ' + 'https://gov.uk' + existing_url
    response = requests.get('https://gov.uk' + existing_url)
    return response.status_code == 200
    return True


def write(list_of_lists):
    with open('redirects.csv', 'wb') as csvfile:
        writer = csv.writer(csvfile)
        for row in list_of_lists:
            writer.writerow(row)
