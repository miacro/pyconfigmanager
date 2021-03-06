from pydoc import locate
import logging
import yaml
import os
import json as JSON


def pickitems(data, pickname="", excludes=["schema"]):
    if isinstance(pickname, str):
        names = [item for item in pickname.split(".") if item]
    elif isinstance(pickname, list):
        names = pickname
    else:
        names = []
    names = [item for item in names if item]
    result = dict(data.items())
    for name in names:
        if name in result:
            result = result[name]
        else:
            return {}
        if not isinstance(result, dict):
            return {}
    if not excludes:
        excludes = []
    return {key: value for key, value in result.items() if key not in excludes}


def typename(type_instance):
    assert isinstance(type_instance, type), ("not an instance of 'type'")
    if type_instance.__module__ == "builtins":
        return type_instance.__name__
    return "{}.{}".format(type_instance.__module__, type_instance.__name__)


def locate_type(name):
    if not name:
        return None

    if isinstance(name, type):
        return name

    if not isinstance(name, str):
        return None

    if name == "module":
        name = "types.ModuleType"
    real_type = locate(name)
    if real_type is None:
        raise NameError("type '{}' can not be located".format(name))
    return real_type


def convert_type(value, value_type):
    if not isinstance(value_type, type):
        value_type = locate_type(value_type)
    if isinstance(value, value_type):
        return value
    try:
        value = value_type(value)
    except (ValueError, TypeError) as error:
        logging.warning(
            "convert '{}' to type '{}' failed, set to 'None', {}: {}".format(
                value, value_type.__name__, error.__class__.__name__, error))
        value = None
    finally:
        return value


def load_yaml(contents=[], filenames=[]):
    def load_content(content):
        for item in yaml.load_all(content):
            if item is not None:
                yield item

    if isinstance(contents, str):
        contents = [contents]
    elif contents is None:
        contents = []

    if isinstance(filenames, str):
        filenames = [filenames]
    elif filenames is None:
        filenames = []

    for content in contents:
        for item in load_content(content):
            yield item

    for filename in filenames:
        with open(os.path.abspath(filename), "r") as stream:
            for item in load_content(stream):
                yield item


def dump_yaml(data, filename=""):
    if isinstance(data, list):
        dump = yaml.dump_all
    else:
        dump = yaml.dump
    output = dump(
        data,
        default_style="",
        canonical=False,
        indent=2,
        default_flow_style=False,
        encoding="utf-8",
        allow_unicode=True)
    if not filename:
        return output
    with open(filename, "wb") as stream:
        stream.write(output)
    return output


def load_json(contents=[], filenames=[]):
    def load_content(content):
        json = JSON.loads(content)
        if not isinstance(json, list):
            json = [json]
        for item in json:
            yield item

    if isinstance(contents, str):
        contents = [contents]
    elif contents is None:
        contents = []

    if isinstance(filenames, str):
        filenames = [filenames]
    elif filenames is None:
        filenames = []

    for content in contents:
        for item in load_content(content):
            yield item
    for filename in filenames:
        with open(os.path.expanduser(os.path.expandvars(filename)),
                  "r") as stream:
            content = stream.read()
        for item in load_content(content):
            yield item


def dump_json(json, filename=None):
    content = JSON.dumps(json, ensure_ascii=False, indent=2)
    if filename:
        with open(os.path.expanduser(os.path.expandvars(filename)),
                  "wt") as stream:
            stream.writelines(content)
    return content


def detect_filetype(filename):
    return filename[filename.rfind(".") + 1:].lower()


def load_config(filename):
    if isinstance(filename, list) or isinstance(filename, tuple):
        for filename_i in filename:
            for _, item in enumerate(load_config(filename_i)):
                yield item
    else:
        filetype = detect_filetype(filename)
        if filetype == "json":
            for item in load_json(filenames=filename):
                yield item
        elif filetype == "yaml":
            for item in load_yaml(filenames=filename):
                yield item


def dump_config(values, filename):
    filetype = detect_filetype(filename)
    if filetype == "json":
        dump_json(values, filename)
    elif filetype == "yaml":
        dump_yaml(values, filename)
