from stagecraft.apps.datasets.models import DataGroup, DataSet, DataType


class DataSetMassUpdate(object):

    @classmethod
    def update_bearer_token_for_data_type_or_group_name(cls, query, new_token):
        return cls(query).update(bearer_token=new_token)

    def __init__(self, query_dict):
        self.model_filter = DataSet.objects

        if 'data_type' in query_dict:
            data_type = self._get_model_instance_by_name(
                DataType, query_dict['data_type'])
            self.model_filter = self.model_filter.filter(data_type=data_type)
        if 'data_group' in query_dict:
            data_group = self._get_model_instance_by_name(
                DataGroup, query_dict['data_group'])
            self.model_filter = self.model_filter.filter(data_group=data_group)

    def update(self, **kwargs):
        return self.model_filter.update(**kwargs)

    def _get_model_instance_by_name(self, model, name):
        return model.objects.get(name=name)
