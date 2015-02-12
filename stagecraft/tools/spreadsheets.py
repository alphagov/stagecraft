import gspread


def parse_tx_row(row):
    """
    >>> parsed_row = parse_tx_row(['thIs', 'that', 'foo', 'Bar'])
    >>> department = parsed_row['department']
    >>> department == {'abbr': 'thIs', 'name': 'that', 'slug': 'this'}
    True
    >>> agency = parsed_row['agency']
    >>> agency == {'abbr': 'Bar', 'name': 'foo', 'slug': 'bar'}
    True
    """
    agency = {
        'abbr': row[3],
        'slug': row[3].lower(),
        'name': row[2],
    }
    department = {
        'abbr': row[0],
        'slug': row[0].lower(),
        'name': row[1],
    }

    if(agency['abbr'] == department['abbr']
       or agency['name'] == department['name']):
        agency = None

    return {
        'department': department,
        'agency': agency,
    }


def parse_names_row(row):
    """
    >>> names_row = ['', '', '', '', '', '', 'thIs', 'that', 'foo', 'Bar']
    >>> result = parse_names_row(names_row)
    >>> result == {'name':'thIs','service':{'name':'','slug':''},'slug':'hat'}
    True
    """
    return {
        'name': row[6],
        'slug': row[7][1:],  # chop off leading slash
        'service': {
            'name': row[4],
            'slug': row[5][1:],  # chop off leading slash
        }
    }


def _parse_rows(worksheet, parse_fn, slug_col_num):
    return {r[slug_col_num]: parse_fn(r)
            for r in worksheet.get_all_values()[1:]}


def merge(tx, names):
    merged = []

    for tx_id, tx_datum in tx.items():
        try:
            names_datum = names[tx_id]
            merged.append(
                dict(list(tx_datum.items()) +
                     list(names_datum.items()) +
                     [('tx_id', tx_id)]))
        except KeyError:
            print('failed to find name info for {}'.format(tx_id))

    return merged


def load(username, password):
    account = gspread.login(username, password)

    tx_worksheet = account.open_by_key(
        '0AiLXeWvTKFmBdFpxdEdHUWJCYnVMS0lnUHJDelFVc0E').worksheet('TX_Data')
    names_worksheet = account.open_by_key(
        '1jwJBNgKCOn5PN_rC2VDK9iwBSaP0s7KrUjQY_Hpj-V8').worksheet('Sheet1')

    tx_data = _parse_rows(tx_worksheet, parse_tx_row, 6)
    names_data = _parse_rows(names_worksheet, parse_names_row, 16)

    return merge(tx_data, names_data)
