from .utils import typename, locate_type, convert_type


class BasicItem():
    def __init__(self, names=[], **kwargs):
        for name in names:
            super().__setattr__(name, None)
        self.update_values(kwargs)

    def __setattr__(self, name, value):
        if not hasattr(self, name):
            raise AttributeError("'{}' object has no attribute '{}'".format(
                type(self).__name__, name))
        return super().__setattr__(name, value)

    def __repr__(self):
        return str(vars(self))

    def update_values(self, values, merge=False):
        for name in values:
            if (not merge) or (values[name] is not None):
                setattr(self, name, values[name])


class ArgparseItem(BasicItem):
    def __init__(self, **kwargs):
        super().__init__([
            "nargs",
            "const",
            "default",
            "type",
            "choices",
            "required",
            "help",
            "metavar",
            "dest",
            "action",
        ], **kwargs)


class Item(BasicItem):
    def __init__(self, **kwargs):
        super().__init__(
            ["type", "value", "required", "min", "max", "argparse"], **kwargs)

    def __setattr__(self, name, value):
        if name == "argparse":
            if isinstance(value, ArgparseItem):
                pass
            elif isinstance(value, dict):
                value = ArgparseItem(**value)
            else:
                value = bool(value)
        if name == "type" and value is not None:
            if isinstance(value, type):
                value = typename(value)
            else:
                value = str(value)
            if self.value is not None:
                super().__setattr__("value", convert_type(self.value, value))
            if self.max is not None:
                super().__setattr__("max", convert_type(self.max, value))
            if self.min is not None:
                super().__setattr__("min", convert_type(self.min, value))

        if name == "max" or name == "min" or name == "value":
            if self.type is not None and value is not None:
                value = convert_type(value, self.type)

        return super().__setattr__(name, value)

    def argparse_options(self):
        argparseitem = ArgparseItem(
            type=self.type, default=self.value, help=" ")
        options = vars(argparseitem)

        if isinstance(self.argparse, ArgparseItem):
            options.update({
                key: value
                for key, value in vars(self.argparse).items()
                if value is not None
            })
        if self.type:
            if issubclass(locate_type(self.type), list):
                options["nargs"] = "*"
                options["type"] = None
                if isinstance(self.argparse, ArgparseItem):
                    if self.argparse.nargs is not None:
                        options["nargs"] = self.argparse.nargs
                    if self.argparse.type is not None:
                        options["type"] = self.argparse.type
            elif issubclass(locate_type(self.type), bool):
                options["type"] = str2bool
                if isinstance(self.argparse, ArgparseItem):
                    if self.argparse.type is not None:
                        options["type"] = self.argparse.type

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
        return options

    def assert_value(self, item=None):
        if item is None:
            item = self
        else:
            if not isinstance(item, Item):
                item = Item(**item)
        class_name = type(item).__name__
        if item.required:
            assert self.value is not None, (
                "'{}' object: attribute 'value' required".format(class_name))
        if item.type is not None:
            assert isinstance(self.value, locate_type(item.type)), (
                "'{}' object: attribute 'value': '{}' is not type '{}'".format(
                    class_name, self.value, item.type))
        if item.min is not None:
            assert self.value >= item.min, (
                "'{}' object: attribute 'value': '{}' required >= {}".format(
                    class_name, self.value, item.min))
        if item.max is not None:
            assert self.value <= item.max, (
                "'{}' object: attribute 'value': '{}' required <= {}".format(
                    class_name, self.value, item.max))


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
