from .item import Item
from pyconfigmanager import utils
import logging
from .logging_config import get_logging_level
import argparse
import sys


class Config():
    ITEM_INDICATOR = "$"

    def __init__(self, schema={}):
        if not isinstance(schema, dict):
            raise ValueError("schema('{}') must be instance of dict".format(
                utils.typename(type(schema))))
        self.update_schema(schema=schema, merge=False)

    def __new__(self, schema={}):
        if isinstance(schema, Item):
            schema = vars(schema)
        elif isinstance(schema, dict):
            if any([
                    True if key[:1] == Config.ITEM_INDICATOR else False
                    for key in schema
            ]):
                schema = {(key[1:]
                           if key[:1] == Config.ITEM_INDICATOR else key): value
                          for key, value in schema.items()}
            else:
                return super(Config, self).__new__(self)
        else:
            schema = {"value": schema}
        if (("value" in schema) and (schema["value"] is not None)):
            if (("type" not in schema) or (schema["type"] is None)):
                schema["type"] = utils.typename(type(schema["value"]))
        return Item(**schema)

    def __iter__(self):
        for name in self.__dict__:
            yield name

    def __repr__(self):
        return str(self.values())

    def __getitem__(self, name):
        return self.getattr(name, raw=False)

    def __setitem__(self, name, value):
        return setattr(self, name, value)

    def __delitem__(self, name):
        return delattr(self, name)

    def __getattribute__(self, name):
        return super().__getattribute__("getattr")(name, raw=False)

    def __setattr__(self, name, value):
        return super().__setattr__(name, value)

    def getattr(self, name, raw=False, name_slicer=None):
        if name_slicer:
            names = list(filter(str, name.split(name_slicer)))
            if not names:
                raise AttributeError(
                    "'{}' object has no attribute '{}'".format(
                        self.__class__.__name__, name))
            attr = self
            for name in names:
                attr = attr.getattr(name=name, raw=raw, name_slicer=None)
            return attr
        else:
            attr = super().__getattribute__(name)
            if (not raw) and isinstance(attr, Item):
                return attr.value
            return attr

    def setattr(self, name, value, raw=False):
        if not raw:
            attr = self.getattr(name, raw=True)
            if (isinstance(attr, Item)):
                attr.value = value
            else:
                raise AttributeError("{} {} {}".format(
                    "only attribute 'value' of 'Item' can be updated",
                    "when raw=False,", "while attribute: '{}'".format(
                        type(attr).__name__)))
        else:
            if isinstance(value, Item) or isinstance(value, Config):
                attr_value = value
            else:
                attr_value = Config(value)
            return super().__setattr__(name, attr_value)

    def items(self, raw=False):
        result = []
        for name in self:
            result.append((name, self.getattr(name, raw=raw)))
        return result

    def values(self):
        result = {}
        for name in self:
            attr = self.getattr(name, raw=True)
            if isinstance(attr, Config):
                result[name] = attr.values()
            elif isinstance(attr, Item):
                result[name] = attr.value
            else:
                result[name] = attr
        return result

    def schema(self, name=None):
        if name is None:
            name = list(self.__dict__.keys())
        if isinstance(name, list):
            result = {}
            for name_item in name:
                result[name_item] = self.schema(name_item)
            return result
        attr = self.getattr(name, raw=True)
        if isinstance(attr, Item):
            return {
                "{}{}".format(Config.ITEM_INDICATOR, key): value
                for key, value in vars(attr).items()
            }
        elif isinstance(attr, Config):
            return attr.schema()

    def update_schema(self, schema={}, merge=True):
        if schema is None:
            if not merge:
                for name in [name for name, _ in self.items()]:
                    del self[name]
            return
        for name in schema:
            if not merge:
                self.setattr(name, schema[name], raw=True)
                continue
            if schema[name] is None:
                continue
            if name not in self:
                self.setattr(name, schema[name], raw=True)
            attr = self.getattr(name, raw=True)
            init_attr = Config.__new__(Config, schema[name])
            if isinstance(attr, Item) and isinstance(init_attr, Item):
                attr.update_values(values=vars(init_attr), merge=merge)
            elif isinstance(attr, Item) and isinstance(init_attr, Config):
                self.setattr(name, schema[name], raw=True)
            elif isinstance(attr, Config) and isinstance(init_attr, Item):
                self.setattr(name, schema[name], raw=True)
            elif isinstance(attr, Config) and isinstance(init_attr, Config):
                attr.update_schema(schema[name], merge=merge)
            else:
                self.setattr(name, schema[name], raw=True)

    def assert_values(self, schema=None, name=""):
        if not schema:
            schema = self.schema()

        for attr_name in schema:
            if not schema[attr_name]:
                continue
            if name:
                show_name = "{}.{}".format(name, attr_name)
            else:
                show_name = attr_name
            assert hasattr(self, attr_name), (
                "'Config' object has no attribute '{}'".format(show_name))
            attr = self.getattr(attr_name, raw=True)
            if isinstance(schema[attr_name], dict):
                check_attr = Config.__new__(Config, schema[attr_name])
                assert isinstance(attr, type(check_attr)), (
                    "attribute '{}' is not instance of '{}'".format(
                        show_name, utils.typename((type(check_attr)))))
            elif schema[attr_name] is True:
                check_attr = None
            else:
                check_attr = {}

            if isinstance(attr, Config):
                if check_attr:
                    attr.assert_values(
                        schema=schema[attr_name], name=show_name)
            else:
                attr.assert_value(item=check_attr)

    def logging_values(self, schema=None, verbosity="INFO", name=""):
        if not schema:
            schema = self.schema()
        for attr_name in schema:
            if not schema[attr_name]:
                continue
            if name:
                show_name = "{}.{}".format(name, attr_name)
            else:
                show_name = attr_name
            attr = self.getattr(attr_name, raw=True)
            if isinstance(attr, Item):
                logging.log(
                    get_logging_level(verbosity), "{}: {}".format(
                        show_name, attr.value))
            elif isinstance(attr, Config):
                if isinstance(
                        Config.__new__(Config, schema[attr_name]), Config):
                    attr.logging_values(
                        schema=schema[attr_name],
                        verbosity=verbosity,
                        name=show_name)
                else:
                    if schema[attr_name] is True:
                        attr.logging_values(
                            schema=attr.schema(),
                            verbosity=verbosity,
                            name=show_name)

    def argument_parser(self, parser=None, prefix=""):
        if not parser:
            parser = argparse.ArgumentParser(
                formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                description="")

        for attr_name, attr in self.items(raw=True):
            arg_name = attr_name if not prefix else "{}-{}".format(
                prefix, attr_name)
            if isinstance(attr, Config):
                attr.argument_parser(parser=parser, prefix=arg_name)
            elif isinstance(attr, Item):
                if attr.argparse is False:
                    continue
                options = attr.argparse_options()
                del options["dest"]
                if isinstance(options["type"], str):
                    options["type"] = utils.locate_type(options["type"])
                parser.add_argument(
                    "--" + arg_name,
                    dest=arg_name.replace("-", "_"),
                    **options)
        return parser

    def update_value_by_argument(self, argname, value, ignore_not_found=True):
        if isinstance(argname, str):
            name = argname.split("_")
        else:
            name = argname
        name = list(filter(str, name))
        if len(name) > 0:
            level_name = ""
            index = 0
            while index < len(name):
                if level_name:
                    level_name += "_" + name[index]
                else:
                    level_name = name[index]
                if level_name in self:
                    break
                index += 1

            if index < len(name):
                attr = self.getattr(level_name, raw=True)
                if isinstance(attr, Item):
                    if index == len(name) - 1:
                        self.setattr(level_name, value)
                        return
                elif isinstance(attr, Config):
                    if index < len(name) - 1:
                        attr.update_value_by_argument(
                            name[index + 1:],
                            value,
                            ignore_not_found=ignore_not_found)
                        return
        if not ignore_not_found:
            raise AttributeError(
                "attr not found by argname '{}'".format(argname))

    def update_values_by_arguments(self, args, **kwargs):
        if not isinstance(args, dict):
            args = vars(args)
        for arg_name in args:
            self.update_value_by_argument(arg_name, args[arg_name], **kwargs)

    def update_values_by_argument_parser(self,
                                         parser=None,
                                         arguments=None,
                                         config_name="config.file",
                                         **kwargs):
        parser = self.argument_parser(parser=parser)
        args = parser.parse_args(arguments)
        # update values to get prog config filename
        self.update_values_by_arguments(args)
        if not config_name:
            return args
        attr = self.getattr(config_name, raw=False, name_slicer=".")
        if not attr:
            return args
        self.update_values_by_file(filename=attr, **kwargs)
        # force args overrides prog_config
        parser = self.argument_parser()
        args = parser.parse_args(arguments)
        self.update_values_by_arguments(args)
        return args

    def update_values(self, values):
        for name in values:
            attr = self.getattr(name, raw=True)
            if isinstance(attr, Config):
                if not isinstance(values[name], dict):
                    raise ValueError(
                        "'values[{}]' == '{}' is not instance of 'dict'".
                        format(name, values[name]))
                attr.update_values(values[name])
            elif isinstance(attr, Item):
                self.setattr(name, values[name], raw=False)

    def update_values_by_file(self, filename=[], **kwargs):
        if isinstance(filename, str):
            filenames = [filename]
        else:
            filenames = filename

        for filename in filenames:
            for values in utils.load_config(filename=filename):
                self.update_values(
                    values=utils.get_item_by_category(values, **kwargs))

    def dump_config(self,
                    filename="",
                    config_name="config.dump",
                    exit=True,
                    category=""):
        if not filename and config_name:
            filename = self.getattr(config_name, raw=False, name_slicer=".")
        if not filename:
            raise ValueError("no filename specified")
        values = self.values()
        if category:
            values = {category: values}
        utils.dump_config(values, filename=filename)
        if exit:
            sys.exit(0)
