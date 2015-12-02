import pickle
import string

import gspread
from oauth2client.client import SignedJwtAssertionCredentials


REPLACE_TABLE = {
    u'\u2013': '-',
    u'\u2018': '\'',
    u'\u2019': '\'',
    u'\u201c': '"',
    u'\u201d': '"',
}


class SpreadsheetMunger:

    def __init__(self, positions={}):
        # The transaction explorer spreadsheet is less likely
        # to change so we can set defaults for these positions.
        # The comments on these are the column names for the positions
        # on 09/06/2015
        # "Name of service",
        self.tx_name = positions.get('tx_name', 4)
        # "Description 1",
        self.tx_desc1 = positions.get('tx_desc1', 69)
        # "Description 2",
        self.tx_desc2 = positions.get('tx_desc2', 70)
        # "Agency abbr",
        self.tx_agency_abbr = positions.get('tx_agency_abbr', 3)
        # "Agency/body",
        self.tx_agency_name = positions.get('tx_agency_name', 2)
        # "Abbr",
        self.tx_department_abbr = positions.get('tx_department_abbr', 0)
        # "Department",
        self.tx_department_name = positions.get('tx_department_name', 1)
        # "High-volume?",
        self.tx_high_volume = positions.get('tx_high_volume', 77)
        # "Notes on costs",
        self.tx_costs = positions.get('tx_costs', 72)
        # "Other notes",
        self.tx_other_notes = positions.get('tx_other_notes', 73)
        # "Slug",
        self.tx_tx_id_column = positions.get('tx_tx_id_column', 6)
        # "Customer type",
        self.tx_customer_type = positions.get('tx_customer_type', 74)
        # "Business model",
        self.tx_business_model = positions.get('tx_business_model', 75)

        # "Proposed new summary",
        self.names_description = positions['names_description']
        # "Proposed name (of page e.g. carers allowance applications not apply
        # for carers allowance)",
        self.names_transaction_name = positions['names_transaction_name']
        # "Proposed URL2 (name of transaction) e.g. /applications",
        self.names_transaction_slug = positions['names_transaction_slug']
        # "Proposed name of overview page",
        self.names_service_name = positions['names_service_name']
        # "Proposed URL1 (name of service) e.g. /carers-allowance",
        self.names_service_slug = positions['names_service_slug']
        # "Other notes",
        self.names_other_notes = positions['names_other_notes']
        # "Slug [do not edit]"
        self.names_tx_id = positions['names_tx_id']

    def _replace_unicode(self, s):
        for k, v in REPLACE_TABLE.items():
            s = string.replace(s, k, v)
        return s

    def _parse_tx_row(self, row):
        record = {}
        record['tx_id'] = row[self.tx_tx_id_column]
        if row[self.tx_name]:
            record['name'] = row[self.tx_name]
        if row[self.tx_desc1]:
            record['description'] = row[self.tx_desc1]
        if row[self.tx_desc2]:
            record['description_extra'] = row[self.tx_desc2]
        if row[self.tx_costs]:
            record['costs'] = row[self.tx_costs]
        if row[self.tx_other_notes]:
            record['other_notes'] = row[self.tx_other_notes]
        if row[self.tx_customer_type]:
            record['customer_type'] = row[self.tx_customer_type]
        if row[self.tx_business_model]:
            record['business_model'] = row[self.tx_business_model]
        if row[self.tx_department_abbr] \
                and row[self.tx_department_name]:
            record['department'] = {
                'abbr': row[self.tx_department_abbr],
                'slug': row[self.tx_department_abbr].lower(),
                'name': row[self.tx_department_name],
            }

        if row[self.tx_agency_name]:
            agency = {
                'name': row[self.tx_agency_name]
            }
            if row[self.tx_agency_abbr]:
                agency['abbr'] = row[self.tx_agency_abbr]
                agency['slug'] = row[self.tx_agency_abbr].lower()
            else:
                agency['abbr'] = row[self.tx_agency_name]
                agency['slug'] = \
                    row[self.tx_agency_name].lower().replace(' ', '-')

            if(agency['abbr'] != record['department']['abbr']
                    or agency['name'] != record['department']['name']):
                record['agency'] = agency

        high_volume = False
        if row[self.tx_high_volume] == 'yes':
            high_volume = True
        record['high_volume'] = high_volume
        return record

    def _parse_names_row(self, row):
        record = {}
        record['tx_id'] = row[self.names_tx_id]

        # If a record does not have a transaction, the service name/slug is
        # used.
        if row[self.names_transaction_name] and \
                row[self.names_transaction_slug]:
            record['name'] = row[self.names_transaction_name]
            record['slug'] = row[self.names_transaction_slug][1:]
            record['transaction'] = {
                'name': row[self.names_transaction_name],
                'slug': row[self.names_transaction_slug][1:],
            }

        if row[self.names_service_name] and \
                row[self.names_service_slug]:
            record['service'] = {
                'name': row[self.names_service_name],
                'slug': row[self.names_service_slug][1:]
            }
            if not record.get('name'):
                record['name'] = row[self.names_service_name]
                record['slug'] = row[self.names_service_slug][1:]

        if row[self.names_description]:
            record['description'] = row[self.names_description]
        if row[self.names_other_notes]:
            record['other_notes'] = row[self.names_other_notes]

        return record

    def _parse_rows(self, worksheet, parse_fn, tx_id_column):
        return {r[tx_id_column]: parse_fn(r)
                for r in worksheet.get_all_values()[1:]}

    def load_tx_worksheet(self, account):
        all_values = account.open_by_key(
            '1DN98HNFtOv6POsQt501dnFiZ4Hus6Uj1IrerhDx1Guk') \
            .worksheet('TX_Data').get_all_values()
        rows = []
        for row in all_values[1:]:
            rows.append(self._parse_tx_row(row))
        return rows

    def load_names_worksheet(self, account):
        all_values = account.open_by_key(
            '1jwJBNgKCOn5PN_rC2VDK9iwBSaP0s7KrUjQY_Hpj-V8')\
            .worksheet('Sheet1').get_all_values()
        rows = []
        for row in all_values[1:]:
            parsed = self._parse_names_row(row)
            if parsed is not None:
                rows.append(parsed)
        return rows

    def merge(self, tx, names):
        # Records are supplied as rows, so convert to dict keyed by tx_id.
        tx_dict = {}
        for record in tx:
            tx_dict[record['tx_id']] = record
        names_dict = {}
        for record in names:
            names_dict[record['tx_id']] = record

        merged = []
        unmerged = []
        for tx_id, tx_datum in tx_dict.items():
            try:
                names_datum = names_dict[tx_id]
                merged.append(
                    dict(list(tx_datum.items()) +
                         list(names_datum.items()) +
                         [('tx_id', tx_id)]))
            except KeyError:
                unmerged.append(tx_id)
        if unmerged:
            print("There were unmerged records:")
            for record in unmerged:
                print(record)
        return merged

    def sanitise_record(self, record):

        if record.get('name'):
            name = self._replace_unicode(record['name'])
            if len(name) > 256:
                name = name[:256]
            record['name'] = name

        if record.get('description'):
            description = self._replace_unicode(record['description'])
            if len(description) > 500:
                description = description[:500]
            record['description'] = description

        if record.get('description_extra'):
            description_extra = self._replace_unicode(
                record['description_extra'])
            if len(description_extra) > 400:
                description_extra = description_extra[:400]
            record['description_extra'] = description_extra

        if record.get('costs'):
            costs = self._replace_unicode(record['costs'])
            if len(costs) > 1500:
                costs = costs[:1500]
            record['costs'] = costs

        if record.get('other_notes'):
            other_notes = self._replace_unicode(record['other_notes'])
            if len(other_notes) > 1000:
                other_notes = other_notes[:1000]
            record['other_notes'] = other_notes

        if record.get('customer_type'):
            customer_type = self._replace_unicode(record['customer_type'])
            if len(customer_type) > 30:
                customer_type = customer_type[:30]
            record['customer_type'] = customer_type

        if record.get('business_model'):
            business_model = self._replace_unicode(record['business_model'])
            if len(business_model) > 31:
                business_model = business_model[:31]
            record['business_model'] = business_model

        if record.get('tx_id'):
            tx_id = self._replace_unicode(record['tx_id'])
            if len(tx_id) > 90:
                print('Truncated slug: {} to {}'.format(tx_id, tx_id[:90]))
                record['tx_truncated'] = tx_id[:90]
            record['tx_id'] = tx_id

    def load(self, client_email, private_key):
        scope = ['https://spreadsheets.google.com/feeds']
        credentials = SignedJwtAssertionCredentials(
            client_email, private_key, scope)

        account = gspread.authorize(credentials)

        try:
            with open('tx_values.pickle', 'rb') as pickled:
                tx = pickle.load(pickled)
        except IOError:
            tx = self.load_tx_worksheet(account)
            with open('tx_values.pickle', 'wb') as pickled:
                pickle.dump(tx, pickled, pickle.HIGHEST_PROTOCOL)

        try:
            with open('names_values.pickle', 'rb') as pickled:
                names = pickle.load(pickled)
        except IOError:
            names = self.load_names_worksheet(account)
            with open('names_values.pickle', 'wb') as pickled:
                pickle.dump(names, pickled, pickle.HIGHEST_PROTOCOL)

        return self.merge(tx, names)
