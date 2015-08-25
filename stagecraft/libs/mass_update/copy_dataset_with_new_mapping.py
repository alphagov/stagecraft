import reversion
from performanceplatform.client import DataSet as client
from stagecraft.apps.datasets.models import DataGroup, DataSet, DataType
from django.conf import settings

INTERNAL_KEY = [
    "_day_start_at",
    "_hour_start_at",
    "_week_start_at",
    "_month_start_at",
    "_quarter_start_at",
    "_updated_at"]


# should pass in whole mapping?
@reversion.create_revision()
def migrate_data_set(old_attributes, changed_attributes, data_mapping):
    print("getting existing dataset")
    existing_data_set = get_existing_data_set(old_attributes['data_group'],
                                              old_attributes['data_type'])
    if not existing_data_set:
        print("no existing dataset found, skipping")
        return False
    new_data_set_attributes = get_new_attributes(
        serialize_for_update(existing_data_set), changed_attributes)
    print("got new attributes {}".format(new_data_set_attributes))
    print("creating new dataset with attributes")
    new_data_set = get_or_create_new_data_set(new_data_set_attributes)
    print("getting old data")
    old_data = get_old_data(old_attributes['data_group'],
                            old_attributes['data_type'])
    print("converting old data")
    new_data = convert_old_data(old_data, data_mapping)
    serialized_new_data_set = new_data_set.serialize()
    print("posting data {} to dataset {}".format(new_data,
                                                 serialized_new_data_set))
    post_new_data(serialized_new_data_set['data_group'],
                  serialized_new_data_set['data_type'],
                  serialized_new_data_set['bearer_token'],
                  new_data)


def serialize_for_update(data_set):
    serialized_data_set = data_set.serialize()
    serialized_data_set['auto_ids'] = data_set.auto_ids
    serialized_data_set['upload_filters'] = data_set.upload_filters
    return serialized_data_set


def get_existing_data_set(data_group_name, data_type_name):
    data_type = DataType.objects.filter(
        name=data_type_name).first()
    data_group = DataGroup.objects.filter(
        name=data_group_name).first()
    if not data_group or not data_type:
        return None
    return DataSet.objects.filter(data_type=data_type,
                                  data_group=data_group).first()


def get_new_attributes(existing_attributes, changed_attributes):
    """
    >>> existing_attributes = {'a': 1, 'b': 2, 'c': 3}
    >>> changed_attributes = {'a': 6, 'c': 'x,y'}
    >>> get_new_attributes(existing_attributes,changed_attributes) \
        == {'b': 2, 'c': 'x,y', 'a': 6}
    True
    """
    new_attributes = existing_attributes.copy()
    new_attributes.update(changed_attributes)
    return new_attributes


def get_or_create_new_data_set(new_attributes):
    (data_type, new) = DataType.objects.get_or_create(
        name=new_attributes.pop('data_type'))
    (data_group, new) = DataGroup.objects.get_or_create(
        name=new_attributes.pop('data_group'))
    (obj, new) = DataSet.objects.get_or_create(
        data_type=data_type, data_group=data_group)
    new_attributes['data_type'] = data_type
    new_attributes['data_group'] = data_group
    del new_attributes['schema']
    del new_attributes['name']
    data_set_to_update_queryset = DataSet.objects.filter(name=obj.name)
    data_set_to_update_queryset.update(**new_attributes)
    return data_set_to_update_queryset.first()


def get_qualified_backdrop_url():
    return settings.BACKDROP_WRITE_URL + '/data'


def get_old_data(data_group_name, data_type_name):
    data_set_client = client.from_group_and_type(get_qualified_backdrop_url(),
                                                 data_group_name,
                                                 data_type_name)
    return data_set_client.get().json()['data']


def apply_new_key_mappings(document, key_mapping):
    for key, val in document.items():
        if key in key_mapping:
            document.pop(key)
            document[key_mapping[key]] = val
        elif key in INTERNAL_KEY:
            del document[key]
        else:
            document[key] = val
    return document


def apply_new_values(document, value_mapping):
    # we need to convert counts to i - they are floats currently
    for key, val in document.items():
        if val in value_mapping:
            document[key] = value_mapping[val]
        if key == 'count':
            document[key] = int(val)
    return document


def convert_old_data(old_data, data_mapping):
    new_data = []
    key_mapping = data_mapping['key_mapping']
    value_mapping = data_mapping['value_mapping']
    for document in old_data:
        doc = apply_new_values(
            apply_new_key_mappings(document, key_mapping), value_mapping)
        new_data.append(doc)

    return new_data


def post_new_data(data_group_name, data_type_name, bearer_token, data):
    data_set_client = client.from_group_and_type(get_qualified_backdrop_url(),
                                                 data_group_name,
                                                 data_type_name,
                                                 token=bearer_token)
    return data_set_client.post(data)
