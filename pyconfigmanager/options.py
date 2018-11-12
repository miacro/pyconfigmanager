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
            "command",
        ], **kwargs)


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
