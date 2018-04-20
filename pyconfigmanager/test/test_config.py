import unittest
from pyconfigmanager.config import Config
from pyconfigmanager.item import Item


class TestConfig(unittest.TestCase):
    def test_new(self):
        config = Config(12)
        self.assertIsInstance(config, Item)
        self.assertEqual(config.type, "int")
        self.assertEqual(config.value, 12)

        config = Config([1, 2, 3])
        self.assertIsInstance(config, Item)
        self.assertEqual(config.type, "list")
        self.assertEqual(config.value, [1, 2, 3])

        config = Config({"$type": str, "value": 12})
        self.assertIsInstance(config, Item)
        self.assertEqual(config.type, "str")
        self.assertEqual(config.value, "12")

        config = Config({"type": "str", "$value": [1, 2, 3]})
        self.assertIsInstance(config, Item)
        self.assertEqual(config.type, "str")
        self.assertEqual(config.value, "[1, 2, 3]")

        config = Config({"a": 1, "b": 2})
        config = Config(schema=config)
        self.assertIsInstance(config, Item)
        self.assertEqual(config.type, "pyconfigmanager.config.Config")
        self.assertEqual(config.value.a, 1)
        self.assertEqual(config.value.b, 2)
        item = Item(value=56.8)
        config = Config(item)
        self.assertIsInstance(config, Item)
        self.assertEqual(config.type, "float")
        self.assertEqual(config.value, 56.8)

    def test_init(self):
        config = Config({
            "type": "str",
            "value": 12,
            "none": None,
            "item": {
                "$type": "str",
                "value": 123,
                "max": 1000,
            },
            "sub": {
                "a": {
                    "c": 12,
                    "d": [1, 2, 3],
                    "e": {
                        "$type": "int"
                    },
                    "f": {
                        "end": 123
                    },
                },
                "b": "hello",
            },
        })
        self.assertIsInstance(config, Config)

        self.assertIsInstance(config.getattr("type", raw=True), Item)
        self.assertEqual(config.getattr("type", raw=True).type, "str")
        self.assertEqual(config.getattr("type", raw=True).value, "str")

        self.assertIsInstance(config.getattr("value", raw=True), Item)
        self.assertEqual(config.getattr("value", raw=True).type, "int")
        self.assertEqual(config.getattr("value", raw=True).value, 12)

        self.assertIsInstance(config.getattr("none", raw=True), Item)
        self.assertEqual(config.getattr("none", raw=True).type, None)
        self.assertEqual(config.getattr("none", raw=True).value, None)

        self.assertIsInstance(config.getattr("item", raw=True), Item)
        self.assertEqual(config.getattr("item", raw=True).type, "str")
        self.assertEqual(config.getattr("item", raw=True).value, "123")
        self.assertEqual(config.getattr("item", raw=True).max, "1000")

        self.assertIsInstance(config.sub, Config)
        self.assertIsInstance(config.sub.a, Config)
        self.assertIsInstance(config.sub.a.getattr("c", raw=True), Item)
        self.assertEqual(config.sub.a.getattr("c", raw=True).type, "int")
        self.assertEqual(config.sub.a.getattr("c", raw=True).value, 12)
        self.assertIsInstance(config.sub.a.getattr("d", raw=True), Item)
        self.assertEqual(config.sub.a.getattr("d", raw=True).type, "list")
        self.assertEqual(config.sub.a.getattr("d", raw=True).value, [1, 2, 3])
        self.assertIsInstance(config.sub.a.getattr("e", raw=True), Item)
        self.assertEqual(config.sub.a.getattr("e", raw=True).type, "int")
        self.assertEqual(config.sub.a.getattr("e", raw=True).value, None)

        self.assertIsInstance(config.sub.a.f, Config)
        self.assertIsInstance(config.sub.a.f.getattr("end", raw=True), Item)
        self.assertEqual(config.sub.a.f.getattr("end", raw=True).type, "int")
        self.assertEqual(config.sub.a.f.getattr("end", raw=True).value, 123)

        self.assertIsInstance(config.sub.getattr("b", raw=True), Item)
        self.assertEqual(config.sub.getattr("b", raw=True).type, "str")
        self.assertEqual(config.sub.getattr("b", raw=True).value, "hello")

    def test_iter(self):
        config = Config({"a": 1, "b": 34})
        result = {}
        for name in config:
            result[name] = getattr(config, name)
        self.assertDictEqual(result, {"a": 1, "b": 34})

    def test_getattr(self):
        config = Config({"a": 1, "b": 2, "c": {"d": 12, "e": 34}})

        self.assertRaises(AttributeError, config.getattr, "abcd")
        self.assertEqual(config.a, 1)
        self.assertEqual(config.b, 2)
        self.assertIsInstance(config.c, Config)
        self.assertEqual(config.c.d, 12)
        self.assertEqual(config.c.e, 34)

        self.assertEqual(config.getattr("a", raw=False), 1)
        self.assertEqual(config.getattr("b", raw=False), 2)
        self.assertIsInstance(config.getattr("c", raw=False), Config)
        self.assertEqual(config.c.getattr("d", raw=False), 12)
        self.assertEqual(config.c.getattr("e", raw=False), 34)

        self.assertIsInstance(config.getattr("a", raw=True), Item)
        self.assertEqual(config.getattr("a", raw=True).type, "int")
        self.assertEqual(config.getattr("a", raw=True).value, 1)
        self.assertIsInstance(config.getattr("b", raw=True), Item)
        self.assertEqual(config.getattr("b", raw=True).type, "int")
        self.assertEqual(config.getattr("b", raw=True).value, 2)
        self.assertIsInstance(config.getattr("c", raw=True), Config)
        self.assertIsInstance(config.c.getattr("d", raw=True), Item)
        self.assertEqual(config.c.getattr("d", raw=True).type, "int")
        self.assertEqual(config.c.getattr("d", raw=True).value, 12)
        self.assertIsInstance(config.c.getattr("e", raw=True), Item)
        self.assertEqual(config.c.getattr("e", raw=True).type, "int")
        self.assertEqual(config.c.getattr("e", raw=True).value, 34)

    def test_setattr(self):
        config = Config({"a": 1, "b": 2, "sub": {"c": "hello", "d": 0.9}})
        config.setattr("a", 12, raw=False)
        self.assertEqual(config.a, 12)
        config.setattr("a", "45", raw=False)
        self.assertEqual(config.a, 45)
        config.setattr("a", None, raw=False)
        self.assertEqual(config.a, None)
        config.getattr("a", raw=True).type = None
        config.setattr("a", {"a": 1, "b": 2, "$type": "int"}, raw=False)
        self.assertDictEqual(config.a, {"a": 1, "b": 2, "$type": "int"})
        config.setattr("a", Item(value=12), raw=False)
        self.assertIsInstance(config.a, Item)
        self.assertEqual(config.a.type, None)
        self.assertEqual(config.a.value, 12)
        self.assertRaises(
            AttributeError, config.setattr, "sub", 123, raw=False)

        config.setattr("a", "123", raw=True)
        self.assertIsInstance(config.getattr("a", raw=True), Item)
        self.assertEqual(config.a, "123")
        config.setattr("a", {"a": 12, "b": 34}, raw=True)
        self.assertIsInstance(config.a, Config)
        self.assertIsInstance(config.a.getattr("a", raw=True), Item)
        self.assertEqual(config.a.a, 12)
        self.assertIsInstance(config.a.getattr("b", raw=True), Item)
        self.assertEqual(config.a.b, 34)
        config.setattr("sub", {"a": 12, "b": 34}, raw=True)
        self.assertIsInstance(config.sub, Config)
        self.assertIsInstance(config.sub.getattr("a", raw=True), Item)
        self.assertEqual(config.sub.a, 12)
        self.assertIsInstance(config.sub.getattr("b", raw=True), Item)
        self.assertEqual(config.sub.b, 34)

    def test_getitem(self):
        config = Config({"a": 12, "b": 34})
        self.assertEqual(config["a"], 12)
        self.assertEqual(config["b"], 34)

    def test_setitem(self):
        config = Config({"a": 12, "b": 34})
        config["a"] = 56
        config["b"] = "100"
        self.assertEqual(config.a, 56)
        self.assertEqual(config.b, "100")

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
        items = sorted(config.items(raw=False))
        self.assertIsInstance(items, list)
        self.assertIsInstance(items[0], tuple)
        self.assertEqual(items[0][0], "a")
        self.assertEqual(items[0][1], 12)
        self.assertIsInstance(items[1], tuple)
        self.assertEqual(items[1][0], "b")
        self.assertEqual(items[1][1], 34)

        items = sorted(config.items(raw=True))
        self.assertIsInstance(items, list)
        self.assertIsInstance(items[0], tuple)
        self.assertEqual(items[0][0], "a")
        self.assertEqual(items[0][1].value, 12)
        self.assertIsInstance(items[1], tuple)
        self.assertEqual(items[1][0], "b")
        self.assertEqual(items[1][1].value, 34)

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
                    "$type": "int",
                    "value": 12
                }
            }
        })
        compare_result = {
            "a": {
                "$type": "int",
                "$value": 12,
                "$required": None,
                "$max": None,
                "$min": None,
                "$argparse": None
            },
            "b": {
                "$type": "int",
                "$value": 34,
                "$required": None,
                "$max": None,
                "$min": None,
                "$argparse": None
            },
            "sub": {
                "d": {
                    "$type": "str",
                    "$value": "hello",
                    "$required": None,
                    "$max": None,
                    "$min": None,
                    "$argparse": None
                },
                "f": {
                    "$type": "float",
                    "$value": 12.5,
                    "$required": None,
                    "$max": None,
                    "$min": None,
                    "$argparse": None
                },
                "h": {
                    "$type": "int",
                    "$value": 12,
                    "$required": None,
                    "$max": None,
                    "$min": None,
                    "$argparse": None
                },
                "g": {
                    "type": {
                        "$type": "str",
                        "$value": "int",
                        "$required": None,
                        "$max": None,
                        "$min": None,
                        "$argparse": None
                    },
                }
            },
        }
        schema = config.schema()
        self.assertDictEqual(schema["a"], compare_result["a"])
        self.assertDictEqual(schema["b"], compare_result["b"])
        self.assertDictEqual(schema["sub"], compare_result["sub"])
        self.assertDictEqual(config.schema("a"), compare_result["a"])
        self.assertDictEqual(
            config.schema(["a", "b"]), {
                "a": compare_result["a"],
                "b": compare_result["b"]
            })

    def test_update_schema(self):
        config = Config({"a": 1, "b": 2})
        self.assertEqual(config.a, 1)
        self.assertEqual(config.b, 2)
        self.assertEqual(config.getattr("b", raw=True).type, "int")
        config.update_schema(
            {
                "a": {
                    "a": 1
                },
                "b": {
                    "$type": str,
                    "$value": 123
                }
            }, merge=False)
        self.assertIsInstance(config.a, Config)
        self.assertEqual(config.a.a, 1)
        self.assertEqual(config.getattr("b", raw=True).type, "str")
        self.assertEqual(config.b, "123")
        self.assertEqual(len(config.items()), 2)

        config.update_schema(None, merge=True)
        self.assertEqual(config.a.a, 1)
        self.assertEqual(len(config.items()), 2)
        config.update_schema(None, merge=False)
        self.assertEqual(len(config.items()), 0)

        config = Config({
            "a": 1,
            "b": 2,
            "c": {
                "a": 1,
                "b": {
                    "$value": "hello",
                    "required": True,
                }
            }
        })
        self.assertEqual(config.a, 1)
        self.assertEqual(config.b, 2)
        self.assertEqual(config.getattr("b", raw=True).type, "int")
        self.assertEqual(config.c.getattr("b", raw=True).required, True)
        self.assertRaises(TypeError, config.update_schema, 12, False)
        self.assertRaises(TypeError, config.update_schema, 12, True)

        config.update_schema(
            {
                "a": {
                    "$type": "str"
                },
                "b": {
                    "a": 12
                },
                "c": {
                    "a": {
                        "d": 1
                    },
                    "b": 12
                }
            },
            merge=True)
        self.assertIsInstance(config.getattr("a", raw=True), Item)
        self.assertEqual(config.a, "1")
        self.assertIsInstance(config.getattr("b", raw=True), Config)
        self.assertIsInstance(config.b.getattr("a", raw=True), Item)
        self.assertEqual(config.b.a, 12)
        self.assertIsInstance(config.c.a, Config)
        self.assertEqual(config.c.a.d, 1)
        self.assertEqual(config.c.b, 12)
        self.assertEqual(config.c.getattr("b", raw=True).required, True)

    def test_assert_values(self):
        config = Config({
            "a": 12,
            "b": {
                "$type": int,
                "value": "123",
                "max": 12
            }
        })
        self.assertRaises(AssertionError, config.assert_values)
        config = Config({
            "a": {
                "b": {
                    "c": {
                        "$value": None,
                        "required": True
                    }
                }
            }
        })
        self.assertRaises(AssertionError, config.assert_values)
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
                        "c": True
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
                        "$type": list,
                        "argparse": {
                            "type": int,
                        }
                    }
                }
            }
        })
        args = parser.parse_args(["--c-d-e", "1", "2", "3"])
        self.assertEqual(args.c_d_e, [1, 2, 3])
