from .options import ArgumentOptions
from pyconfigmanager import utils
import logging
from .logger import get_logging_level
import argparse
import sys
from . import errors


class Config():
    ATTR_INDICATOR = "."
    ATTR_NAMES = ("type", "value", "required", "min", "max", "help",
                  "argoptions")
    ATTR_SUBITEM = "subitems"

    def __init__(self, schema=None):
        self.update_schema(schema=schema, merge=False)

    def __new__(self, schema={}):
        return super(Config, self).__new__(self)

    def __iter__(self):
        for name in getattr(self, self.ATTR_SUBITEM):
            yield name

    def __repr__(self):
        return str(self.values())

    def __getitem__(self, name):
        return self.getitem(name, raw=None)

    def __setitem__(self, name, value):
        return self.setitem(name, value, raw=None)

    def __delitem__(self, name):
        if name not in getattr(self, self.ATTR_SUBITEM):
            raise errors.ItemError("'{}' object has no item '{}'".format(
                self.__class__.__name__, name))
        del getattr(self, self.ATTR_SUBITEM)[name]

    def __getattribute__(self, name):
        if (name in dir(Config) or name in Config.ATTR_NAMES
                or name == Config.ATTR_SUBITEM):
            return super().__getattribute__(name)
        return super().__getattribute__("getitem")(name, raw=None)

    def __setattr__(self, name, value):
        if name in dir(Config):
            raise errors.AttributeError(
                "Can't modify reserved attr '{}'".format(name))
        elif name in self.ATTR_NAMES:
            if name == "argoptions":
                if isinstance(value, ArgumentOptions):
                    pass
                elif isinstance(value, dict):
                    value = ArgumentOptions(**value)
                else:
                    value = bool(value)
            elif name == "type":
                if value is not None:
                    if isinstance(value, type):
                        value = utils.typename(value)
                    else:
                        value = str(value)
                    if self.value is not None:
                        super().__setattr__("value",
                                            utils.convert_type(
                                                self.value, value))
                    if self.max is not None:
                        super().__setattr__("max",
                                            utils.convert_type(
                                                self.max, value))
                    if self.min is not None:
                        super().__setattr__("min",
                                            utils.convert_type(
                                                self.min, value))
            elif name == "max" or name == "min" or name == "value":
                if (self.type is not None and value is not None):
                    value = utils.convert_type(value, self.type)
            return super().__setattr__(name, value)
        else:
            return super().__getattribute__("setitem")(name, value, raw=None)

    def __delattr__(self, name):
        if name == self.ATTR_SUBITEM:
            super().__setattr__(name, {})
        elif name in self.ATTR_NAMES:
            setattr(self, name, None)
        else:
            raise errors.AttributeError(
                "Unexcepted attr name '{}'".format(name))

    def isleaf(self):
        return len(getattr(self, self.ATTR_SUBITEM)) == 0

    def getitem(self, name, raw=None):
        if not name:
            if raw is None:
                if not self.isleaf():
                    raw = True
            if raw:
                return self
            else:
                return self.value

        if not (isinstance(name, list) or isinstance(name, tuple)):
            names = [name]
        else:
            names = name

        name = names[0]
        names = names[1:]
        if name not in getattr(self, self.ATTR_SUBITEM):
            raise errors.ItemError("'{}' object has no item '{}'".format(
                self.__class__.__name__, name))
        return getattr(self, self.ATTR_SUBITEM)[name].getitem(names, raw=raw)

    def setitem(self, name, value, raw=None):
        if name:
            if not (isinstance(name, list) or isinstance(name, tuple)):
                names = [name]
            else:
                names = name
        else:
            names = []

        if not raw:
            item = self.getitem(names, raw=True)
            if isinstance(value, Config):
                value = getattr(value, "value")
            item.value = value
            return
        else:
            item = self.getitem(names[:-1], raw=True)
            if not names:
                raise errors.ItemError(
                    "Unexcepted item name '{}'".format(names))
            name = names[-1]
            if not isinstance(value, Config):
                value = Config(value)
            getattr(item, self.ATTR_SUBITEM)[name] = value

    def items(self, raw=None):
        result = []
        for name in self:
            result.append((name, self.getitem(name, raw=raw)))
        return result

    def attrs(self):
        result = []
        for name in self.ATTR_NAMES:
            result.append((name, getattr(self, name)))
        return result

    def values(self):
        result = {}
        for name in self:
            item = self.getitem(name, raw=True)
            if item.isleaf():
                result[name] = item.value
            else:
                result[name] = item.values()
        return result

    def schema(self, recursive=True):
        result = {}
        for name, value in self.attrs():
            result[self.ATTR_INDICATOR + name] = value
        if recursive:
            for name, value in self.items(raw=True):
                result[name] = value.schema(recursive=recursive)
        return result

    def update_schema(self, schema={}, merge=True):
        def normalize_schema(schema):
            attrtype = self.ATTR_INDICATOR + "type"
            attrvalue = self.ATTR_INDICATOR + "value"
            if not isinstance(schema, dict):
                schema = {attrvalue: schema}
            if ((attrvalue in schema) and (schema[attrvalue] is not None)):
                if ((attrtype not in schema) or (schema[attrtype] is None)):
                    schema[attrtype] = utils.typename(type(schema[attrvalue]))
            return schema

        schema = normalize_schema(schema)
        if not merge:
            for name in self.ATTR_NAMES:
                setattr(self, name, None)
            super().__setattr__(self.ATTR_SUBITEM, {})
        for name in sorted(schema.keys()):
            if name[0] == self.ATTR_INDICATOR:
                setattr(self, name[1:], schema[name])
            elif name not in self:
                self.setitem(name, Config(schema[name]), raw=True)
            else:
                self.getitem(name, raw=True).update_schema(schema[name])

    def assert_value(self, schema=None, name=""):
        show_name = name
        if schema is None:
            checker = self
        elif not isinstance(schema, Config):
            checker = Config({
                name: value
                for name, value in schema.items()
                if name[0:1] == self.ATTR_INDICATOR
            })
        else:
            checker = schema

        value = self.value
        check_type = checker.type
        check_min = checker.min
        check_max = checker.max
        if show_name:
            message = "Item '{}': value ".format(show_name)
        else:
            message = "Item value "
        if checker.required:
            assert value is not None, message + "required"
        if check_type is not None:
            assert isinstance(value, utils.locate_type(check_type)), (
                message +
                "'{}' not instance of '{}'".format(value, check_type))
        if check_min is not None:
            assert value >= check_min, (
                message + "'{}' required >= {}".format(value, check_min))
        if check_max is not None:
            assert value <= check_max, (
                message + "'{}' required <= {}".format(value, check_max))

    def assert_values(self, schema=None, name=""):
        if not schema:
            schema = self.schema(recursive=True)

        self.assert_value(
            schema={
                name: value
                for name, value in schema.items()
                if name[0:1] == self.ATTR_INDICATOR
            },
            name=name)
        for item_name in schema:
            if item_name[0:1] == self.ATTR_INDICATOR:
                continue
            if not schema[item_name]:
                continue
            if name:
                show_name = "{}.{}".format(name, item_name)
            else:
                show_name = item_name
            assert item_name in self, (
                "'Config' object has no item '{}'".format(show_name))
            item = self.getitem(item_name, raw=True)
            if isinstance(schema[item_name], dict):
                item.assert_values(schema=schema[item_name], name=show_name)

    def logging_values(self, schema=None, verbosity="INFO", name=""):
        attr_value = self.ATTR_INDICATOR + "value"
        if not schema:
            schema = self.schema(recursive=True)
        elif not isinstance(schema, dict):
            schema = {attr_value: None}
        if attr_value in schema:
            tolog = False
            if self.isleaf():
                if schema[attr_value] or schema[attr_value] is None:
                    tolog = True
            else:
                if schema[attr_value]:
                    tolog = True
            if tolog:
                logging.log(
                    get_logging_level(verbosity), "{}: {}".format(
                        name, self.value))
        for item_name in sorted(schema.keys()):
            if item_name[0:1] == self.ATTR_INDICATOR:
                continue
            if not schema[item_name]:
                continue
            if name:
                show_name = "{}.{}".format(name, item_name)
            else:
                show_name = item_name
            item = self.getitem(item_name, raw=True)
            item.logging_values(
                schema=schema[item_name], verbosity=verbosity, name=show_name)

    def argument_options(self,
                         prefix="",
                         subcommands=(),
                         command_name="command"):
        pass

    def argument_parser(
            self,
            parser=None,
            subcommands=(),
            ignores=(),
            command_attrname="command",
            parentnames=[],
            argprefix="",
    ):
        subcommands = normalize_subcommands(subcommands)
        if not parser:
            parser = argparse.ArgumentParser(
                formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                description="")
        if subcommands:
            subparsers = parser.add_subparsers(
                title="subcommands", help="subcommands", dest=command_attrname)
        else:
            subcommands = {}
            subparsers = None

        for attr_name, attr in self.items(raw=True):
            if attr_name == command_attrname:
                continue
            if attr_name in ignores:
                continue
            if attr_name in subcommands:
                subparser = subparsers.add_parser(
                    attr_name,
                    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                    description=attr_name,
                    help=attr_name)
                arg_name = "".join(
                    ["{}.".format(name) for name in parentnames])
                arg_name += attr_name
                subparser.set_defaults(**{command_attrname: arg_name})
                getattr(
                    self, attr_name, raw=True).argument_parser(
                        parser=subparser,
                        subcommands=subcommands[attr_name],
                        parentnames=parentnames + [attr_name])
                continue

            arg_name = attr_name if not argprefix else "{}-{}".format(
                argprefix, attr_name)
            if isinstance(attr, Config):
                attr.argument_parser(parser=parser, argprefix=arg_name)
            elif isinstance(attr, Options):
                if attr.argoptions is False:
                    continue
                options = attr.argument_options()
                if "dest" in options:
                    del options["dest"]
                parser.add_argument(
                    "--" + arg_name,
                    dest=arg_name.replace("-", "_"),
                    **options)
        return parser

    def update_value_by_argument(self, argname, value, ignore_not_found=True):
        if isinstance(argname, str):
            names = argname.split("_")
        else:
            names = argname
        names = [name for name in names]
        if len(names) > 0:
            test_name = ""
            match_name = None
            match_index = 0
            for index, item in enumerate(names):
                test_name = "{}_{}".format(test_name,
                                           item) if test_name else item
                if test_name in self:
                    match_name = test_name
                    match_index = index

            if match_name:
                attr = self.getattr(match_name, raw=True)
                if isinstance(attr, Options):
                    if match_index == len(names) - 1:
                        setattr(self, match_name, value)
                        return
                elif isinstance(attr, Config):
                    if match_index < len(names) - 1:
                        attr.update_value_by_argument(
                            names[match_index + 1:],
                            value,
                            ignore_not_found=ignore_not_found)
                        return
        if not ignore_not_found:
            raise AttributeError(
                "attr not found by argname '{}'".format(argname))

    def update_values_by_arguments(self,
                                   args,
                                   subcommands=(),
                                   command_attrname="command",
                                   **kwargs):
        subcommands = normalize_subcommands(subcommands)
        if not isinstance(args, dict):
            args = vars(args)

        if (subcommands and (command_attrname in args)
                and args[command_attrname]):
            command_names = [
                name for name in args[command_attrname].split(".") if name
            ]
            subconfigs = [self]
            for name in command_names:
                if name not in subcommands:
                    subconfigs = []
                    break
                subconfigs.append(subconfigs[-1].getattr(name, raw=True))
                subcommands = subcommands[name]
            subconfigs = subconfigs[1:]
        else:
            subconfigs = []
        subconfigs.reverse()
        for arg_name in args:
            argfound = False
            for index, subconfig in enumerate(subconfigs):
                try:
                    subconfig.update_value_by_argument(
                        arg_name, args[arg_name], ignore_not_found=False)
                    argfound = True
                    break
                except AttributeError:
                    argfound = False
            if argfound:
                continue
            self.update_value_by_argument(arg_name, args[arg_name], **kwargs)

    def update_values_by_argument_parser(self,
                                         parser=None,
                                         arguments=None,
                                         subcommands=(),
                                         valuefile_config="config.file",
                                         valuefile_pickname="",
                                         valuefile_excludes=[]):
        parser = self.argument_parser(parser=parser, subcommands=subcommands)
        args = parser.parse_args(arguments)
        # update values to get prog config filename
        self.update_values_by_arguments(args, subcommands=subcommands)
        if not valuefile_config:
            return args
        valuefile_config = list(filter(str, valuefile_config.split(".")))
        attr = self.getattr(valuefile_config, raw=False)
        if not attr:
            return args
        for values in utils.load_config(filename=attr):
            self.update_values(
                utils.pickitems(
                    values,
                    pickname=valuefile_pickname,
                    excludes=valuefile_excludes))
        # force args overrides prog_config
        parser = self.argument_parser(subcommands=subcommands, )
        args = parser.parse_args(arguments)
        self.update_values_by_arguments(args, subcommands=subcommands)
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
            elif isinstance(attr, Options):
                setattr(self, name, values[name], raw=False)

    def dump_config(self,
                    filename="",
                    filename_config="config.dump",
                    exit=True,
                    ignores=["config"],
                    dumpname=""):
        if not filename and filename_config:
            filename_config = list(filter(str, filename_config.split(".")))
            filename = self.getattr(filename_config, raw=False)
        if not filename:
            raise ValueError("no filename specified")
        values = self.values()
        values = {
            key: value
            for key, value in values.items() if key not in ignores
        }
        if dumpname:
            values = {dumpname: values}
        utils.dump_config(values, filename=filename)
        if exit:
            sys.exit(0)


def normalize_subcommands(subcommands):
    if isinstance(subcommands, dict):
        return subcommands
    elif isinstance(subcommands, list) or isinstance(subcommands, tuple):
        return {name: True for name in subcommands}
    return {}
