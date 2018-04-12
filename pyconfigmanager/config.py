from .item import Item
from .utils import typename


class Config():
    ITEM_INDICATOR = "$"

    def __init__(self, schema={}):
        for name, value in schema.items():
            item = Config(value)
            super().__setattr__(name, item)

    def __new__(self, schema={}):
        if isinstance(schema, dict):
            if any([
                    True if key[:1] == Config.ITEM_INDICATOR else False
                    for key in schema
            ]):
                schema = {(key[1:]
                           if key[:1] == Config.ITEM_INDICATOR else key): value
                          for key, value in schema.items()}
            else:
                return super().__new__(self)
        else:
            schema = {"value": schema}
        if (("value" in schema) and (schema["value"] is not None)):
            if (("type" not in schema) or (schema["type"] is None)):
                schema["type"] = typename(type(schema["value"]))
        return Item(**schema)

    def __iter__(self):
        for name in self.__dict__:
            yield name

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
        attr = super().__getattribute__(name)
        if (not raw) and isinstance(attr, Item):
            return attr.value
        return attr

    def setattr(self, name, value, raw=False):
        pass

    def items(self):
        result = []
        for name in self:
            result.append((name, self.getattr(name)))
        return result

    def schema(self, name=None):
        if name is None:
            name = self.__dict__.keys()
        if isinstance(name, list):
            result = {}
            for name_item in name:
                result[name_item] = self.schema(name_item)
            return result
        attr = super().__getattribute__(name)
        if isinstance(attr, Item):
            return {
                "{}{}".format(Config.ITEM_INDICATOR, key): value
                for key, value in vars(attr).items()
            }
        elif isinstance(attr, Config):
            return attr.schema()
