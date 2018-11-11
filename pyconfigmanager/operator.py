from .options import ArgumentOptions
from pyconfigmanager import utils
import logging
from .logger import get_logging_level
import argparse
import sys
from . import errors
from .config import Config
from .config import isattrname
from .utils import locate_type


def operator(func):
    def operate(config, *args, **kwargs):
        if not isinstance(config, Config):
            raise errors.TypeError("argument '{}' not instance of '{}'".format(
                config, Config.__name__))
        return func(config, *args, **kwargs)

    return operate


@operator
def assert_values(config, schema=None, nameprefix=""):
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

    if schema is None:
        schema = config._schema_
    elif not isinstance(schema, dict):
        schema = config._attrs_
    assert_item(config, schema=schema, nameprefix=nameprefix)
    for item_name in schema:
        if isattrname(item_name):
            continue
        if not schema[item_name]:
            continue
        if nameprefix:
            showname = "{}.{}".format(nameprefix, item_name)
        else:
            showname = item_name
        assert item_name in config, (
            "'Config' object has no item '{}'".format(showname))
        item = config[item_name]
        if isinstance(schema[item_name], dict):
            assert_values(item, schema=schema[item_name], nameprefix=showname)


@operator
def logging_values(config, schema=None, verbosity="INFO", nameprefix=""):
    if not schema:
        schema = config._schema_
    elif not isinstance(schema, dict):
        schema = {"_value_": schema}

    tolog = False
    if "_value_" in schema:
        if schema["_value_"]:
            tolog = True
    else:
        if config._isleaf_:
            tolog = True
        else:
            if config._value_ is not None:
                tolog = True
    message = "{}: {}".format(nameprefix, config._value_)
    if tolog:
        logging.log(get_logging_level(verbosity), message)
    for item_name in sorted(schema.keys()):
        if isattrname(item_name):
            continue
        if not schema[item_name]:
            continue
        if nameprefix:
            showname = "{}.{}".format(nameprefix, item_name)
        else:
            showname = item_name
        item = config[item_name]
        logging_values(
            item,
            schema=schema[item_name],
            verbosity=verbosity,
            nameprefix=showname)


@operator
def argument_options(config):
    options = ArgumentOptions(
        type=config._type_, default=config._value_, help=config._help_ or " ")
    options = vars(options)

    if options["type"]:
        if issubclass(locate_type(options["type"]), list):
            options["nargs"] = "*"
            options["type"] = None
        elif issubclass(locate_type(options["type"]), bool):
            options["type"] = str2bool

    if isinstance(config._argoptions_, ArgumentOptions):
        options.update({
            key: value
            for key, value in vars(config._argoptions_).items()
            if value is not None
        })

    if options["action"]:
        options["type"] = None
        options["metavar"] = None
        options["choices"] = None
        options["nargs"] = None
        options["const"] = None

    if options["type"]:
        if isinstance(options["type"], str):
            options["type"] = locate_type(options["type"])
    options = {
        key: value
        for key, value in options.items() if value is not None
    }

    results = {"--": options}
    for name in config:
        suboptions = argument_options(config[name])
        for key, value in suboptions.items():
            assert key[0:2] == "--"
            if key != "--":
                key = "--{}-{}".format(name, key[2:])
            else:
                key = "--{}".format(name)
            results[key] = value
    return results


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
def dump_config(config,
                filename="",
                filename_config="config.dump",
                exit=True,
                ignores=["config"],
                dumpname=""):
    if not filename and filename_config:
        filename_config = list(filter(str, filename_config.split(".")))
        filename = config[filename_config]._value_
    if not filename:
        raise ValueError("no filename specified")
    values = config._values_
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


def str2bool(value):
    return value.lower() in (
        'true',
        '1',
        't',
        'y',
        'yes',
        'yeah',
        'yup',
        'certainly',
    )
