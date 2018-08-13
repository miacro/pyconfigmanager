import unittest
from pyconfigmanager.config import Config
from pyconfigmanager.item import Item
from pyconfigmanager import utils
import os
import tempfile


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
        config = Config({
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

        self.assertRaises(AttributeError, config.getattr, "abcd")
        self.assertEqual(config.a, 1)
        self.assertEqual(config.b, 2)
        self.assertIsInstance(config.c, Config)
        self.assertEqual(config.c.d, 12)
        self.assertEqual(config.c.e.f.g, 34)

        self.assertEqual(config.getattr("a", raw=False), 1)
        self.assertEqual(config.getattr("b", raw=False), 2)
        self.assertIsInstance(config.getattr("c", raw=False), Config)
        self.assertEqual(config.c.getattr("d", raw=False), 12)
        self.assertEqual(config.c.e.f.getattr("g", raw=False), 34)

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
        self.assertIsInstance(config.c.e.f.getattr("g", raw=True), Item)
        self.assertEqual(config.c.e.f.getattr("g", raw=True).type, "int")
        self.assertEqual(config.c.e.f.getattr("g", raw=True).value, 34)

        self.assertEqual(config.getattr("a", raw=False, name_slicer="."), 1)
        self.assertEqual(
            config.getattr("c.e.f.g", raw=False, name_slicer="."), 34)
        self.assertEqual(
            config.getattr("c_e_f_g", raw=False, name_slicer="_"), 34)
        self.assertIsInstance(
            config.getattr("c.e.f.g", raw=True, name_slicer="."), Item)
        self.assertEqual(
            config.getattr("c.e.f.g", raw=True, name_slicer=".").value, 34)

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

    def test_values(self):
        config = Config({"a": 12, "b": 34, "c": {"d": {"e": "hello"}}})
        values = config.values()
        self.assertDictEqual(values, {
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
                "$argparse": None,
                "$help": None,
            },
            "b": {
                "$type": "int",
                "$value": 34,
                "$required": None,
                "$max": None,
                "$min": None,
                "$argparse": None,
                "$help": None,
            },
            "c": {
                "$type": "list",
                "$value": [1, 2, 3],
                "$required": None,
                "$max": None,
                "$min": None,
                "$argparse": None,
                "$help": None,
            },
            "sub": {
                "d": {
                    "$type": "str",
                    "$value": "hello",
                    "$required": None,
                    "$max": None,
                    "$min": None,
                    "$argparse": None,
                    "$help": None,
                },
                "f": {
                    "$type": "float",
                    "$value": 12.5,
                    "$required": None,
                    "$max": None,
                    "$min": None,
                    "$argparse": None,
                    "$help": None
                },
                "h": {
                    "$type": "int",
                    "$value": 12,
                    "$required": None,
                    "$max": None,
                    "$min": None,
                    "$argparse": None,
                    "$help": None,
                },
                "g": {
                    "type": {
                        "$type": "str",
                        "$value": "int",
                        "$required": None,
                        "$max": None,
                        "$min": None,
                        "$argparse": None,
                        "$help": None,
                    },
                }
            },
        }
        self.maxDiff = None
        schema = config.schema()
        self.assertDictEqual(schema, compare_result)
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
                },
                "d": {
                    "f": 12
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
        self.assertIsInstance(config.d.getattr("f", raw=True), Item)
        self.assertEqual(config.d.f, 12)

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
            command_name="subcommand")
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
            command_name="subcommand")
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
            command_name="subcommand")
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
                        "$type": list,
                        "argparse": {
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
                        "$type": list,
                        "argparse": {
                            "nargs": 2
                        }
                    }
                }
            }
        })
        parser = config.argument_parser()
        args = parser.parse_args(["--c-d-e", "1", "2"])
        self.assertEqual(args.c_d_e, ["1", "2"])

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
            subcommands=("a", "b"), command_name="subcommand")
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
        self.assertEqual(config.command, "d")
