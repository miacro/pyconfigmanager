from .options import Options
from pyconfigmanager import utils
import logging
from .logging import get_logging_level
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
        if isinstance(schema, Options):
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
        return Options(**schema)

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

    def getattr(self, name, raw=False):
        if isinstance(name, list) or isinstance(name, tuple):
            names = name
            attr = self
            for name in names:
                attr = attr.getattr(name=name, raw=raw)
            return attr
        else:
            attr = super().__getattribute__(name)
            if (not raw) and isinstance(attr, Options):
                return attr.value
            else:
                return attr

    def setattr(self, name, value, raw=False):
        if not raw:
            attr = self.getattr(name, raw=True)
            if (isinstance(attr, Options)):
                attr.value = value
            else:
                raise AttributeError("{} {} {}".format(
                    "only attribute 'value' of 'Options' can be updated",
                    "when raw=False,", "while attribute: '{}'".format(
                        type(attr).__name__)))
        else:
            if isinstance(value, Options) or isinstance(value, Config):
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
            elif isinstance(attr, Options):
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
        if isinstance(attr, Options):
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
            if isinstance(attr, Options) and isinstance(init_attr, Options):
                attr.update_values(values=vars(init_attr), merge=merge)
            elif isinstance(attr, Options) and isinstance(init_attr, Config):
                self.setattr(name, schema[name], raw=True)
            elif isinstance(attr, Config) and isinstance(init_attr, Options):
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
                attr.assert_value(options=check_attr)

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
            if isinstance(attr, Options):
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

    def argument_options(self,
                         prefix="",
                         subcommands=(),
                         command_name="command"):
        pass

    def argument_parser(self,
                        parser=None,
                        subcommands=(),
                        ignores=(),
                        command_attrname="command",
                        parentnames=[],
                        argprefix="",):
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
                subparser.set_defaults(
                    **{command_attrname: arg_name})
                self.getattr(
                    attr_name, raw=True).argument_parser(
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
                        self.setattr(match_name, value)
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

        if (subcommands and (command_attrname in args) and
                args[command_attrname]):
            command_names = [
                name for name in args[command_attrname].split(".") if name]
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
            self.update_values(utils.pickitems(
                values,
                pickname=valuefile_pickname,
                excludes=valuefile_excludes))
        # force args overrides prog_config
        parser = self.argument_parser(subcommands=subcommands,)
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
                self.setattr(name, values[name], raw=False)

    def dump_config(self,
                    filename="",
                    filename_config="config.dump",
                    exit=True,
                    ignores=["config"],
                    dumpname=""):
        if not filename and filename_config:
            filename_config = list(filter(str, filename_config.split(".")))
            filename = self.getattr(
                filename_config, raw=False)
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
