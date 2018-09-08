from .utils import typename, locate_type, convert_type


class BasicOptions():
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


class ArgumentOptions(BasicOptions):
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
            "position",
            "short",
        ], **kwargs)


class Options(BasicOptions):
    def __init__(self, **kwargs):
        super().__init__(
            ["type", "value", "required", "min", "max", "help", "argoptions"],
            **kwargs)

    def __setattr__(self, name, value):
        if name == "argoptions":
            if isinstance(value, ArgumentOptions):
                pass
            elif isinstance(value, dict):
                value = ArgumentOptions(**value)
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

    def argument_options(self):
        argoptions = ArgumentOptions(
            type=self.type, default=self.value, help=self.help or " ")
        options = vars(argoptions)

        if isinstance(self.argoptions, ArgumentOptions):
            options.update({
                key: value
                for key, value in vars(self.argoptions).items()
                if value is not None
            })
        if self.type:
            if issubclass(locate_type(self.type), list):
                options["nargs"] = "*"
                options["type"] = None
                if isinstance(self.argoptions, ArgumentOptions):
                    if self.argoptions.nargs is not None:
                        options["nargs"] = self.argoptions.nargs
                    if self.argoptions.type is not None:
                        options["type"] = self.argoptions.type
            elif issubclass(locate_type(self.type), bool):
                options["type"] = str2bool
                if isinstance(self.argoptions, ArgumentOptions):
                    if self.argoptions.type is not None:
                        options["type"] = self.argoptions.type

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

    def assert_value(self, options=None):
        if options is None:
            options = self
        else:
            if not isinstance(options, Options):
                options = Options(**options)
        class_name = type(options).__name__
        if options.required:
            assert self.value is not None, (
                "'{}' object: attribute 'value' required".format(class_name))
        if options.type is not None:
            assert isinstance(self.value, locate_type(options.type)), (
                "'{}' object: attribute 'value': '{}' is not type '{}'".format(
                    class_name, self.value, options.type))
        if options.min is not None:
            assert self.value >= options.min, (
                "'{}' object: attribute 'value': '{}' required >= {}".format(
                    class_name, self.value, options.min))
        if options.max is not None:
            assert self.value <= options.max, (
                "'{}' object: attribute 'value': '{}' required <= {}".format(
                    class_name, self.value, options.max))


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
