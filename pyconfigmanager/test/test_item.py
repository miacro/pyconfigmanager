import unittest
from pyconfigmanager.item import BasicItem, ArgparseItem, Item


class TestBasicItem(unittest.TestCase):
    def test_init(self):
        item = BasicItem(names=["abc", "cde", "fgh"])
        self.assertTrue(hasattr(item, "abc"))
        self.assertTrue(hasattr(item, "cde"))
        self.assertTrue(hasattr(item, "fgh"))
        self.assertIsNone(item.abc)
        self.assertIsNone(item.cde)
        self.assertIsNone(item.fgh)
        item = BasicItem(
            names=["abc", "cde", "fgh"], abc=12, cde="ddd", fgh=23.4)
        self.assertEqual(item.abc, 12)
        self.assertEqual(item.cde, "ddd")
        self.assertEqual(item.fgh, 23.4)

    def test_setattr(self):
        item = BasicItem(names=["abc", "cde", "efg"])
        item.abc = 12
        self.assertEqual(item.abc, 12)
        self.assertRaises(AttributeError, setattr, item, "bbb", 34)

    def test_update_values(self):
        item = BasicItem(names=["abc", "cde", "fgh"])
        item.update_values({"abc": 12, "cde": "hello", "fgh": 12.4})
        self.assertEqual(item.abc, 12)
        self.assertEqual(item.cde, "hello")
        self.assertEqual(item.fgh, 12.4)
        self.assertRaises(AttributeError, item.update_values, {"aaa": 1})


class TestArgparseItem(unittest.TestCase):
    def test_init(self):
        item = ArgparseItem()
        self.assertTrue(hasattr(item, "default"))
        self.assertTrue(hasattr(item, "help"))
        self.assertTrue(hasattr(item, "action"))
        self.assertTrue(hasattr(item, "choices"))
        self.assertTrue(hasattr(item, "nargs"))
        self.assertTrue(hasattr(item, "required"))
        self.assertTrue(hasattr(item, "type"))
        self.assertTrue(hasattr(item, "metavar"))
        self.assertTrue(hasattr(item, "dest"))


class TestItem(unittest.TestCase):
    def test_init(self):
        item = Item()
        self.assertTrue(hasattr(item, "type"))
        self.assertTrue(hasattr(item, "value"))
        self.assertTrue(hasattr(item, "required"))
        self.assertTrue(hasattr(item, "min"))
        self.assertTrue(hasattr(item, "max"))
        self.assertTrue(hasattr(item, "argparse"))

    def test_setattr(self):
        item = Item()
        item.type = "str"
        item.value = "hello"
        self.assertEqual(item.type, "str")
        self.assertEqual(item.value, "hello")
        item.argparse = "hello"
        self.assertEqual(item.argparse, True)
        item.argparse = []
        self.assertEqual(item.argparse, False)
        item.argparse = {"default": 123, "help": "empty", "action": "append"}
        self.assertIsInstance(item.argparse, ArgparseItem)
        self.assertEqual(item.argparse.default, 123)
        self.assertEqual(item.argparse.help, "empty")
        self.assertEqual(item.argparse.action, "append")
        item.type = int
        self.assertEqual(item.type, "int")
        item.value = 12.4
        self.assertEqual(item.value, 12)
        item.max = 0.7
        self.assertEqual(item.max, 0)
        item.min = 12.4
        self.assertEqual(item.min, 12)
        self.assertRaises(ValueError, item.__setattr__, "value", "hello")
        item.type = "str"
        item.value = None
        self.assertEqual(item.value, "None")

        item.type = None
        item.value = "hello"
        self.assertEqual(item.value, "hello")

    def test_update_values(self):
        item = Item()
        item.update_values({
            "type": "str",
            "value": "hello",
            "required": True,
            "argparse": [1, 2, 3]
        })
        self.assertEqual(item.type, "str")
        self.assertEqual(item.value, "hello")
        self.assertEqual(item.required, True)
        self.assertEqual(item.argparse, True)
        item.update_values({
            "type": "int",
            "argparse": {
                "default": 123,
                "nargs": "*"
            }
        })
        self.assertEqual(item.type, "int")
        self.assertEqual(item.value, "hello")
        self.assertIsInstance(item.argparse, ArgparseItem)
        self.assertEqual(item.argparse.default, 123)
        self.assertEqual(item.argparse.nargs, "*")

    def test_get_argparse_options(self):
        item = Item(
            type="str",
            value="hello",
            argparse={
                "default": None,
                "action": "append"
            })
        compare_options = {
            "type": None,
            "nargs": None,
            "const": None,
            "default": None,
            "choices": None,
            "required": None,
            "help": None,
            "metavar": None,
            "dest": None,
            "action": None
        }
        compare_options["type"] = "str"
        compare_options["default"] = "hello"
        compare_options["action"] = "append"
        compare_options["help"] = " "
        self.assertDictEqual(item.get_argparse_options(), compare_options)

        item.argparse.type = "int"
        item.argparse.default = 123
        item.argparse.help = "empty"
        compare_options["type"] = "int"
        compare_options["default"] = 123
        compare_options["help"] = "empty"
        self.assertDictEqual(item.get_argparse_options(), compare_options)

    def test_assert_value(self):
        item = Item()
        item.type = None
        item.value = "hello"
        item.type = "int"
        self.assertRaises(AssertionError, item.assert_value)
        item.type = None
        item.required = True
        item.value = None
        self.assertRaises(AssertionError, item.assert_value)

        item.type = int
        item.max = 12
        item.min = 2
        item.value = 0
        self.assertRaises(AssertionError, item.assert_value)
        item.value = 13
        self.assertRaises(AssertionError, item.assert_value)
