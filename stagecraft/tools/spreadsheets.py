import logging
import pickle
import string

import gspread


log = logging.getLogger(__name__)
log.setLevel(logging.ERROR)
handler = logging.StreamHandler()
handler.setLevel(logging.ERROR)
log.addHandler(handler)


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
        self.tx_customer_type = positions.get('tx_customer_type', 70)
        self.tx_business_model = positions.get('tx_business_model', 71)

        self.names_description = positions['names_description']
        self.names_transaction_name = positions['names_transaction_name']
        self.names_transaction_slug = positions['names_transaction_slug']
        self.names_service_name = positions['names_service_name']
        self.names_service_slug = positions['names_service_slug']
        self.names_notes = positions['names_notes']
        self.names_other_notes = positions['names_other_notes']
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
        if row[self.tx_agency_abbr] \
                and row[self.tx_agency_name]:
            agency = {
                'abbr': row[self.tx_agency_abbr],
                'slug': row[self.tx_agency_abbr].lower(),
                'name': row[self.tx_agency_name],
            }
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

        if row[self.names_transaction_name]:
            record['name'] = row[self.names_transaction_name]
        elif row[self.names_service_name]:
            record['name'] = row[self.names_service_name]
        else:
            log.error('Missing name for {}'.format(row[self.names_tx_id]))
            return None

        if row[self.names_transaction_slug]:
            record['slug'] = row[self.names_transaction_slug][1:]
        elif row[self.names_service_slug]:
            record['slug'] = row[self.names_service_slug]
        else:
            log.error('Missing slug for {}'.format(row[self.names_tx_id]))
            return None

        if row[self.names_description]:
            record['description'] = row[self.names_description]
        # description-extra is not present in the names spreadsheet
        if row[self.names_notes]:
            record['costs'] = row[self.names_notes]
        if row[self.names_other_notes]:
            record['other_notes'] = row[self.names_other_notes]
        if row[self.names_service_name] and \
                row[self.names_service_slug]:
            record['service'] = {
                'name': row[self.names_service_name],
                'slug': row[self.names_service_slug][1:]
            }
        if row[self.names_transaction_name] and \
                row[self.names_transaction_slug]:
            record['transaction'] = {
                'name': row[self.names_transaction_name],
                'slug': row[self.names_transaction_slug][1:],
            }
        return record

    def _parse_rows(self, worksheet, parse_fn, tx_id_column):
        return {r[tx_id_column]: parse_fn(r)
                for r in worksheet.get_all_values()[1:]}

    def load_tx_worksheet(self, account):
        all_values = account.open_by_key(
            '0AiLXeWvTKFmBdFpxdEdHUWJCYnVMS0lnUHJDelFVc0E') \
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
            rows.append(self._parse_names_row(row))
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
            log.error("There were unmerged records: {}".format(unmerged))
        return merged

    def sanitise_record(self, record):

        if record.get('name'):
            name = self._replace_unicode(record['name'])
            if len(name) > 80:
                name = name[:80]
            record['name'] = name

        if record.get('description'):
            description = self._replace_unicode(record['description'])
            if len(description) > 500:
                description = description[:500]
            record['description'] = description

        if record.get('description_extra'):
            description_extra = self._replace_unicode(record['description_extra'])
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
            if len(customer_type) > 20:
                customer_type = customer_type[:20]
            record['customer_type'] = customer_type

        if record.get('business_model'):
            business_model = self._replace_unicode(record['business_model'])
            if len(business_model) > 31:
                business_model = business_model[:31]
            record['business_model'] = business_model

        if record.get('tx_id'):
            tx_id = self._replace_unicode(record['tx_id'])
            if len(tx_id) > 90:
                log.warn('Truncated slug: {} to {}'.format(tx_id, tx_id[:90]))
                tx_id = tx_id[:90]
            record['tx_id'] = tx_id

    def load(self, username, password):
        account = gspread.login(username, password)

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
