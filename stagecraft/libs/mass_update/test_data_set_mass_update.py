from stagecraft.apps.datasets.models import DataGroup, DataSet, DataType
from django.test import TestCase
from stagecraft.libs.mass_update import DataSetMassUpdate
from nose.tools import assert_equal


class TestDataSetMassUpdate(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data_group1 = DataGroup.objects.create(name='datagroup1')
        cls.data_group2 = DataGroup.objects.create(name='datagroup2')
        cls.data_type1 = DataType.objects.create(name='datatype1')
        cls.data_type2 = DataType.objects.create(name='datatype2')

        cls.dataset_a = DataSet.objects.create(
            name='foo',
            data_group=cls.data_group1,
            bearer_token="abc123",
            data_type=cls.data_type1)

        cls.dataset_b = DataSet.objects.create(
            name='bar',
            data_group=cls.data_group2,
            bearer_token="def456",
            data_type=cls.data_type1)

        cls.dataset_c = DataSet.objects.create(
            name='baz',
            data_group=cls.data_group2,
            bearer_token="999999",
            data_type=cls.data_type2)

    def test_update_bearer_token_by_date_type(self):

        new_bearer_token = "ghi789"

        query = {u'data_type': self.data_type1.name}
        number_updated = DataSetMassUpdate \
            .update_bearer_token_for_data_type_or_group_name(
                query, new_bearer_token)

        dataset_a = DataSet.objects.get(id=self.dataset_a.id)
        dataset_b = DataSet.objects.get(id=self.dataset_b.id)
        dataset_c = DataSet.objects.get(id=self.dataset_c.id)

        assert_equal(number_updated, 2)
        assert_equal(dataset_a.bearer_token, new_bearer_token)
        assert_equal(dataset_b.bearer_token, new_bearer_token)
        assert_equal(dataset_c.bearer_token == new_bearer_token, False)

    def test_update_bearer_token_by_data_group(self):

        new_bearer_token = "ghi789"

        query = {u'data_group': self.data_group2.name}
        number_updated = DataSetMassUpdate \
            .update_bearer_token_for_data_type_or_group_name(
                query, new_bearer_token)

        dataset_a = DataSet.objects.get(id=self.dataset_a.id)
        dataset_b = DataSet.objects.get(id=self.dataset_b.id)
        dataset_c = DataSet.objects.get(id=self.dataset_c.id)

        assert_equal(number_updated, 2)
        assert_equal(dataset_a.bearer_token == new_bearer_token, False)
        assert_equal(dataset_b.bearer_token, new_bearer_token)
        assert_equal(dataset_c.bearer_token, new_bearer_token)

    def test_update_bearer_token_by_data_group_and_data_type(self):

        new_bearer_token = "ghi789"

        query = {
            u'data_type': self.data_type1.name,
            u'data_group': self.data_group2.name}
        number_updated = DataSetMassUpdate \
            .update_bearer_token_for_data_type_or_group_name(
                query, new_bearer_token)

        dataset_a = DataSet.objects.get(id=self.dataset_a.id)
        dataset_b = DataSet.objects.get(id=self.dataset_b.id)
        dataset_c = DataSet.objects.get(id=self.dataset_c.id)

        assert_equal(number_updated, 1)
        assert_equal(dataset_a.bearer_token == new_bearer_token, False)
        assert_equal(dataset_b.bearer_token, new_bearer_token)
        assert_equal(dataset_c.bearer_token == new_bearer_token, False)
