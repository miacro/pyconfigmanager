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
        items = sorted(config.items())
        self.assertIsInstance(items, list)
        self.assertIsInstance(items[0], tuple)
        self.assertEqual(items[0][0], "a")
        self.assertEqual(items[0][1], 12)
        self.assertIsInstance(items[1], tuple)
        self.assertEqual(items[1][0], "b")
        self.assertEqual(items[1][1], 34)

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
        # schema = config.schema()
        # self.assertDictEqual(schema["a"], compare_result["a"])
        # self.assertDictEqual(schema["b"], compare_result["b"])
        # self.assertDictEqual(schema["sub"], compare_result["sub"])
        # print(config.schema("a"))
        # self.assertDictEqual(config.schema("a"), compare_result["a"])
        # self.assertDictEqual(
        #     config.schema(["a", "b"]), {
        #         "a": compare_result["a"],
        #         "b": compare_result["b"]
        #     })
