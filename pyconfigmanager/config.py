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
