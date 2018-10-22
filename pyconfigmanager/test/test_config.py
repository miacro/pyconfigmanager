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
        self.assertEqual(config["value"], 12)
        self.assertIsInstance(config.getitem("value", raw=True), Config)

        config = Config({"type": "str", "_value_": [1, 2, 3]})
        self.assertIsInstance(config, Config)
        self.assertEqual(config._type_, "list")
        self.assertEqual(config["type"], "str")
        self.assertEqual(config._value_, [1, 2, 3])
        self.assertIsInstance(config.getitem("type", raw=True), Config)

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

        self.assertIsInstance(config.getitem("type", raw=True), Config)
        self.assertEqual(config.getitem("type", raw=True)._type_, "str")
        self.assertEqual(config.getitem("type", raw=True)._value_, "str")

        self.assertIsInstance(config.getitem("value", raw=True), Config)
        self.assertEqual(config.getitem("value", raw=True)._type_, "int")
        self.assertEqual(config.getitem("value", raw=True)._value_, 12)

        self.assertIsInstance(config.getitem("none", raw=True), Config)
        self.assertEqual(config.getitem("none", raw=True)._type_, None)
        self.assertEqual(config.getitem("none", raw=True)._value_, None)

        self.assertIsInstance(config.getitem("item", raw=True), Config)
        self.assertEqual(config.getitem("item", raw=True)._type_, "str")
        self.assertEqual(config.getitem("item", raw=True)._value_, None)
        self.assertEqual(config.getitem("item", raw=True)["value"], 123)
        self.assertEqual(config.getitem("item", raw=True)["max"], 1000)

        self.assertIsInstance(config.getitem("sub", raw=True), Config)
        self.assertIsInstance(
            config.getitem("sub", raw=True).getitem("a", raw=True), Config)
        self.assertIsInstance(
            config.getitem("sub", raw=True).getitem("a", raw=True).getitem(
                "c", raw=True), Config)
        self.assertEqual(
            config.getitem(["sub", "a", "c"], raw=True)._type_, "int")
        self.assertEqual(config.getitem(["sub", "a", "c"], raw=False), 12)
        self.assertIsInstance(
            config.getitem(["sub", "a", "d"], raw=True), Config)
        self.assertEqual(
            config.getitem(["sub", "a", "d"], raw=True)._type_, "list")
        self.assertEqual(config.getitem(["sub", "a", "d"]), [1, 2, 3])
        self.assertIsInstance(
            config.getitem(["sub", "a", "e"], raw=True), Config)
        self.assertEqual(
            config.getitem(["sub", "a", "e"], raw=True)._type_, "int")
        self.assertEqual(config.getitem(["sub", "a", "e"]), None)

        self.assertIsInstance(
            config.getitem(["sub", "a", "f"], raw=True), Config)
        self.assertIsInstance(
            config.getitem(["sub", "a", "f", "end"], raw=True), Config)
        self.assertEqual(
            config.getitem(["sub", "a", "f", "end"], raw=True)._type_, "int")
        self.assertEqual(config.getitem(["sub", "a", "f", "end"]), 123)

        self.assertIsInstance(config.getitem(["sub", "b"], raw=True), Config)
        self.assertEqual(config.getitem(["sub", "b"], raw=True)._type_, "str")
        self.assertEqual(config.getitem(["sub", "b"]), "hello")

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
        self.assertEqual(config.getitem("a", raw=True)._type_, "int")
        self.assertEqual(config.getitem("a", raw=True)._value_, 12)
        self.assertEqual(config.b._type_, None)
        self.assertEqual(config.b._value_, None)
        self.assertEqual(config.b._max_, None)
        self.assertEqual(config.b.getitem("c", raw=True)._type_, "str")
        self.assertEqual(config.b.c, "12")
        self.assertEqual(config.getitem("c", raw=True)._type_, "str")
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
        self.assertRaises(errors.ItemError, config.getitem, "abdd")
        self.assertEqual(config.a, 1)
        self.assertEqual(config.b, 2)
        self.assertIsInstance(config.getitem("c", raw=True), Config)
        self.assertEqual(config.c.d, 12)
        self.assertEqual(config.c.e.f.g, 34)
        self.assertEqual(config["a"], 1)
        self.assertEqual(config["b"], 2)
        self.assertEqual(config["c"]["d"], 12)
        self.assertEqual(config["c"]["e"]["f"]["g"], 34)

        self.assertEqual(config.getitem("a", raw=False), 1)
        self.assertEqual(config.getitem("b", raw=False), 2)
        self.assertIsInstance(config.getitem("c", raw=True), Config)
        self.assertEqual(config.c.getitem("d", raw=False), 12)
        self.assertEqual(config.c.e.f.getitem("g", raw=False), 34)

        self.assertIsInstance(config.getitem("a", raw=True), Config)
        self.assertEqual(config.getitem("a", raw=True)._type_, "int")
        self.assertEqual(config.getitem("a", raw=True)._value_, 1)
        self.assertIsInstance(config.getitem("b", raw=True), Config)
        self.assertEqual(config.getitem("b", raw=True)._type_, "int")
        self.assertEqual(config.getitem("b", raw=True)._value_, 2)
        self.assertIsInstance(config.getitem("c", raw=True), Config)
        self.assertIsInstance(config.c.getitem("d", raw=True), Config)
        self.assertEqual(config.c.getitem("d", raw=True)._type_, "int")
        self.assertEqual(config.c.getitem("d", raw=True)._value_, 12)
        self.assertIsInstance(config.c.e.f.getitem("g", raw=True), Config)
        self.assertEqual(config.c.e.f.getitem("g", raw=True)._type_, "int")
        self.assertEqual(config.c.e.f.getitem("g", raw=None), 34)

        self.assertEqual(config.getitem("a", raw=None), 1)
        self.assertEqual(config.getitem(["c", "e", "f", "g"]), 34)
        self.assertIsInstance(
            config.getitem(("c", "e", "f", "g"), raw=True), Config)
        self.assertEqual(
            config.getitem(("c", "e", "f", "g"), raw=True)._value_, 34)
        self.assertIsInstance(config.getitem(["c", "e"]), Config)
        self.assertIsInstance(
            config.getitem(["c", "e", "f"], raw=None), Config)

        self.assertIsInstance(config.getitem([]), Config)
        self.assertIs(config.getitem(None), config)
        self.assertIs(config.getitem([], raw=True), config)
        self.assertEqual(config.getitem([], raw=False), 12)

    def test_setitem(self):
        config = Config({"a": 1, "b": 2, "sub": {"c": "hello", "d": 0.9}})
        config.setitem("a", 12, raw=False)
        self.assertEqual(config.a, 12)
        config.setitem("a", "45", raw=False)
        self.assertEqual(config.a, 45)
        config.setitem("a", None, raw=False)
        self.assertEqual(config.a, None)
        config.getitem("a", raw=True)._type_ = None
        config.setitem("a", {"a": 1, "b": 2, "_type_": "int"}, raw=False)
        self.assertDictEqual(config.a, {"a": 1, "b": 2, "_type_": "int"})
        config.setitem("a", Config({"_value_": 12}), raw=False)
        self.assertIsInstance(config.getitem("a", raw=True), Config)
        self.assertEqual(config.getitem("a", raw=True)._type_, None)
        self.assertEqual(config.a, 12)
        self.assertRaises(
            errors.ItemError, config.setitem, "subb", 123, raw=False)
        self.assertRaises(
            errors.ItemError, config.setitem, ["a", "d"], 12, raw=False)

        config.setitem("a", "123", raw=True)
        self.assertIsInstance(config.getitem("a", raw=True), Config)
        self.assertEqual(config.a, "123")
        config.setitem("a", {"a": 12, "b": 34}, raw=True)
        self.assertIsInstance(config.a, Config)
        self.assertIsInstance(config.a.getitem("a", raw=True), Config)
        self.assertEqual(config.a.a, 12)
        self.assertIsInstance(config.a.getitem("b", raw=True), Config)
        self.assertEqual(config.a.b, 34)
        config.setitem("sub", {"a": 12, "b": 34}, raw=True)
        self.assertIsInstance(config.sub, Config)
        self.assertIsInstance(config.sub.getitem("a", raw=True), Config)
        self.assertEqual(config.sub.a, 12)
        self.assertIsInstance(config.sub.getitem("b", raw=True), Config)
        self.assertEqual(config.sub.b, 34)
        self.assertRaises(
            errors.ItemError,
            config.setitem, ["sub", "b", "c", "d"],
            34,
            raw=True)
        config.setitem(["sub", "b", "c"], 12, raw=True)
        self.assertEqual(config.sub.b.c, 12)

        config.sub = 124
        self.assertEqual(config.getitem("sub", raw=False), 124)
        self.assertEqual(config.sub._value_, 124)
        self.assertEqual(config.sub._type_, None)
        config.sub.a = "12345"
        self.assertEqual(config.sub.a, 12345)

        config["sub"] = "125"
        self.assertEqual(config.getitem("sub", raw=False), "125")
        config["sub"]["a"] = "12346"
        self.assertEqual(config.sub.a, 12346)

        config.setitem([], 12)
        self.assertEqual(config._value_, 12)
        config.setitem(["sub"], "678")
        self.assertEqual(config.sub._value_, "678")
        config.setitem(["sub", "a"], "789")
        self.assertEqual(config.sub.a, 789)
        self.assertRaises(errors.ItemError, config.setitem, ["sub", "a", "b"],
                          "456")

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
        config = Config({"a": 12, "b": 34, "c": {"d": {"e": "hello"}}})
        self.assertDictEqual(config._values_, {
            "a": 12,
            "b": 34,
            "c": {
                "d": {
                    "e": "hello"
                }
            }
        })

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

    def test_update_schema(self):
        config = Config({"a": 1, "b": 2})
        self.assertEqual(config.a, 1)
        self.assertEqual(config.b, 2)
        self.assertEqual(config.getitem("b", raw=True)._type_, "int")
        config.update_schema(
            {
                "a": {
                    "a": 1
                },
                "b": {
                    "_type_": str,
                    "_value_": 123
                }
            }, merge=False)
        self.assertIsInstance(config.a, Config)
        self.assertEqual(config.a.a, 1)
        self.assertEqual(config.getitem("b", raw=True)._type_, "str")
        self.assertEqual(config.b, "123")
        self.assertEqual(len(config._items_), 2)

        config.update_schema(None, merge=True)
        self.assertEqual(config.a.a, 1)
        self.assertEqual(len(config._items_), 2)
        config.update_schema(None, merge=False)
        self.assertEqual(len(config._items_), 0)

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
        self.assertEqual(config.a, 1)
        self.assertEqual(config.b, 2)
        self.assertEqual(config.getitem("b", raw=True)._type_, "int")
        self.assertEqual(config.c.b["required"], True)
        self.assertEqual(config.c.b._required_, None)
        self.assertEqual(config.c.b._type_, "str")
        config.update_schema("13", merge=True)
        self.assertEqual(config._type_, "str")
        self.assertEqual(config._value_, "13")
        self.assertEqual(len(config._items_), 3)
        self.assertEqual(config.c.b["required"], True)
        config.update_schema(12, merge=False)
        self.assertEqual(config._type_, "int")
        self.assertEqual(config._value_, 12)
        self.assertEqual(len(config._items_), 0)

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
        config.update_schema(
            {
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
            },
            merge=True)
        self.assertIsInstance(config.getitem("a", raw=True), Config)
        self.assertEqual(config.a, "1")
        self.assertIsInstance(config.getitem("b", raw=True), Config)
        self.assertIsInstance(config.b.getitem("a", raw=True), Config)
        self.assertEqual(config.b.a, 12)
        self.assertEqual(config.getitem("b", raw=False), 2)
        self.assertIsInstance(config.c.a, Config)
        self.assertEqual(config.c.a.d, 1)
        self.assertEqual(config.c.b["required"], True)
        self.assertEqual(config.c.getitem("b", raw=False), 12)
        self.assertEqual(config.c.b._type_, "int")
        self.assertEqual(config.c.getitem("b", raw=True)["required"], True)
        self.assertIsInstance(config.d.getitem("f", raw=True), Config)
        self.assertEqual(config.d.f, 12)

    def test_assert_values(self):
        config = Config({
            "a": 12,
            "b": {
                "_type_": int,
                "_value_": "123",
                "_max_": 12
            }
        })
        self.assertRaises(AssertionError, config.assert_values)
        self.assertRaises(AssertionError, config.assert_values, {
            "a": {
                "b": {
                    "_max_": 12
                }
            }
        })
        self.assertRaises(AssertionError, config.assert_values, {
            "a": {
                "b": {
                    "_min_": 345
                }
            }
        })
        self.assertRaises(AssertionError, config.assert_values, {
            "a": {
                "b": {
                    "_type_": "str"
                }
            }
        })
        config = Config({
            "a": {
                "b": {
                    "c": {
                        "_value_": None,
                        "_required_": True
                    }
                }
            }
        })
        self.assertRaises(AssertionError, config.assert_values)
        config.a.b.getitem(
            "c", raw=True).assert_value(schema={
                "_required_": False
            })
        config.assert_values(schema={"a": True})
        self.assertRaises(AssertionError, config.assert_values, {
            "a": True,
            "b": True
        })
        config.assert_values(schema={"a": {"b": True}})
        self.assertRaises(
            AssertionError,
            config.assert_values,
            schema={
                "a": {
                    "b": {
                        "c": {
                            "_required_": True
                        }
                    }
                }
            })
        config.assert_values(schema={"a": {"b": 12}})
        config.assert_values(schema={"a": {"b": {"c": "haha"}}})
        self.assertRaises(
            AssertionError,
            config.assert_values,
            schema={
                "a": {
                    "b": {
                        "c": {
                            "d": 12
                        }
                    }
                }
            })
        config = Config({
            "a": {
                "b": {
                    "c": {
                        "_value_": None,
                        "_required_": None
                    }
                }
            }
        })
        self.assertRaises(
            AssertionError,
            config.assert_values,
            schema={
                "a": {
                    "b": {
                        "c": {
                            "_required_": True
                        }
                    }
                }
            })
        self.assertRaises(
            AssertionError,
            config.assert_values,
            schema={
                "a": {
                    "_required_": True
                }
            })


"""
    def test_update_value_by_argument(self):
        config = Config({"a": 12, "b": 13, "c": {"d": {"e": 45}}})
        config.update_value_by_argument(
            argname="a", value=34, ignore_not_found=False)
        self.assertEqual(config.a, 34)
        config.update_value_by_argument(
            argname="b", value="56", ignore_not_found=False)
        self.assertEqual(config.b, 56)
        config.update_value_by_argument(
            argname="c_d_e", value=23454, ignore_not_found=False)
        self.assertEqual(config.c.d.e, 23454)
        self.assertRaises(
            AttributeError,
            config.update_value_by_argument,
            argname="c_d",
            value=12,
            ignore_not_found=False)
        config.update_value_by_argument(
            argname="c_d", value=12, ignore_not_found=True)
        self.assertEqual(config.c.d.e, 23454)
        config.update_value_by_argument(
            argname=["a"], value=34, ignore_not_found=False)
        self.assertEqual(config.a, 34)
        config.update_value_by_argument(
            argname=["c", "d", "e"], value=67, ignore_not_found=False)
        self.assertEqual(config.c.d.e, 67)

        config = Config({"a": {"b": 1}, "a_b": 3})
        config.update_value_by_argument(
            argname="a_b", value=12, ignore_not_found=False)
        self.assertEqual(config.a.b, 1)
        self.assertEqual(config.a_b, 12)

    def test_update_values_by_arguments(self):
        config = Config({"a": 12, "b": 13, "c": {"d": {"e": 45}}})
        config.update_values_by_arguments(
            args={"a": 34,
                  "b": 56,
                  "c_d_e": 12}, ignore_not_found=False)
        self.assertEqual(config.a, 34)
        self.assertEqual(config.b, 56)
        self.assertEqual(config.c.d.e, 12)
        self.assertRaises(
            AttributeError,
            config.update_values_by_arguments,
            args={"a": 12,
                  "b": 34,
                  "c_d": 45},
            ignore_not_found=False)

        config.update_values_by_arguments(
            args={"a": 0,
                  "b": 1,
                  "c_d": 45}, ignore_not_found=True)
        self.assertEqual(config.a, 0)
        self.assertEqual(config.b, 1)
        self.assertEqual(config.c.d.e, 12)

        config = Config({
            "subcommand": "",
            "a": {
                "a": 1,
                "b": 2
            },
            "b": {
                "c": 3,
                "d": 4
            },
            "c": 12,
            "d": 13
        })
        config.update_values_by_arguments(
            args={"subcommand": "a",
                  "a": 10,
                  "b": 20,
                  "c": 120,
                  "d": 130},
            subcommands=("a", "b"),
            command_attrname="subcommand")
        self.assertEqual(config.subcommand, "a")
        self.assertEqual(config.a.a, 10)
        self.assertEqual(config.a.b, 20)
        self.assertEqual(config.c, 120)
        self.assertEqual(config.d, 130)
        self.assertEqual(config.b.c, 3)
        self.assertEqual(config.b.d, 4)
        config.update_values_by_arguments(
            args={"subcommand": "",
                  "a": 11,
                  "b": 21,
                  "c": 12,
                  "d": 13},
            subcommands=("a", "b"),
            command_attrname="subcommand")
        self.assertEqual(config.subcommand, "")
        self.assertEqual(config.a.a, 10)
        self.assertEqual(config.a.b, 20)
        self.assertEqual(config.c, 12)
        self.assertEqual(config.d, 13)
        self.assertEqual(config.b.c, 3)
        self.assertEqual(config.b.d, 4)
        config.update_values_by_arguments(
            args={"subcommand": "b",
                  "a": 110,
                  "b": 210,
                  "c": 120,
                  "d": 130},
            subcommands=("a", "b"),
            command_attrname="subcommand")
        self.assertEqual(config.subcommand, "b")
        self.assertEqual(config.a.a, 10)
        self.assertEqual(config.a.b, 20)
        self.assertEqual(config.c, 12)
        self.assertEqual(config.d, 13)
        self.assertEqual(config.b.c, 120)
        self.assertEqual(config.b.d, 130)

    def test_argument_parser(self):
        config = Config({"a": 1, "b": 2, "c": {"d": {"e": [1, 2, 3]}}})
        parser = config.argument_parser()
        args = parser.parse_args(["--a", "12", "--b", "12"])
        self.assertEqual(args.a, 12)
        self.assertEqual(args.b, 12)
        self.assertEqual(args.c_d_e, [1, 2, 3])
        config.update_values_by_arguments(args=args, ignore_not_found=False)
        self.assertEqual(config.a, 12)
        self.assertEqual(config.b, 12)
        self.assertEqual(config.c.d.e, [1, 2, 3])

        config = Config({"a": 1, "b": 2, "c": {"d": {"e": [1, 2, 3]}}})
        parser = config.argument_parser()
        args = parser.parse_args(
            ["--a", "12", "--b", "12", "--c-d-e", "1", "2", "3"])
        self.assertEqual(args.a, 12)
        self.assertEqual(args.b, 12)
        self.assertEqual(args.c_d_e, ["1", "2", "3"])
        config = Config({
            "c": {
                "d": {
                    "e": {
                        "_type_": list,
                        "argoptions": {
                            "type": int,
                        }
                    }
                }
            }
        })
        parser = config.argument_parser()
        args = parser.parse_args(["--c-d-e", "1", "2", "3"])
        self.assertEqual(args.c_d_e, [1, 2, 3])

        config = Config({
            "c": {
                "d": {
                    "e": {
                        "_type_": list,
                        "argoptions": {
                            "nargs": 2
                        }
                    }
                },
                "f": 12,
            }
        })
        parser = config.argument_parser()
        args = parser.parse_args(["--c-d-e", "1", "2"])
        self.assertEqual(args.c_d_e, ["1", "2"])

        parser = config.argument_parser(subcommands={"c": {"d": True}})
        args = parser.parse_args(["c", "--f", "34", "d", "--e", "45", "23"])
        self.assertEqual(args.e, ["45", "23"])
        self.assertEqual(args.command, "c.d")
        self.assertEqual(args.f, 34)

        config = Config({
            "c": {
                "d": {
                    "e": {
                        "_type_": list,
                        "argoptions": {
                            "nargs": 2
                        }
                    }
                }
            },
            "a": {
                "d": {
                    "e": 24
                }
            }
        })
        parser = config.argument_parser(subcommands={
            "c": {
                "d": True
            },
            "a": {
                "d": True
            }
        })
        args = parser.parse_args(["c", "d", "--e", "45", "23"])
        self.assertEqual(args.e, ["45", "23"])
        args = parser.parse_args(["a", "d", "--e", "78"])
        self.assertEqual(args.e, 78)

        config = Config({
            "subcommand": "",
            "command": "",
            "logging": "INFO",
            "c": 12,
            "d": 13,
            "a": {
                "a": 1,
                "b": 3
            },
            "b": {
                "c": 3,
                "d": 1
            }
        })
        parser = config.argument_parser(
            subcommands=("a", "b"), command_attrname="subcommand")
        args = parser.parse_args([
            "--logging", "DEBUG", "--command", "test", "a", "--a", "100",
            "--b", "200"
        ])
        self.assertDictEqual(
            vars(args), {
                "logging": "DEBUG",
                "a": 100,
                "b": 200,
                "d": 13,
                "c": 12,
                "subcommand": 'a',
                "command": "test",
            })
        args = parser.parse_args(["b", "--c", "34", "--d", "435"])
        self.assertDictEqual(
            vars(args), {
                "logging": "INFO",
                "c": 34,
                "d": 435,
                "subcommand": "b",
                "command": "",
            })

    def test_update_values(self):
        config = Config({"a": 1, "b": {"c": 2}, "d": {"e": {"f": "hello"}}})
        self.assertRaises(
            ValueError, config.update_values, values={
                "a": 2.25,
                "b": 12
            })
        self.assertRaises(AttributeError, config.update_values, {
            "a": 2.34,
            "b": {
                "d": 12
            }
        })
        config.update_values({
            "a": 2.34,
            "b": {
                "c": 5
            },
            "d": {
                "e": {
                    "f": {
                        "g": 12
                    }
                }
            }
        })
        self.assertEqual(config.a, 2)
        self.assertEqual(config.b.c, 5)
        self.assertEqual(config.d.e.f, "{'g': 12}")

    def test_dump_config(self):
        with tempfile.NamedTemporaryFile("wt") as temp_file:
            pass
        jsonfile = "{}.json".format(temp_file.name)
        yamlfile = "{}.yaml".format(temp_file.name)
        config = Config({
            "a": 1,
            "b": 2,
            "c": {
                "d": "123",
                "f": 34
            },
            "config": {
                "file": ""
            },
        })
        self.assertRaises(
            ValueError,
            config.dump_config,
            filename="",
            filename_config="config.file",
            exit=False)
        config.dump_config(filename=jsonfile, exit=False, dumpname="test")
        result = [item for item in utils.load_json(filenames=jsonfile)]
        self.assertListEqual(result, [{
            "test": {
                "a": 1,
                "b": 2,
                "c": {
                    "d": "123",
                    "f": 34
                },
            }
        }])
        config.dump_config(filename=yamlfile, exit=False, dumpname="")
        result = [item for item in utils.load_yaml(filenames=yamlfile)]
        self.assertListEqual(result, [{
            "a": 1,
            "b": 2,
            "c": {
                "d": "123",
                "f": 34
            },
        }])

        config.config.file = yamlfile
        config.dump_config(
            filename_config="config.file", exit=False, dumpname="12")
        result = [item for item in utils.load_yaml(filenames=yamlfile)]
        self.assertListEqual(result, [{
            "12": {
                "a": 1,
                "b": 2,
                "c": {
                    "d": "123",
                    "f": 34
                },
            }
        }])
        os.remove(jsonfile)
        os.remove(yamlfile)

    def test_update_values_by_argument_parser(self):
        filedir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "files")
        configfile = os.path.join(filedir, "2.yaml")
        origin = {
            "a": 1,
            "b": 2,
            "c": {
                "d": "123",
                "f": 34
            },
            "config": {
                "file": ""
            }
        }
        config = Config(origin)
        config.update_values_by_argument_parser(
            arguments=["--a", "23", "--c-d", "hello"], valuefile_config="")
        self.assertEqual(config.a, 23)
        self.assertEqual(config.c.d, "hello")

        config = Config(origin)
        config.update_values_by_argument_parser(
            arguments=[
                "--a", "23", "--c-d", "hell", "--config-file", configfile
            ],
            valuefile_config="config.file",
            valuefile_pickname="test")
        self.assertEqual(config.a, 23)
        self.assertEqual(config.c.d, "hell")
        self.assertEqual(config.b, 34)

        config = Config(origin)
        config.config.file = configfile
        config.update_values_by_argument_parser(
            arguments=["--a", "23", "--c-d", "hell"],
            valuefile_config="config.file",
            valuefile_pickname="test")
        self.assertEqual(config.a, 23)
        self.assertEqual(config.c.d, "hell")
        self.assertEqual(config.b, 34)

        schema = dict(origin.items())
        schema["command"] = ""
        schema["d"] = {"a": 23, "b": 45}
        config = Config(schema)
        config.update_values_by_argument_parser(
            arguments=[
                "--a", "23", "--b", "45", "c", "--d", "345", "--f", "456"
            ],
            valuefile_config="config.file",
            valuefile_pickname="test",
            subcommands=("c", "d"))
        self.assertEqual(config.a, 23)
        self.assertEqual(config.b, 45)
        self.assertEqual(config.c.d, "345")
        self.assertEqual(config.c.f, 456)
        self.assertEqual(config.command, "c")
        config.update_values_by_argument_parser(
            arguments=[
                "--a", "230", "--b", "450", "d", "--a", "345", "--b", "456"
            ],
            valuefile_config="config.file",
            valuefile_pickname="test",
            subcommands=("c", "d"))
        self.assertEqual(config.a, 23)
        self.assertEqual(config.b, 45)
        self.assertEqual(config.c.d, "345")
        self.assertEqual(config.c.f, 456)
        self.assertEqual(config.d.a, 345)
        self.assertEqual(config.d.b, 456)
        self.assertEqual(config.command, "d")
        config.update_values_by_argument_parser(
            arguments=["--a", "230", "--b", "450", "d"],
            valuefile_config="config.file",
            valuefile_pickname="test",
            subcommands=("c", "d"))
        self.assertEqual(config.a, 23)
        self.assertEqual(config.b, 45)
        self.assertEqual(config.c.d, "345")
        self.assertEqual(config.c.f, 456)
        self.assertEqual(config.d.a, 345)
        self.assertEqual(config.d.b, 456)
        self.assertEqual(config.command, "d")
        config.update_values_by_argument_parser(
            arguments=["--a", "230", "--b", "450"],
            valuefile_config="config.file",
            valuefile_pickname="test",
            subcommands=("c", "d"))
        self.assertEqual(config.a, 230)
        self.assertEqual(config.b, 450)
        self.assertEqual(config.c.d, "345")
        self.assertEqual(config.c.f, 456)
        self.assertEqual(config.d.a, 345)
        self.assertEqual(config.d.b, 456)
        self.assertEqual(config.command, None)

        schema = dict(origin.items())
        schema.update({
            "e": {
                "d": 23,
                "f": {
                    "h": "345"
                }
            },
            "g": {
                "d": "qwe",
                "f": {
                    "h": {
                        "i": 567
                    },
                    "d": "rrrr",
                }
            },
            "command": "",
        })
        config = Config(schema)
        subcommands = {"e": {"f": True}, "g": {"f": {"h": True}}}
        config.update_values_by_argument_parser(
            arguments=["e", "--d", "56", "f", "--h", "dddd"],
            subcommands=subcommands)
        self.assertEqual(config.e.d, 56)
        self.assertEqual(config.e.f.h, "dddd")
        self.assertEqual(config.command, "e.f")

        config = Config(schema)
        config.update_values_by_argument_parser(
            arguments=["g", "--d", "567", "f", "h", "--i", "123"],
            subcommands=subcommands)
        self.assertEqual(config.command, "g.f.h")
        self.assertEqual(config.g.f.h.i, 123)
        # value of args.g.f.d reset by the default value of config.g.f.d
        self.assertEqual(config.g.f.d, "rrrr")
        self.assertEqual(config.g.d, "qwe")

        config = Config(schema)
        config.update_values_by_argument_parser(
            arguments=[
                "g", "--d", "567", "f", "--d", "123", "h", "--i", "123"
            ],
            subcommands=subcommands)
        self.assertEqual(config.command, "g.f.h")
        self.assertEqual(config.g.f.h.i, 123)
        self.assertEqual(config.g.f.d, "123")
        self.assertEqual(config.g.d, "qwe")
"""
