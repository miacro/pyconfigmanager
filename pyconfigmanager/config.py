from .item import Item
from .utils import typename


class Config():
    ITEM_INDICATOR = "$"

    def __init__(self, schema={}):
        if not isinstance(schema, dict):
            raise ValueError("schema('{}') must be instance of dict".format(
                typename(type(schema))))
        self.update_schema(schema=schema, merge=False)

    def __new__(self, schema={}):
        if isinstance(schema, Item):
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
        if not raw:
            attr = self.getattr(name, raw=True)
            if (isinstance(attr, Item)):
                attr.value = value
            else:
                raise AttributeError("{} {} {}".format(
                    "only value of 'Item' attribute can be updated",
                    "when raw=False,", "while attribute: '{}'".format(
                        type(attr).__name__)))
        else:
            if isinstance(value, Item) or isinstance(value, Config):
                attr_value = value
            else:
                attr_value = Config(value)
            return super().__setattr__(name, attr_value)

    def items(self):
        result = []
        for name in self:
            result.append((name, self.getattr(name, raw=False)))
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
        if isinstance(attr, Item):
            return {
                "{}{}".format(Config.ITEM_INDICATOR, key): value
                for key, value in vars(attr).items()
            }
        elif isinstance(attr, Config):
            return attr.schema()

    def update_schema(self, schema={}, merge=True):
        for name in schema:
            if not merge:
                self.setattr(name, schema[name], raw=True)
                continue
            if schema[name] is None:
                continue
            attr = self.getattr(name, raw=True)
            new_attr = Config.__new__(Config, schema[name])
            if isinstance(attr, Item) and isinstance(new_attr, Item):
                attr.update_values(attr, vars(new_attr))
            elif isinstance(attr, Item) and isinstance(new_attr, Config):
                self.setattr(name, schema[name], raw=True)
            elif isinstance(attr, Config) and isinstance(new_attr, Item):
                self.setattr(name, schema[name], raw=True)
            elif isinstance(attr, Config) and isinstance(new_attr, Config):
                attr.update_schema(schema[name], merge=merge)
            else:
                self.setattr(name, schema[name], raw=True)
