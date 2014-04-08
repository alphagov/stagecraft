from stagecraft.apps.datasets.models import DataGroup, DataSet, DataType


class DataSetMassUpdate():
    @classmethod
    def update_bearer_token_for_data_type_or_group_name(cls, query, new_token):
        model_filter = DataSet.objects
        if 'data_type' in query:
            data_type = cls._get_model_instance_by_name(
                DataType, query['data_type'])
            model_filter = model_filter.filter(data_type=data_type)
        if 'data_group' in query:
            data_group = cls._get_model_instance_by_name(
                DataGroup, query['data_group'])
            model_filter = model_filter.filter(data_group=data_group)

        model_filter.update(bearer_token=new_token)

    @classmethod
    def _get_model_instance_by_name(cls, model, name):
        return model.objects.get(name=name)
