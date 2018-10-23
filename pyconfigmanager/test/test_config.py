import unittest
from pyconfigmanager.config import Config
from pyconfigmanager import errors
from pyconfigmanager import utils
from pyconfigmanager import options
import os
import tempfile


class TestConfig(unittest.TestCase):
    def test_init(self):
        config = Config(12)
        self.assertIsInstance(config, Config)
        self.assertEqual(config._type_, "int")
        self.assertEqual(config._value_, 12)

        config = Config([1, 2, 3])
        self.assertIsInstance(config, Config)
        self.assertEqual(config._type_, "list")
        self.assertEqual(config._value_, [1, 2, 3])

        config = Config({"_type_": str, "value": 12})
        self.assertIsInstance(config, Config)
        self.assertEqual(config._type_, "str")
        self.assertEqual(config._value_, None)
        self.assertEqual(config["value"]._value_, 12)
        self.assertIsInstance(config["value"], Config)

        config = Config({"type": "str", "_value_": [1, 2, 3]})
        self.assertIsInstance(config, Config)
        self.assertEqual(config._type_, "list")
        self.assertEqual(config["type"]._value_, "str")
        self.assertEqual(config._value_, [1, 2, 3])
        self.assertIsInstance(config["type"], Config)

        config = Config({"a": 1, "b": 2})
        config = Config(schema=config)
        self.assertIsInstance(config, Config)
        self.assertEqual(config._type_, "pyconfigmanager.config.Config")
        self.assertEqual(config._value_.a, 1)
        self.assertEqual(config._value_.b, 2)

        config = Config({
            "type": "str",
            "value": 12,
            "none": None,
            "item": {
                "_type_": "str",
                "value": 123,
                "max": 1000,
            },
            "sub": {
                "a": {
                    "c": 12,
                    "d": [1, 2, 3],
                    "e": {
                        "_type_": "int"
                    },
                    "f": {
                        "end": 123
                    },
                },
                "b": "hello",
            },
        })
        self.assertIsInstance(config, Config)

        self.assertIsInstance(config["type"], Config)
        self.assertEqual(config["type"]._type_, "str")
        self.assertEqual(config["type"]._value_, "str")

        self.assertIsInstance(config["value"], Config)
        self.assertEqual(config["value"]._type_, "int")
        self.assertEqual(config["value"]._value_, 12)

        self.assertIsInstance(config["none"], Config)
        self.assertEqual(config["none"]._type_, None)
        self.assertEqual(config["none"]._value_, None)

        self.assertIsInstance(config["item"], Config)
        self.assertEqual(config["item"]._type_, "str")
        self.assertEqual(config["item"]._value_, None)
        self.assertEqual(config["item"]["value"]._value_, 123)
        self.assertEqual(config["item"]["max"]._value_, 1000)

        self.assertIsInstance(config["sub"], Config)
        self.assertIsInstance(config["sub"]["a"], Config)
        self.assertIsInstance(config["sub"]["a"]["c"], Config)
        self.assertEqual(config["sub", "a", "c"]._type_, "int")
        self.assertEqual(config["sub", "a", "c"]._value_, 12)
        self.assertIsInstance(config["sub", "a", "d"], Config)
        self.assertEqual(config["sub", "a", "d"]._type_, "list")
        self.assertEqual(config["sub", "a", "d"]._value_, [1, 2, 3])
        self.assertIsInstance(config["sub", "a", "e"], Config)
        self.assertEqual(config["sub", "a", "e"]._type_, "int")
        self.assertEqual(config["sub", "a", "e"]._value_, None)

        self.assertIsInstance(config["sub", "a", "f"], Config)
        self.assertIsInstance(config["sub", "a", "f", "end"], Config)
        self.assertEqual(config["sub", "a", "f", "end"]._type_, "int")
        self.assertEqual(config["sub", "a", "f", "end"]._value_, 123)

        self.assertIsInstance(config["sub", "b"], Config)
        self.assertEqual(config["sub", "b"]._type_, "str")
        self.assertEqual(config["sub", "b"]._value_, "hello")

    def test_iter(self):
        config = Config({"a": 1, "b": 34})
        result = {}
        for name in config:
            result[name] = getattr(config, name)
        self.assertDictEqual(result, {"a": 1, "b": 34})

    def test_getattr(self):
        config = Config({
            "_type_": "int",
            "_value_": "123",
            "a": 12,
            "b": {
                "c": "12"
            },
            "c": {
                "_value_": "123"
            }
        })
        self.assertEqual(config._type_, "int")
        self.assertEqual(config._value_, 123)
        self.assertEqual(config["a"]._type_, "int")
        self.assertEqual(config["a"]._value_, 12)
        self.assertEqual(config.b._type_, None)
        self.assertEqual(config.b._value_, None)
        self.assertEqual(config.b._max_, None)
        self.assertEqual(config.b["c"]._type_, "str")
        self.assertEqual(config.b.c, "12")
        self.assertEqual(config["c"]._type_, "str")
        self.assertEqual(config.c, "123")
        self.assertRaises(errors.ItemError, getattr, config, "abc")
        config.__class__
        self.assertIsInstance(config._items_, dict)

        self.assertIs(config.__class__, Config)

    def test_setattr(self):
        config = Config({
            "_type_": "int",
            "_value_": "123",
            "_min_": 56,
        })
        self.assertEqual(config._type_, "int")
        self.assertEqual(config._value_, 123)
        self.assertEqual(config._min_, 56)
        self.assertEqual(config._max_, None)
        config._value_ = 456
        self.assertEqual(config._type_, "int")
        self.assertEqual(config._value_, 456)
        self.assertEqual(config._min_, 56)
        self.assertEqual(config._max_, None)
        config._min_ = 500
        self.assertEqual(config._type_, "int")
        self.assertEqual(config._value_, 456)
        self.assertEqual(config._min_, 500)
        self.assertEqual(config._max_, None)
        config._type_ = "str"
        self.assertEqual(config._type_, "str")
        self.assertEqual(config._value_, "456")
        self.assertEqual(config._min_, "500")
        self.assertEqual(config._max_, None)
        self.assertRaises(errors.ItemError, setattr, config, "items", {"a": 1})
        self.assertRaises(errors.AttributeError, setattr, config, "__dict__", {
            "a": 1
        })
        self.assertRaises(errors.ItemError, setattr, config, "abc", 12)
        self.assertRaises(errors.AttributeError, setattr, config, "__dict__", {
            "a": 1
        })
        config._argoptions_ = {"default": 12, "type": int}
        self.assertIsInstance(config._argoptions_, options.ArgumentOptions)
        config._argoptions_ = None
        self.assertIs(config._argoptions_, False)
        config._argoptions_ = "12"
        self.assertIs(config._argoptions_, True)

    def test_delattr(self):
        config = Config({
            "_type_": "int",
            "_value_": "123",
            "_min_": 56,
            "a": 12,
            "b": 34,
        })
        self.assertEqual(config._type_, "int")
        self.assertEqual(config._value_, 123)
        self.assertEqual(config._min_, 56)
        self.assertEqual(len(config._items_), 2)
        delattr(config, "_type_")
        self.assertIs(config._type_, None)
        delattr(config, "_value_")
        self.assertIs(config._value_, None)
        delattr(config, "_min_")
        self.assertIs(config._min_, None)
        delattr(config, "_items_")
        self.assertEqual(len(config._items_), 0)
        config = Config({"a": 12, "b": 34, "_value_": 12})
        del config._schema_
        self.assertEqual(len(config._items_), 0)
        self.assertEqual(config._type_, None)
        self.assertEqual(config._value_, None)

    def test_attrs(self):
        config = Config({
            "_type_": "int",
            "_value_": "123",
            "_min_": 56,
            "a": 12,
            "b": 34,
        })

        self.assertDictEqual(
            config._attrs_,
            {
                '_argoptions_': False,
                '_help_': None,
                '_max_': None,
                '_min_': 56,
                '_required_': None,
                '_type_': 'int',
                '_value_': 123,
            },
        )

    def test_getitem(self):
        config = Config({
            "_value_": 12,
            "a": 1,
            "b": 2,
            "c": {
                "d": 12,
                "e": {
                    "f": {
                        "g": 34
                    }
                }
            }
        })

        self.assertRaises(errors.ItemError, getattr, config, "abcd")
        self.assertRaises(errors.ItemError, config.__getitem__, "abdd")
        self.assertEqual(config.a, 1)
        self.assertEqual(config.b, 2)
        self.assertIsInstance(config["c"], Config)
        self.assertEqual(config.c.d, 12)
        self.assertEqual(config.c["d"]._value_, 12)
        self.assertEqual(config.c.e.f.g, 34)

        self.assertIsInstance(config["a"], Config)
        self.assertEqual(config["a"]._type_, "int")
        self.assertEqual(config["a"]._value_, 1)
        self.assertIsInstance(config["b"], Config)
        self.assertEqual(config["b"]._type_, "int")
        self.assertEqual(config["b"]._value_, 2)
        self.assertIsInstance(config["c"], Config)
        self.assertIsInstance(config.c["d"], Config)
        self.assertEqual(config.c["d"]._type_, "int")
        self.assertEqual(config.c["d"]._value_, 12)
        self.assertIsInstance(config.c.e.f["g"], Config)
        self.assertEqual(config.c.e.f["g"]._type_, "int")
        self.assertEqual(config.c.e.f["g"]._value_, 34)

        self.assertEqual(config["c", "e", "f", "g"]._value_, 34)
        self.assertIsInstance(config[("c", "e", "f", "g")], Config)
        self.assertEqual(config["c", "e", "f", "g"]._value_, 34)
        self.assertIsInstance(config["c", "e"], Config)
        self.assertIsInstance(config["c", "e", "f"], Config)

        self.assertIsInstance(config[()], Config)
        self.assertIs(config[None], config)
        self.assertIs(config[[]], config)
        self.assertEqual(config[None]._value_, 12)

    def test_setitem(self):
        config = Config({"a": 1, "b": 2, "sub": {"c": "hello", "d": 0.9}})
        config["a"] = 12
        self.assertEqual(config.a, 12)
        config["a"] = Config(45)
        self.assertEqual(config.a, 45)
        config["a"] = None
        self.assertEqual(config.a, None)
        config["a"]._type_ = None
        config["a"] = {"a": 1, "b": 2, "_type_": "int"}
        self.assertDictEqual(config.a, {"a": 1, "b": 2, "_type_": "int"})
        config["a"] = Config({"a": 4, "b": 5, "_type_": "int"})
        self.assertEqual(config.a, None)
        config["a"] = Config({"_value_": 12})
        self.assertIsInstance(config["a"], Config)
        self.assertEqual(config["a"]._type_, None)
        self.assertEqual(config.a, 12)
        self.assertRaises(errors.ItemError, config.__setitem__, "subb", 123)
        self.assertRaises(errors.ItemError, config.__setitem__, ["a", "d"], 12)

        config.sub = 124
        self.assertEqual(config.sub._value_, 124)
        self.assertEqual(config.sub._type_, None)
        config.sub.c = 12345
        self.assertEqual(config.sub.c, "12345")

        config["sub"] = "125"
        self.assertEqual(config["sub"]._value_, "125")
        config["sub"]["c"] = 12346
        self.assertEqual(config.sub.c, "12346")

        config[None] = 12
        self.assertEqual(config._value_, 12)
        config["sub"] = "678"
        self.assertEqual(config.sub._value_, "678")
        config["sub", "c"] = "789"
        self.assertEqual(config.sub.c, "789")
        self.assertRaises(errors.ItemError, config.__setitem__,
                          ["sub", "a", "b"], "456")

    def test_delitem(self):
        config = Config({"a": 12, "b": 34})
        self.assertIn("a", config)
        self.assertIn("b", config)
        del config["a"]
        self.assertNotIn("a", config)
        self.assertIn("b", config)
        del config["b"]
        self.assertNotIn("b", config)

    def test_items(self):
        config = Config({"a": 12, "b": 34})
        self.assertIsInstance(config._items_, dict)
        self.assertEqual(len(config._items_), 2)
        self.assertIsInstance(config._items_["a"], Config)
        self.assertEqual(config._items_["a"]._value_, 12)
        self.assertEqual(config._items_["b"]._value_, 34)

    def test_values(self):
        config = Config({
            "a": 12,
            "b": 34,
            "c": {
                "_value_": 12,
                "d": {
                    "e": "hello"
                }
            }
        })
        self.assertDictEqual(config._values_, {
            "a": 12,
            "b": 34,
            "c": {
                "_value_": 12,
                "d": {
                    "e": "hello"
                }
            }
        })

    def test_values_setter(self):
        config = Config({
            "a": 1,
            "b": {
                "c": 2
            },
            "c": None,
            "d": {
                "e": {
                    "f": "hello"
                }
            }
        })

        def raiseerror():
            config._values_ = {"b": {"d": 4}}

        self.assertRaises(errors.ItemError, raiseerror)
        config._values_ = {"c": {"c": 1}, "a": {"c": 1}, "b": 12}
        self.assertDictEqual(config.c, {"c": 1})
        self.assertIs(config.a, None)
        self.assertEqual(config.b._value_, 12)
        config._values_ = {
            "a": 2.34,
            "b": {
                "_value_": 45,
                "c": 5
            },
            "d": {
                "e": {
                    "_value_": 1000,
                    "f": {
                        "g": 12
                    }
                }
            }
        }
        self.assertEqual(config.a, 2)
        self.assertEqual(config.b.c, 5)
        self.assertEqual(config.d.e.f, "{'g': 12}")
        self.assertEqual(config.b._value_, 45)
        self.assertEqual(config.d.e._value_, 1000)

    def test_schema(self):
        config = Config({
            "a": 12,
            "b": 34,
            "c": [1, 2, 3],
            "sub": {
                "d": "hello",
                "f": 12.5,
                "g": {
                    "type": "int"
                },
                "h": {
                    "_type_": "int",
                    "value": 12
                }
            }
        })
        compare_result = {
            "_type_": None,
            "_value_": None,
            "_required_": None,
            "_max_": None,
            "_min_": None,
            "_argoptions_": False,
            "_help_": None,
            "a": {
                "_type_": "int",
                "_value_": 12,
                "_required_": None,
                "_max_": None,
                "_min_": None,
                "_argoptions_": False,
                "_help_": None,
            },
            "b": {
                "_type_": "int",
                "_value_": 34,
                "_required_": None,
                "_max_": None,
                "_min_": None,
                "_argoptions_": False,
                "_help_": None,
            },
            "c": {
                "_type_": "list",
                "_value_": [1, 2, 3],
                "_required_": None,
                "_max_": None,
                "_min_": None,
                "_argoptions_": False,
                "_help_": None,
            },
            "sub": {
                "_type_": None,
                "_value_": None,
                "_required_": None,
                "_max_": None,
                "_min_": None,
                "_argoptions_": False,
                "_help_": None,
                "d": {
                    "_type_": "str",
                    "_value_": "hello",
                    "_required_": None,
                    "_max_": None,
                    "_min_": None,
                    "_argoptions_": False,
                    "_help_": None,
                },
                "f": {
                    "_type_": "float",
                    "_value_": 12.5,
                    "_required_": None,
                    "_max_": None,
                    "_min_": None,
                    "_argoptions_": False,
                    "_help_": None
                },
                "h": {
                    "_type_": "int",
                    "_value_": None,
                    "_required_": None,
                    "_max_": None,
                    "_min_": None,
                    "_argoptions_": False,
                    "_help_": None,
                    "value": {
                        "_type_": "int",
                        "_value_": 12,
                        "_required_": None,
                        "_max_": None,
                        "_min_": None,
                        "_argoptions_": False,
                        "_help_": None,
                    }
                },
                "g": {
                    "_type_": None,
                    "_value_": None,
                    "_required_": None,
                    "_max_": None,
                    "_min_": None,
                    "_argoptions_": False,
                    "_help_": None,
                    "type": {
                        "_type_": "str",
                        "_value_": "int",
                        "_required_": None,
                        "_max_": None,
                        "_min_": None,
                        "_argoptions_": False,
                        "_help_": None,
                    },
                }
            },
        }
        self.maxDiff = None
        schema = config._schema_
        self.assertDictEqual(schema, compare_result)

    def test_schema_setter(self):
        config = Config({"a": 1, "b": 2})
        self.assertEqual(config.a, 1)
        self.assertEqual(config.b, 2)
        self.assertEqual(config["b"]._type_, "int")
        config._schema_ = {"a": {"a": 1}, "b": {"_type_": str, "_value_": 123}}
        self.assertIsInstance(config.a, Config)
        self.assertEqual(config.a.a, 1)
        self.assertEqual(config["b"]._type_, "str")
        self.assertEqual(config.b, "123")
        self.assertEqual(len(config._items_), 2)

        config._schema_ = None
        self.assertEqual(config.a.a, 1)
        self.assertEqual(len(config._items_), 2)
        del config._schema_
        self.assertEqual(len(config._items_), 0)

        config._schema_ = {
            "a": 1,
            "b": 2,
            "c": {
                "_value_": 12,
                "a": 1,
                "b": {
                    "_value_": "hello",
                    "required": True,
                }
            }
        }
        self.assertEqual(config.a, 1)
        self.assertEqual(config.b, 2)
        self.assertEqual(config["b"]._type_, "int")
        self.assertEqual(config["c"]._value_, 12)
        self.assertEqual(config.c.b["required"]._value_, True)
        self.assertEqual(config.c.b._required_, None)
        self.assertEqual(config.c.b._type_, "str")
        config._schema_ = "13"
        self.assertEqual(config._type_, "str")
        self.assertEqual(config._value_, "13")
        self.assertEqual(len(config._items_), 3)
        self.assertEqual(config.c.b["required"]._value_, True)
        config._schema_ = 12
        self.assertEqual(config._type_, "int")
        self.assertEqual(config._value_, 12)
        self.assertEqual(len(config._items_), 3)

        config = Config({
            "a": 1,
            "b": 2,
            "c": {
                "a": 1,
                "b": {
                    "_value_": "hello",
                    "required": True,
                }
            }
        })
        config._schema_ = {
            "a": {
                "_type_": "str"
            },
            "b": {
                "a": 12
            },
            "c": {
                "a": {
                    "d": 1
                },
                "b": 12
            },
            "d": {
                "f": 12
            }
        }
        self.assertIsInstance(config["a"], Config)
        self.assertEqual(config.a, "1")
        self.assertIsInstance(config["b"], Config)
        self.assertIsInstance(config.b["a"], Config)
        self.assertEqual(config.b.a, 12)
        self.assertEqual(config["b"]._value_, 2)
        self.assertIsInstance(config.c.a, Config)
        self.assertEqual(config.c.a.d, 1)
        self.assertEqual(config.c.b["required"]._value_, True)
        self.assertEqual(config.c["b"]._value_, 12)
        self.assertEqual(config.c.b._type_, "int")
        self.assertEqual(config.c["b"]["required"]._value_, True)
        self.assertIsInstance(config.d["f"], Config)
        self.assertEqual(config.d.f, 12)
