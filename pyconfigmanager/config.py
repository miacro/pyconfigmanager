from .options import ArgumentOptions
from pyconfigmanager import utils
import logging
from .logger import get_logging_level
import argparse
import sys
from . import errors


def isattrname(name):
    if len(name) > 2 and name[0:1] == "_" and name[-1:] == "_":
        return True
    else:
        return False


class Config():
    ATTR_NAMES = ("_type_", "_value_", "_required_", "_min_", "_max_",
                  "_help_", "_argoptions_")
    ATTR_ITEMS = "_items_"
    ATTR_ACCESSOR = ("_schema_", "_values_")

    def __init__(self, schema=None):
        super().__setattr__(self.ATTR_ITEMS, {})
        for name in self.ATTR_NAMES:
            setattr(self, name, None)
        self._schema_ = schema

    def __new__(self, schema={}):
        return super(Config, self).__new__(self)

    def __iter__(self):
        for name in getattr(self, self.ATTR_ITEMS):
            yield name

    def __repr__(self):
        return str(self._values_)

    def __getitem__(self, name):
        if not name:
            return self

        if not (isinstance(name, list) or isinstance(name, tuple)):
            names = [name]
        else:
            names = name

        name = names[0]
        names = names[1:]
        if name not in getattr(self, self.ATTR_ITEMS):
            raise errors.ItemError("'{}' object has no item '{}'".format(
                self.__class__.__name__, name))
        return getattr(self, self.ATTR_ITEMS)[name][names]

    def __setitem__(self, name, value):
        if name:
            if not (isinstance(name, list) or isinstance(name, tuple)):
                names = [name]
            else:
                names = name
        else:
            names = []

        item = self[names]
        if isinstance(value, Config):
            value = value._value_
        item._value_ = value

    def __delitem__(self, name):
        if name not in getattr(self, self.ATTR_ITEMS):
            raise errors.ItemError("'{}' object has no item '{}'".format(
                self.__class__.__name__, name))
        del getattr(self, self.ATTR_ITEMS)[name]

    def __getattribute__(self, name):
        if (name in dir(Config) or name in Config.ATTR_NAMES
                or name == Config.ATTR_ITEMS):
            return super().__getattribute__(name)

        item = self[name]
        if item._isleaf_:
            return item._value_
        else:
            return item

    def __setattr__(self, name, value):
        if name in self.ATTR_ACCESSOR:
            return super().__setattr__(name, value)
        elif name in dir(Config):
            raise errors.AttributeError(
                "Can't modify reserved attr '{}'".format(name))
        elif name in self.ATTR_NAMES:
            if name == "_argoptions_":
                if isinstance(value, ArgumentOptions):
                    pass
                elif isinstance(value, dict):
                    value = ArgumentOptions(**value)
                else:
                    value = bool(value)
            elif name == "_type_":
                if value is not None:
                    if isinstance(value, type):
                        value = utils.typename(value)
                    else:
                        value = str(value)
                    if self._value_ is not None:
                        super().__setattr__("_value_",
                                            utils.convert_type(
                                                self._value_, value))
                    if self._max_ is not None:
                        super().__setattr__("_max_",
                                            utils.convert_type(
                                                self._max_, value))
                    if self._min_ is not None:
                        super().__setattr__("_min_",
                                            utils.convert_type(
                                                self._min_, value))
            elif name == "_max_" or name == "_min_" or name == "_value_":
                if (self._type_ is not None and value is not None):
                    value = utils.convert_type(value, self._type_)
            return super().__setattr__(name, value)
        else:
            self[name] = value

    def __delattr__(self, name):
        if name == self.ATTR_ITEMS:
            super().__setattr__(name, {})
        elif name in self.ATTR_NAMES:
            setattr(self, name, None)
        elif name == "_schema_":
            super().__setattr__(self.ATTR_ITEMS, {})
            for name in self.ATTR_NAMES:
                setattr(self, name, None)
        else:
            raise errors.AttributeError(
                "Unexcepted attr name '{}'".format(name))

    @property
    def _isleaf_(self):
        return len(getattr(self, self.ATTR_ITEMS)) == 0

    @property
    def _attrs_(self):
        result = {}
        for name in self.ATTR_NAMES:
            result[name] = getattr(self, name)
        return result

    @property
    def _values_(self):
        result = {}
        for name in self:
            item = self[name]
            if item._isleaf_:
                result[name] = item._value_
            else:
                result[name] = item._values_
                if item._value_ is not None:
                    result[name]["_value_"] = item._value_
        return result

    @_values_.setter
    def _values_(self, values):
        if "_value_" in values:
            self._value_ = values["_value_"]
        for name in values:
            if isattrname(name):
                continue
            item = self[name]
            if item._isleaf_:
                item._value_ = values[name]
            elif isinstance(values[name], dict):
                item._values_ = values[name]
            else:
                item._value_ = values[name]

    @property
    def _schema_(self):
        result = {}
        for name in self._attrs_:
            result[name] = self._attrs_[name]
        for name in getattr(self, self.ATTR_ITEMS):
            result[name] = getattr(self, self.ATTR_ITEMS)[name]._schema_
        return result

    @_schema_.setter
    def _schema_(self, value={}):
        def normalize_schema(schema):
            if not isinstance(schema, dict):
                schema = {"_value_": schema}
            if (("_value_" in schema) and (schema["_value_"] is not None)):
                if (("_type_" not in schema) or (schema["_type_"] is None)):
                    schema["_type_"] = utils.typename(type(schema["_value_"]))
            return schema

        if value is None:
            return
        schema = normalize_schema(value)
        for name in sorted(schema.keys()):
            if isattrname(name):
                if name not in Config.ATTR_NAMES:
                    raise errors.AttributeError(
                        "Unexcepted attr '{}'".format(name))
                setattr(self, name, schema[name])
            elif name not in self:
                getattr(self, self.ATTR_ITEMS)[name] = Config(schema[name])
            else:
                self[name]._schema_ = schema[name]

    def logging_values(self, schema=None, verbosity="INFO", name=""):
        if not schema:
            schema = self.schema(recursive=True)
        elif not isinstance(schema, dict):
            schema = {"_value_": None}
        if "_value_" in schema:
            tolog = False
            if self.isleaf():
                if schema["_value_"] or schema["_value_"] is None:
                    tolog = True
            else:
                if schema["_value_"]:
                    tolog = True
            if tolog:
                logging.log(
                    get_logging_level(verbosity), "{}: {}".format(
                        name, self._value_))
        for item_name in sorted(schema.keys()):
            if isattrname(item_name):
                continue
            if not schema[item_name]:
                continue
            if name:
                show_name = "{}.{}".format(name, item_name)
            else:
                show_name = item_name
            item = self[item_name]
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

        for attr_name, attr in self._items_:
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
                if attr._argoptions_ is False:
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
            for key, value in values._items_ if key not in ignores
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
