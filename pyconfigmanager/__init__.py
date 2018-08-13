from pyconfigmanager import utils
from .config import Config
import os
from . import logging


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


DEFAULT_SCHEMA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "schema.yaml")


def getschema(filenames=[DEFAULT_SCHEMA_FILE], category="schema",
              excludes=[]):
    result = {}
    for _, item in enumerate(utils.load_config(filename=filenames)):
        item = utils.get_item_by_category(
            item, category=category, excludes=excludes)
        result.update(item)

    return result
