from pydoc import locate


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
    type = locate(name)
    if type is None:
        raise NameError("type '{}' can not be located".format(name))
    return type
