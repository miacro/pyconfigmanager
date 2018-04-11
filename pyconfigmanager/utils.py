from pydoc import locate
import logging


def get_item_by_catrgory(item, category="", exclude_categories=["metadata"]):
    result = {}
    result.update(item)
    if category:
        result = result[category]
    if not exclude_categories:
        return result
    for exclude_category in exclude_categories:
        if exclude_category in result:
            del result[exclude_category]
    return result


def typename(type_instance):
    assert isinstance(type_instance, type), ("not an instance of 'type'")
    if type_instance.__module__ == "builtins":
        return type_instance.__name__
    return "{}.{}".format(type_instance.__module__, type_instance.__name__)


def locate_type(name):
    if name == "module":
        name = "types.ModuleType"
    type = locate(name)
    if type is None:
        raise NameError("type '{}' can not be located".format(name))
    return type


def convert_type(value, value_type):
    if not isinstance(value_type, type):
        value_type = locate_type(value_type)
    if isinstance(value, value_type):
        return value
    try:
        value = value_type(value)
    except ValueError as error:
        logging.warning(
            "convert '{}' to type '{}' failed, set to 'None', ValueError: {}".
            format(value, value_type.__name__, error))
        value = None
    finally:
        return value
