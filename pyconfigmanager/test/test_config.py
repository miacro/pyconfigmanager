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

        self.assertIsInstance(config.type, Item)
        self.assertEqual(config.type.type, "str")
        self.assertEqual(config.type.value, "str")

        self.assertIsInstance(config.value, Item)
        self.assertEqual(config.value.type, "int")
        self.assertEqual(config.value.value, 12)

        self.assertIsInstance(config.none, Item)
        self.assertEqual(config.none.type, None)
        self.assertEqual(config.none.value, None)

        self.assertIsInstance(config.item, Item)
        self.assertEqual(config.item.type, "str")
        self.assertEqual(config.item.value, "123")
        self.assertEqual(config.item.max, "1000")

        self.assertIsInstance(config.sub, Config)
        self.assertIsInstance(config.sub.a, Config)
        self.assertIsInstance(config.sub.a.c, Item)
        self.assertEqual(config.sub.a.c.type, "int")
        self.assertEqual(config.sub.a.c.value, 12)
        self.assertIsInstance(config.sub.a.d, Item)
        self.assertEqual(config.sub.a.d.type, "list")
        self.assertEqual(config.sub.a.d.value, [1, 2, 3])
        self.assertIsInstance(config.sub.a.e, Item)
        self.assertEqual(config.sub.a.e.type, "int")
        self.assertEqual(config.sub.a.e.value, None)

        self.assertIsInstance(config.sub.a.f, Config)
        self.assertIsInstance(config.sub.a.f.end, Item)
        self.assertEqual(config.sub.a.f.end.type, "int")
        self.assertEqual(config.sub.a.f.end.value, 123)

        self.assertIsInstance(config.sub.b, Item)
        self.assertEqual(config.sub.b.type, "str")
        self.assertEqual(config.sub.b.value, "hello")
