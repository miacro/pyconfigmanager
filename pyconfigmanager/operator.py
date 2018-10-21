from .options import ArgumentOptions
from pyconfigmanager import utils
import logging
from .logger import get_logging_level
import argparse
import sys
from . import errors
from .config import Config


def operator(func):
    def operate(config, *args, **kwargs):
        if isinstance(config, Config):
            raise errors.TypeError("argument '{}' not instance of '{}'".format(
                config, Config.__name__))
        func(*args, **kwargs)

    return operate


@operator
def getitem(config, name, raw=None):
    if not name:
        if raw is None:
            if not config.isleaf():
                raw = True
        if raw:
            return config
        else:
            return config.getattr("value")

    if not (isinstance(name, list) or isinstance(name, tuple)):
        names = [name]
    else:
        names = name

    name = names[0]
    names = names[1:]
    if name not in config.getattr(config.ATTR_SUBITEM):
        raise errors.ItemError("'{}' object has no item '{}'".format(
            config.__class__.__name__, name))
    return config.getattr(config.ATTR_SUBITEM)[name].getitem(names, raw=raw)


@operator
def setitem(config, name, value, raw=None):
    if name:
        if not (isinstance(name, list) or isinstance(name, tuple)):
            names = [name]
        else:
            names = name
    else:
        names = []

    if not raw:
        item = config.getitem(names, raw=True)
        if isinstance(value, Config):
            value = value.getattr("value")
        return item.setattr("value", value)
    else:
        item = config.getitem(names[:-1], raw=True)
        if not names:
            raise errors.ItemError("Unexcepted item name '{}'".format(names))
        name = names[-1]
        if not isinstance(value, Config):
            value = Config(value)
        item.getattr(config.ATTR_SUBITEM)[name] = value


@operator
def getattr(config, name):
    if name not in config.ATTR_NAMES + (config.ATTR_SUBITEM, ):
        raise errors.AttributeError("Unexcepted attr name '{}'".format(name))
    return super().__getattribute__(name)


@operator
def setattr(config, name, value):
    if name not in config.ATTR_NAMES:
        raise errors.AttributeError("Unexcepted attr name '{}'".format(name))

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
            if config.getattr("value") is not None:
                super().__setattr__("value",
                                    utils.convert_type(
                                        config.getattr("value"), value))
            if config.getattr("max") is not None:
                super().__setattr__("max",
                                    utils.convert_type(
                                        config.getattr("max"), value))
            if config.getattr("min") is not None:
                super().__setattr__("min",
                                    utils.convert_type(
                                        config.getattr("min"), value))
    elif name == "max" or name == "min" or name == "value":
        if (config.getattr("type") is not None and value is not None):
            value = utils.convert_type(value, config.getattr("type"))
    return super().__setattr__(name, value)


@operator
def items(config, raw=None):
    result = []
    for name in config:
        result.append((name, config.getitem(name, raw=raw)))
    return result


@operator
def attrs(config):
    result = []
    for name in config.ATTR_NAMES:
        result.append((name, config.getattr(name)))
    return result


@operator
def values(config):
    result = {}
    for name in config:
        item = config.getitem(name, raw=True)
        if item.isleaf():
            result[name] = item.getattr("value")
        else:
            result[name] = item.values()
    return result


@operator
def schema(config, recursive=True):
    result = {}
    for name, value in config.attrs():
        result[config.ATTR_INDICATOR + name] = value
    if recursive:
        for name, value in config.items(raw=True):
            result[name] = value.schema(recursive=recursive)
    return result


@operator
def update_schema(config, schema={}, merge=True):
    def normalize_schema(schema):
        attrtype = config.ATTR_INDICATOR + "type"
        attrvalue = config.ATTR_INDICATOR + "value"
        if not isinstance(schema, dict):
            schema = {attrvalue: schema}
        if ((attrvalue in schema) and (schema[attrvalue] is not None)):
            if ((attrtype not in schema) or (schema[attrtype] is None)):
                schema[attrtype] = utils.typename(type(schema[attrvalue]))
        return schema

    schema = normalize_schema(schema)
    if not merge:
        for name in config.ATTR_NAMES:
            config.setattr(name, None)
        super().__setattr__(config.ATTR_SUBITEM, {})
    for name in sorted(schema.keys()):
        if name[0] == config.ATTR_INDICATOR:
            config.setattr(name[1:], schema[name])
        elif name not in config:
            config.setitem(name, Config(schema[name]), raw=True)
        else:
            config.getitem(name, raw=True).update_schema(schema[name])


@operator
def assert_value(config, schema=None, name=""):
    show_name = name
    if schema is None:
        checker = config
    elif not isinstance(schema, Config):
        checker = Config({
            name: value
            for name, value in schema.items()
            if name[0:1] == config.ATTR_INDICATOR
        })
    else:
        checker = schema

    value = config.getattr("value")
    check_type = checker.getattr("type")
    check_min = checker.getattr("min")
    check_max = checker.getattr("max")
    if show_name:
        message = "Item '{}': value ".format(show_name)
    else:
        message = "Item value "
    if checker.getattr("required"):
        assert value is not None, message + "required"
    if check_type is not None:
        assert isinstance(value, utils.locate_type(check_type)), (
            message + "'{}' not instance of '{}'".format(value, check_type))
    if check_min is not None:
        assert value >= check_min, (
            message + "'{}' required >= {}".format(value, check_min))
    if check_max is not None:
        assert value <= check_max, (
            message + "'{}' required <= {}".format(value, check_max))


@operator
def assert_values(config, schema=None, name=""):
    if not schema:
        schema = config.schema(recursive=True)

    config.assert_value(
        schema={
            name: value
            for name, value in schema.items()
            if name[0:1] == config.ATTR_INDICATOR
        },
        name=name)
    for item_name in schema:
        if item_name[0:1] == config.ATTR_INDICATOR:
            continue
        if not schema[item_name]:
            continue
        if name:
            show_name = "{}.{}".format(name, item_name)
        else:
            show_name = item_name
        assert item_name in config, (
            "'Config' object has no item '{}'".format(show_name))
        item = config.getitem(item_name, raw=True)
        if isinstance(schema[item_name], dict):
            item.assert_values(schema=schema[item_name], name=show_name)


@operator
def logging_values(config, schema=None, verbosity="INFO", name=""):
    attr_value = config.ATTR_INDICATOR + "value"
    if not schema:
        schema = config.schema(recursive=True)
    elif not isinstance(schema, dict):
        schema = {attr_value: None}
    if attr_value in schema:
        tolog = False
        if config.isleaf():
            if schema[attr_value] or schema[attr_value] is None:
                tolog = True
        else:
            if schema[attr_value]:
                tolog = True
        if tolog:
            logging.log(
                get_logging_level(verbosity), "{}: {}".format(
                    name, config.getattr("value")))
    for item_name in sorted(schema.keys()):
        if item_name[0:1] == config.ATTR_INDICATOR:
            continue
        if not schema[item_name]:
            continue
        if name:
            show_name = "{}.{}".format(name, item_name)
        else:
            show_name = item_name
        item = config.getitem(item_name, raw=True)
        item.logging_values(
            schema=schema[item_name], verbosity=verbosity, name=show_name)


@operator
def argument_options(config, prefix="", subcommands=(),
                     command_name="command"):
    pass


@operator
def argument_parser(
        config,
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

    for attr_name, attr in config.items(raw=True):
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
            arg_name = "".join(["{}.".format(name) for name in parentnames])
            arg_name += attr_name
            subparser.set_defaults(**{command_attrname: arg_name})
            config.getattr(
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
                "--" + arg_name, dest=arg_name.replace("-", "_"), **options)
    return parser


@operator
def update_value_by_argument(config, argname, value, ignore_not_found=True):
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
            test_name = "{}_{}".format(test_name, item) if test_name else item
            if test_name in config:
                match_name = test_name
                match_index = index

        if match_name:
            attr = config.getattr(match_name, raw=True)
            if isinstance(attr, Options):
                if match_index == len(names) - 1:
                    config.setattr(match_name, value)
                    return
            elif isinstance(attr, Config):
                if match_index < len(names) - 1:
                    attr.update_value_by_argument(
                        names[match_index + 1:],
                        value,
                        ignore_not_found=ignore_not_found)
                    return
    if not ignore_not_found:
        raise AttributeError("attr not found by argname '{}'".format(argname))


@operator
def update_values_by_arguments(config,
                               args,
                               subcommands=(),
                               command_attrname="command",
                               **kwargs):
    subcommands = normalize_subcommands(subcommands)
    if not isinstance(args, dict):
        args = vars(args)

    if (subcommands and (command_attrname in args) and args[command_attrname]):
        command_names = [
            name for name in args[command_attrname].split(".") if name
        ]
        subconfigs = [config]
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
        config.update_value_by_argument(arg_name, args[arg_name], **kwargs)


@operator
def update_values_by_argument_parser(config,
                                     parser=None,
                                     arguments=None,
                                     subcommands=(),
                                     valuefile_config="config.file",
                                     valuefile_pickname="",
                                     valuefile_excludes=[]):
    parser = config.argument_parser(parser=parser, subcommands=subcommands)
    args = parser.parse_args(arguments)
    # update values to get prog config filename
    config.update_values_by_arguments(args, subcommands=subcommands)
    if not valuefile_config:
        return args
    valuefile_config = list(filter(str, valuefile_config.split(".")))
    attr = config.getattr(valuefile_config, raw=False)
    if not attr:
        return args
    for values in utils.load_config(filename=attr):
        config.update_values(
            utils.pickitems(
                values,
                pickname=valuefile_pickname,
                excludes=valuefile_excludes))
    # force args overrides prog_config
    parser = config.argument_parser(subcommands=subcommands, )
    args = parser.parse_args(arguments)
    config.update_values_by_arguments(args, subcommands=subcommands)
    return args


@operator
def update_values(config, values):
    for name in values:
        attr = config.getattr(name, raw=True)
        if isinstance(attr, Config):
            if not isinstance(values[name], dict):
                raise ValueError(
                    "'values[{}]' == '{}' is not instance of 'dict'".format(
                        name, values[name]))
            attr.update_values(values[name])
        elif isinstance(attr, Options):
            config.setattr(name, values[name], raw=False)


@operator
def dump_config(config,
                filename="",
                filename_config="config.dump",
                exit=True,
                ignores=["config"],
                dumpname=""):
    if not filename and filename_config:
        filename_config = list(filter(str, filename_config.split(".")))
        filename = config.getattr(filename_config, raw=False)
    if not filename:
        raise ValueError("no filename specified")
    values = config.values()
    values = {
        key: value
        for key, value in values.items() if key not in ignores
    }
    if dumpname:
        values = {dumpname: values}
    utils.dump_config(values, filename=filename)
    if exit:
        sys.exit(0)


@operator
def normalize_subcommands(subcommands):
    if isinstance(subcommands, dict):
        return subcommands
    elif isinstance(subcommands, list) or isinstance(subcommands, tuple):
        return {name: True for name in subcommands}
    return {}
