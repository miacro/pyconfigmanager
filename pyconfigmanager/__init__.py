from pyconfigmanager import utils
from .config import Config


def get_config(schema=[], values=[], **kwargs):
    if (not isinstance(schema, list)) and (not isinstance(schema, tuple)):
        schema = [schema]
    if (not isinstance(values, list)) and (not isinstance(values, tuple)):
        values = [values]
    config = Config()
    for item in normalize_dict(schema):
        config.update_schema(
            schema=utils.get_item_by_category(item, **kwargs), merge=True)
    for item in normalize_dict(values):
        config.update_values(values=utils.get_item_by_category(item, **kwargs))
    return config


def normalize_dict(data):
    for item in data:
        if isinstance(item, str):
            for _, entry in enumerate(utils.load_config(item)):
                yield entry
        else:
            yield item
