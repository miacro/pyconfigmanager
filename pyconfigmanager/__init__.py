from pyconfigmanager import utils
from .config import Config
import os
from . import logging


def getconfig(schema=[], values=[], **kwargs):
    def normalizedict(data):
        for item in data:
            if isinstance(item, str):
                for _, entry in enumerate(utils.load_config(item)):
                    yield entry
            else:
                yield item
    if (not isinstance(schema, list)) and (not isinstance(schema, tuple)):
        schema = [schema]
    if (not isinstance(values, list)) and (not isinstance(values, tuple)):
        values = [values]
    config = Config()
    for item in normalizedict(schema):
        config.update_schema(
            schema=utils.pickitems(item, **kwargs), merge=True)
    for item in normalizedict(values):
        config.update_values(values=utils.pickitems(item, **kwargs))
    return config


def loadvalues(filename, pickname="", excludes=[]):
    result = {}
    for _, item in enumerate(utils.load_config(filename=filename)):
        item = utils.pickitems(item, pickname=pickname, excludes=excludes)
        result.update(item)
    return result


DEFAULT_SCHEMA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "schema.yaml")


def getschema(filename=[DEFAULT_SCHEMA_FILE], pickname="schema", excludes=[]):
    return loadvalues(filename=filename, pickname=pickname, excludes=excludes)
