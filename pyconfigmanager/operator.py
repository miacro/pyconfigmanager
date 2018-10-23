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
        if not isinstance(config, Config):
            raise errors.TypeError("argument '{}' not instance of '{}'".format(
                config, Config.__name__))
        func(config, *args, **kwargs)

    return operate


@operator
def assert_value(config, schema=None, recursive=True, nameprefix=""):
    def isattrname(name):
        return len(name) > 2 and name[0:1] == "_" and name[-1:] == "_"

    def assert_item(item, schema, nameprefix=""):
        if schema is None:
            checker = item
        elif not isinstance(schema, Config):
            checker = Config({
                name: value
                for name, value in schema.items() if isattrname(name)
            })
        else:
            checker = schema

        value = config._value_
        if nameprefix:
            message = "Item '{}': value ".format(nameprefix)
        else:
            message = "Item value "
        if checker._required_:
            assert value is not None, message + "required"
        if checker._type_ is not None:
            assert isinstance(value, utils.locate_type(checker._type_)), (
                message +
                "'{}' not instance of '{}'".format(value, checker._type_))
        if checker._min_ is not None:
            assert value >= checker._min_, (
                message + "'{}' required >= {}".format(value, checker._min_))
        if checker._max_ is not None:
            assert value <= checker._max_, (
                message + "'{}' required <= {}".format(value, checker._max_))

    if not schema:
        if recursive:
            schema = config._schema_
        else:
            schema = config._attrs_
    assert_item(config, schema=schema, nameprefix=nameprefix)
    if not recursive:
        return
    for item_name in schema:
        if isattrname(item_name):
            continue
        if not schema[item_name]:
            continue
        if nameprefix:
            nameprefix = "{}.{}".format(nameprefix, item_name)
        assert item_name in config, (
            "'Config' object has no item '{}'".format(nameprefix))
        item = config[item_name]
        if isinstance(schema[item_name], dict):
            assert_value(
                item,
                schema=schema[item_name],
                recursive=recursive,
                nameprefix=nameprefix)


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
