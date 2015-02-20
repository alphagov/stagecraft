import pickle
import string

import gspread


REPLACE_TABLE = {
    u'\u2013': '-',
    u'\u2018': '\'',
    u'\u2019': '\'',
}


class SpreadsheetMunger:

    def __init__(self, positions={}):
        # The transaction explorer spreadsheet is less likely to change.
        # As a result we can assume these positions.
        self.tx_name = positions.get('tx_name', 4)
        self.tx_desc1 = positions.get('tx_desc1', 65)
        self.tx_desc2 = positions.get('tx_desc2', 66)
        self.tx_agency_abbr = positions.get('tx_agency_abbr', 3)
        self.tx_agency_name = positions.get('tx_agency_name', 2)
        self.tx_department_abbr = positions.get('tx_department_abbr', 0)
        self.tx_department_name = positions.get('tx_department_name', 1)
        self.tx_high_volume = positions.get('tx_high_volume', 74)
        self.tx_costs = positions.get('tx_costs', 68)
        self.tx_other_notes = positions.get('tx_other_notes', 69)

        self.tx_tx_id_column = positions.get('tx_tx_id_column', 6)

        self.names_name = positions['names_name']
        self.names_slug = positions['names_slug']
        self.names_service_name = positions['names_service_name']
        self.names_service_slug = positions['names_service_slug']

        self.names_tx_id_column = positions['names_tx_id_column']

    def _replace_unicode(self, s):
        for k, v in REPLACE_TABLE.items():
            s = string.replace(s, k, v)
        return s

    def _parse_tx_row(self, row):
        name = self._replace_unicode(row[self.tx_name])
        if len(name) > 80:
            name = name[:80]

        description = self._replace_unicode(row[self.tx_desc1])
        if len(description) > 500:
            description = description[:500]

        description_extra = self._replace_unicode(row[self.tx_desc2])
        if len(description_extra) > 400:
            description_extra = description_extra[:400]

        costs = self._replace_unicode(row[self.tx_costs])
        if len(costs) > 1500:
            costs = costs[:1500]

        other_notes = self._replace_unicode(row[self.tx_other_notes])
        if len(other_notes) > 1000:
            other_notes = other_notes[:1000]

        slug = row[self.tx_tx_id_column]
        if len(slug) > 90:
            slug = slug[:90]

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

        high_volume = False
        if row[self.tx_high_volume] == 'yes':
            high_volume = True

        return {
            'name': name,
            'description': description,
            'description_extra': description_extra,
            'slug': slug,
            'department': department,
            'agency': agency,
            'high_volume': high_volume,
            'costs': costs,
            'other_notes': other_notes,
        }

    def _parse_names_row(self, row):
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
                print(
                    'Failed to find names spreadsheet record for {}'\
                            .format(tx_id))

        return merged

    def load_tx_worksheet(self, username, password):
        account = gspread.login(username, password)

        try:
            with open('tx_worksheet.pickle', 'rb') as pickled:
                all_values = pickle.load(pickled)
        except IOError:
            tx_worksheet = account.open_by_key(
                '0AiLXeWvTKFmBdFpxdEdHUWJCYnVMS0lnUHJDelFVc0E')\
                        .worksheet('TX_Data')
            all_values = tx_worksheet.get_all_values()

            with open('tx_worksheet.pickle', 'wb') as pickled:
                pickle.dump(all_values, pickled, pickle.HIGHEST_PROTOCOL)

        rows = []
        for row in all_values[1:]:
            rows.append(self._parse_tx_row(row))
        return rows

    def load_names_worksheet(self, username, password):
        account = gspread.login(username, password)

        try:
            with open('names_worksheet.pickle', 'rb') as pickled:
                all_values = pickle.load(pickled)
        except IOError:
            tx_worksheet = account.open_by_key(
                '1jwJBNgKCOn5PN_rC2VDK9iwBSaP0s7KrUjQY_Hpj-V8')\
                        .worksheet('Sheet1')
            all_values = tx_worksheet.get_all_values()

            with open('names_worksheet.pickle', 'wb') as pickled:
                pickle.dump(all_values, pickled, pickle.HIGHEST_PROTOCOL)

        rows = []
        for row in all_values[1:]:
            rows.append(self._parse_names_row(row))
        return rows


    def load(self, username, password):
        tx = self.load_tx_worksheet(username, password)
        names = self.load_names_worksheet(username, password)
        return self._merge(tx, names)
