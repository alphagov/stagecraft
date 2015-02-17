import gspread


class SpreadsheetMunger:

    def __init__(self, positions={}):
        # The transaction explorer spreadsheet is less likely to change.
        # As a result we can assume these positions.
        self.tx_agency_abbr = positions.get('tx_agency_abbr', 3)
        self.tx_agency_name = positions.get('tx_agency_name', 2)
        self.tx_department_abbr = positions.get('tx_department_abbr', 0)
        self.tx_department_name = positions.get('tx_department_name', 1)

        self.tx_tx_id_column = positions.get('tx_tx_id_column', 6)

        self.names_name = positions['names_name']
        self.names_slug = positions['names_slug']
        self.names_service_name = positions['names_service_name']
        self.names_service_slug = positions['names_service_slug']

        self.names_tx_id_column = positions['names_tx_id_column']

    def _parse_tx_row(self, row):
        """
        >>> positions={
        ...     'names_name': 6,
        ...     'names_slug': 7,
        ...     'names_service_name': 4,
        ...     'names_service_slug': 5,
        ...     'names_tx_id_column': 16}
        >>> munger = SpreadsheetMunger(positions)
        >>> parsed_row = munger._parse_tx_row(['thIs', 'that', 'foo', 'Bar'])
        >>> department = parsed_row['department']
        >>> department == {'abbr': 'thIs', 'name': 'that', 'slug': 'this'}
        True
        >>> agency = parsed_row['agency']
        >>> agency == {'abbr': 'Bar', 'name': 'foo', 'slug': 'bar'}
        True
        """
        agency = {
            'abbr': row[self.tx_agency_abbr],
            'slug': row[self.tx_agency_abbr].lower(),
            'name': row[self.tx_agency_name],
        }
        department = {
            'abbr': row[self.tx_department_abbr],
            'slug': row[self.tx_department_abbr].lower(),
            'name': row[self.tx_department_name],
        }

        if(agency['abbr'] == department['abbr']
           or agency['name'] == department['name']):
            agency = None

        return {
            'department': department,
            'agency': agency,
        }

    def _parse_names_row(self, row):
        """
        >>> positions={
        ...     'names_name': 6,
        ...     'names_slug': 7,
        ...     'names_service_name': 4,
        ...     'names_service_slug': 5,
        ...     'names_tx_id_column': 16}
        >>> munger = SpreadsheetMunger(positions)
        >>> names_row = ['', '', '', '', '', '', 'thIs', 'tha', 'foo', 'Bar']
        >>> result = munger._parse_names_row(names_row)
        >>> result=={'name':'thIs','service':{'name':'','slug':''},'slug':'ha'}
        True
        """
        return {
            'name': row[self.names_name],
            'slug': row[self.names_slug][1:],  # cut leading slash
            'service': {
                'name': row[self.names_service_name],
                'slug': row[self.names_service_slug][1:],  # cut leading slash
            }
        }

    def _parse_rows(self, worksheet, parse_fn, tx_id_column):
        return {r[tx_id_column]: parse_fn(r)
                for r in worksheet.get_all_values()[1:]}

    def _merge(self, tx, names):
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

    def load(self, username, password):
        account = gspread.login(username, password)

        tx_worksheet = account.open_by_key(
            '0AiLXeWvTKFmBdFpxdEdHUWJCYnVMS0lnUHJDelFVc0E').worksheet(
                'TX_Data')
        names_worksheet = account.open_by_key(
            '1jwJBNgKCOn5PN_rC2VDK9iwBSaP0s7KrUjQY_Hpj-V8').worksheet('Sheet1')

        tx_data = self._parse_rows(
            tx_worksheet,
            self._parse_tx_row,
            self.tx_tx_id_column)
        names_data = self._parse_rows(
            names_worksheet,
            self._parse_names_row,
            self.names_tx_id_column)

        return self._merge(tx_data, names_data)
