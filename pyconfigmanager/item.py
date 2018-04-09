from .utils import typename, locate_type


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

    def update_values(self, values):
        for name in values:
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
            if isinstance(value, dict):
                value = ArgparseItem(**value)
            else:
                value = bool(value)
        if name == "type" and value is not None:
            if isinstance(value, type):
                value = typename(value)
            else:
                value = str(value)

        if hasattr(self, "type") and self.type is not None:
            value_type = locate_type(self.type)
            if name == "value" or name == "min" or name == "max":
                if not isinstance(value, value_type):
                    value = value_type(value)
        return super().__setattr__(name, value)

    def get_argparse_options(self):
        argparseitem = ArgparseItem(
            type=self.type, default=self.value, help=" ")
        options = vars(argparseitem)

        if isinstance(self.argparse, ArgparseItem):
            options.update({
                key: value
                for key, value in vars(self.argparse).items()
                if value is not None
            })
        return options

    def assert_value(self):
        class_name = type(self).__name__
        if self.required:
            assert self.value is not None, (
                "'{}' object: value required".format(class_name))
        if self.type is not None:
            assert isinstance(self.value, locate_type(self.type)), (
                "'{}' object: value '{}' is not type '{}'".format(
                    class_name, self.value, self.type))
        if self.min is not None:
            assert self.value >= self.min, (
                "'{}' object: value '{}' required >= {}".format(
                    class_name, self.value, self.min))
        if self.max is not None:
            assert self.value <= self.max, (
                "'{}' object: value '{}' required <= {}".format(
                    class_name, self.value, self.max))
