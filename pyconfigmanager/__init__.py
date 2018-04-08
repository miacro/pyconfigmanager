import os
import argparse
import logging
from .logging_config import get_logging_level
from . import yaml
from . import utils
import sys


def get_config(metadata={}, yamls=[], metadata_files=[], **kwargs):
    config = Config(metadata=metadata)
    for _, item in enumerate(yaml.load_yaml(filenames=metadata_files)):
        item = utils.get_item_by_catrgory(item, **kwargs)
        config.update_metadata(item)
    if not (isinstance(yamls, list) or isinstance(yamls, tuple)):
        yamls = [yamls]
    if yamls:
        config.update_values_by_yaml(filenames=yamls, **kwargs)
    return config


class Config():
    def __init__(self, metadata):
        self.update_metadata(metadata)

    def __new__(self, metadata):
        normalized_metadata = self.normalize_metadata(self, metadata)
        if normalized_metadata[METADATA.TYPE] != TYPENAME.CONFIG:
            return metadata
        else:
            return super(Config, self).__new__(self)

    def __iter__(self):
        for attr_name in self._metadata:
            if attr_name != METADATA.TYPE:
                yield attr_name, getattr(self, attr_name)

    def __str__(self):
        return str(self.get_values())

    def __setattr__(self, name, value):
        return self.setattr(name, value, override_config=False)

    def __getattribute__(self, name):
        return super().__getattribute__(name)

    def __getattr__(self, name):
        if name == "_metadata":
            raise AttributeError(
                "'Config' object has no attribute '_metadata'")
        return self._metadata[name][METADATA.VALUE]

    def setattr(self, name, value, override_config=False):
        if name == "_metadata":
            return super().__setattr__(name, value)

        if isinstance(value, dict) and METADATA.TYPE in value:
            if METADATA.VALUE in value:
                value = value[METADATA.VALUE]
            else:
                value = type2value(value[METADATA.TYPE])

        if name not in self._metadata:
            raise AttributeError("%s is not attrubute" % name)
        if (not override_config) and (
                self._metadata[name][METADATA.TYPE] == TYPENAME.CONFIG):
            raise AttributeError(
                "can not update value of type %s" % TYPENAME.CONFIG)
        if self._metadata[name][METADATA.TYPE] != typestring(value):
            value = type2value(self._metadata[name][METADATA.TYPE], value)
        self._metadata[name][METADATA.VALUE] = value

    def normalize_metadata(self, metadata):
        result = {}
        if isinstance(metadata, dict):
            result.update(metadata)
            if (METADATA.TYPE in result) and (result[METADATA.TYPE] !=
                                              TYPENAME.CONFIG):
                return result
            result[METADATA.TYPE] = TYPENAME.CONFIG
        else:
            result = {
                METADATA.VALUE: metadata,
                METADATA.TYPE: typestring(metadata)
            }
        return result

    def update_metadata(self, metadata, merge=True):
        if not hasattr(self, "_metadata"):
            self._metadata = {}
        for key in metadata:
            if key == METADATA.TYPE:
                continue
            new_metadata = self.normalize_metadata(metadata[key])
            target_metadata = {}

            if not merge:
                target_metadata = new_metadata
            elif (key not in self._metadata) or (
                    self._metadata[key][METADATA.TYPE] == TYPENAME.NONE):
                target_metadata = new_metadata
            elif new_metadata[METADATA.TYPE] == TYPENAME.NONE:
                continue
            elif (new_metadata[METADATA.TYPE] != TYPENAME.CONFIG) or (
                    self._metadata[key][METADATA.TYPE] != TYPENAME.CONFIG):
                target_metadata = new_metadata
            else:
                attr = getattr(self, key)
                attr.update_metadata(metadata=new_metadata)
                continue
            if target_metadata[METADATA.TYPE] == TYPENAME.CONFIG:
                self._metadata[key] = {
                    METADATA.TYPE: target_metadata[METADATA.TYPE],
                    METADATA.VALUE: None
                }
            else:
                self._metadata[key] = target_metadata

            self.setattr(key, Config(target_metadata), override_config=True)

    def get_metadata(self):
        result = {}
        for key in self._metadata:
            if self._metadata[key][METADATA.TYPE] == TYPENAME.CONFIG:
                result[key] = getattr(self, key).get_metadata()
            else:
                result[key] = self._metadata[key]
        return result

    def get_values(self):
        result = {}
        for key in self._metadata:
            attr = getattr(self, key)
            if self._metadata[key][METADATA.TYPE] == TYPENAME.CONFIG:
                result[key] = attr.get_values()
            elif self._metadata[key][METADATA.TYPE] == TYPENAME.MODULE:
                pass
            else:
                result[key] = attr
        return result

    def argument_parser(self, parser=None, prefix=""):
        if not parser:
            parser = argparse.ArgumentParser(
                formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                description="")

        for attr_name in self._metadata:
            attr = getattr(self, attr_name)
            attr_metadata = self._metadata[attr_name]
            if isinstance(attr, Config):
                attr.argument_parser(
                    parser,
                    prefix=attr_name
                    if not prefix else prefix + "-" + attr_name)
            else:
                if (METADATA.ARGPARSE in attr_metadata) and (
                        not attr_metadata[METADATA.ARGPARSE]):
                    continue
                if ((attr_metadata[METADATA.TYPE] == TYPENAME.CONFIG)
                        or (attr_metadata[METADATA.TYPE] == TYPENAME.MODULE)):
                    continue
                if prefix:
                    arg_name = "%s-%s" % (prefix, attr_name)
                else:
                    arg_name = attr_name
                arg_name = arg_name.replace("_", "-")
                arg_type = string2type(attr_metadata[METADATA.TYPE])
                if ((METADATA.REQUIRED in attr_metadata)
                        and attr_metadata[METADATA.REQUIRED]):
                    required = True
                else:
                    required = False
                if METADATA.HELP in attr_metadata:
                    help = attr_metadata[METADATA.HELP]
                else:
                    help = " "
                if METADATA.ACTION in attr_metadata:
                    action = attr_metadata[METADATA.ACTION]
                else:
                    action = None
                if METADATA.CHOICES in attr_metadata:
                    choices = attr_metadata[METADATA.CHOICES]
                else:
                    choices = None
                if METADATA.NARGS in attr_metadata:
                    nargs = attr_metadata[METADATA.NARGS]
                    arg_type = None
                else:
                    nargs = None
                parser.add_argument(
                    "--" + arg_name,
                    dest=arg_name.replace("-", "_"),
                    help=help,
                    default=attr,
                    type=arg_type,
                    action=action,
                    required=required,
                    choices=choices,
                    nargs=nargs,
                )

        return parser

    def update_values(self, values):
        if not values:
            return
        for key in values:
            if self._metadata[key][METADATA.TYPE] == TYPENAME.CONFIG:
                getattr(self, key).update_values(values[key])
            else:
                setattr(self, key, values[key])

    def assert_values(self, metadata=None, name=""):
        if not metadata:
            metadata = self.get_metadata()
        for attr_name in metadata:
            if not metadata[attr_name]:
                continue
            show_name = attr_name
            if name:
                show_name = "%s.%s" % (name, show_name)
            assert hasattr(self, attr_name), ("%s not exists" % show_name)
            attr = getattr(self, attr_name)
            meta = self.normalize_metadata(metadata=metadata[attr_name])
            if meta[METADATA.TYPE] == TYPENAME.CONFIG:
                assert isinstance(
                    attr, Config), ("%s not instance of Config" % show_name)
                attr.assert_values(metadata[attr_name], name=show_name)
            else:
                if METADATA.MIN in meta:
                    assert attr >= meta[METADATA.MIN], (
                        "%s required to be at least %s" % (show_name,
                                                           meta[METADATA.MIN]))
                if METADATA.MAX in meta:
                    assert attr <= meta[METADATA.MAX], (
                        "%s, required to be at most %s" % (show_name,
                                                           meta[METADATA.MAX]))
                if METADATA.CHOICES in meta:
                    assert attr in meta[METADATA.CHOICES], ("%s not in %s" % (
                        show_name, meta[METADATA.CHOICES]))

    def logging_values(self, metadata=None, verbosity="INFO", name=""):
        if not metadata:
            metadata = self.get_metadata()
        for attr_name in metadata:
            if not metadata[attr_name]:
                continue
            attr = getattr(self, attr_name)
            logging_name = attr_name
            if name:
                logging_name = "%s.%s" % (name, logging_name)
            if isinstance(attr, Config):
                attr.logging_values(
                    metadata[attr_name],
                    verbosity=verbosity,
                    name=logging_name)
            else:
                logging.log(
                    get_logging_level(verbosity),
                    "%s: %s" % (logging_name, getattr(self, attr_name)))

    def update_value_by_argument(self, name, value, ignore_not_found=True):
        if isinstance(name, str):
            name = name.split("_")
        name = list(filter(str, name))
        if len(name) <= 0:
            raise AttributeError("argument name error")
        level_name = ""
        index = 0
        while index < len(name):
            if level_name:
                level_name += "_" + name[index]
            else:
                level_name = name[index]
            if level_name in self._metadata:
                break
            index += 1

        if index < len(name):
            attr = getattr(self, level_name)
            if isinstance(attr, Config):
                attr.update_value_by_argument(name[index + 1:], value)
            else:
                setattr(self, level_name, value)
        else:
            if not ignore_not_found:
                raise AttributeError("argument not found: %s" % name)

    def update_values_by_arguments(self, args, **kwargs):
        args = vars(args)
        for arg_name in args:
            self.update_value_by_argument(arg_name, args[arg_name], **kwargs)

    def update_values_by_argument_parser(self,
                                         parser=None,
                                         arguments=None,
                                         config_name="config.filename",
                                         **kwargs):
        parser = self.argument_parser(parser=parser)
        args = parser.parse_args(arguments)
        # update values to get prog config filename
        self.update_values_by_arguments(args)
        if not config_name:
            return args
        attr = self.getattr_by_name(config_name)
        if not attr:
            return args
        self.update_values_by_yaml(
            filenames=os.path.expandvars(os.path.expanduser(attr)), **kwargs)
        # force args overrides prog_config
        parser = self.argument_parser()
        args = parser.parse_args(arguments)
        self.update_values_by_arguments(args)
        return args

    def getattr_by_name(self, name):
        names = filter(str, name.split("."))
        if not names:
            return None
        attr = self
        for name in names:
            attr = getattr(attr, name)
        return attr

    def dump_config(self, filename="", config_name="config.dump", exit=True):
        if not filename and config_name:
            filename = self.getattr_by_name(config_name)
        if not filename:
            raise ValueError("no filename specified")
        values = self.get_values()
        yaml.dump_yaml(values, filename=filename)
        if exit:
            sys.exit(0)

    def update_values_by_yaml(self, contents=[], filenames=[], **kwargs):
        for item in yaml.load_yaml(contents=contents, filenames=filenames):
            item = utils.get_item_by_catrgory(item, **kwargs)
            self.update_values(item)


class TYPENAME():
    CONFIG = "Config"
    FLOAT = "float"
    INT = "int"
    LIST = "list"
    TUPLE = "tuple"
    DICT = "dict"
    STR = "str"
    MODULE = "module"
    NONE = "None"
    BOOL = "bool"


METADATA_KEYWORD = [
    "type", "value", "argparse", "help", "action", "choices", "required",
    "min", "max", "nargs"
]


class METADATA():
    pass


for keyword in METADATA_KEYWORD:
    setattr(METADATA, keyword.upper(), keyword)

MODULE_TYPE = type(os)
NONE_TYPE = type(None)
STRING2TYPE = {
    TYPENAME.CONFIG: Config,
    TYPENAME.FLOAT: float,
    TYPENAME.INT: int,
    TYPENAME.LIST: list,
    TYPENAME.TUPLE: tuple,
    TYPENAME.DICT: dict,
    TYPENAME.STR: str,
    TYPENAME.BOOL: bool,
    TYPENAME.MODULE: MODULE_TYPE,
    TYPENAME.NONE: NONE_TYPE
}

TYPE2STRING = {
    Config: TYPENAME.CONFIG,
    float: TYPENAME.FLOAT,
    int: TYPENAME.INT,
    list: TYPENAME.LIST,
    tuple: TYPENAME.TUPLE,
    dict: TYPENAME.DICT,
    str: TYPENAME.STR,
    bool: TYPENAME.BOOL,
    MODULE_TYPE: TYPENAME.MODULE,
    NONE_TYPE: TYPENAME.NONE,
}

TYPE2VALUE = {
    Config: None,
    float: 0.,
    int: 0,
    list: [],
    tuple: (),
    dict: {},
    str: "",
    bool: False,
    MODULE_TYPE: "",
    NONE_TYPE: None,
}


def string2type(string):
    if string in STRING2TYPE:
        return STRING2TYPE[string]
    else:
        return str


def type2string(type):
    if type in TYPE2STRING:
        return TYPE2STRING[type]
    else:
        return TYPENAME.STR


def typestring(value):
    for key in TYPE2STRING:
        if isinstance(value, key):
            return TYPE2STRING[key]
    return TYPENAME.STR


def type2value(type, value=None):
    if isinstance(type, str):
        type = string2type(type)
    if value is None:
        value = TYPE2VALUE[type]
    elif (type == list or type == tuple) and isinstance(value, str):
        value = [value]
    return type(value)


if __name__ == "__main__":
    print("test get_config====================")
    config = get_config()
    print(config)
    print(config.get_metadata())
    print("test update_metadata===============")
    for item in yaml.load_yaml(filenames=["recognizer.yaml"]):
        config.update_metadata(metadata=item)
    print(config.get_metadata())
    print(config.get_metadata()["recognizer"]["prog"])
    print(id(config.recognizer.prog._metadata))
    print("test update_values_by_yaml=========")
    config.update_values_by_yaml(filenames=["detector.yaml"])
    print(config.get_metadata())
    print("test update_values_by_arguments====")
    parser = config.argument_parser()
    args = parser.parse_args()
    config.update_values_by_arguments(args)
    print(config.get_metadata())
    print("test logging_values================")
    config.logging_values({}, verbosity="CRITICAL")
    print("test assert_values=================")
    config.assert_values()
