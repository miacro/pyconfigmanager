from pyconfigmanager import utils
from .config import Config


def getconfig(schema=[], values=[], **kwargs):
    if (not isinstance(schema, list)) and (not isinstance(schema, tuple)):
        schema = [schema]
    if (not isinstance(values, list)) and (not isinstance(values, tuple)):
        values = [values]
    config = Config()
    for item in normalizedict(schema):
        config.update_schema(
            schema=utils.get_item_by_category(item, **kwargs), merge=True)
    for item in normalizedict(values):
        config.update_values(values=utils.get_item_by_category(item, **kwargs))
    return config


def normalizedict(data):
    for item in data:
        if isinstance(item, str):
            for _, entry in enumerate(utils.load_config(item)):
                yield entry
        else:
            yield item
