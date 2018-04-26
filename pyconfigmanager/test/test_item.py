import unittest
from pyconfigmanager.item import BasicItem, ArgparseItem, Item, str2bool


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
        item.update_values(
            {
                "abc": 12,
                "cde": "hello",
                "fgh": 12.4
            }, merge=False)
        self.assertEqual(item.abc, 12)
        self.assertEqual(item.cde, "hello")
        self.assertEqual(item.fgh, 12.4)
        self.assertRaises(AttributeError, item.update_values, {"aaa": 1})

        item.update_values({"abc": None, "cde": 12}, merge=True)
        self.assertEqual(item.abc, 12)
        self.assertEqual(item.cde, 12)


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
        self.assertRaises(TypeError, Item, None)

    def test_setattr(self):
        item = Item()
        item.type = "str"
        item.value = "hello"
        self.assertEqual(item.type, "str")
        self.assertEqual(item.value, "hello")
        self.assertEqual(item.argparse, None)
        item.argparse = "hello"
        self.assertEqual(item.argparse, True)
        item.argparse = []
        self.assertEqual(item.argparse, False)
        item.argparse = {"default": 123, "help": "empty", "action": "append"}
        self.assertIsInstance(item.argparse, ArgparseItem)
        self.assertEqual(item.argparse.default, 123)
        self.assertEqual(item.argparse.help, "empty")
        self.assertEqual(item.argparse.action, "append")
        item.argparse = None
        self.assertEqual(item.argparse, False)
        item.type = int
        self.assertEqual(item.type, "int")
        item.value = 12.4
        self.assertEqual(item.value, 12)
        item.max = 0.7
        self.assertEqual(item.max, 0)
        item.min = 12.4
        self.assertEqual(item.min, 12)
        item.value = "hello"
        self.assertEqual(item.value, None)
        item.type = "str"
        item.value = None
        self.assertEqual(item.value, None)

        item.type = None
        item.value = "hello"
        self.assertEqual(item.value, "hello")

        item.type = "float"
        item.value = "123.5"
        self.assertEqual(item.value, 123.5)

        item.type = list
        item.value = 12.4
        self.assertEqual(item.value, None)

        argparseitem = ArgparseItem(required=True)
        item.argparse = argparseitem
        self.assertIs(item.argparse, argparseitem)

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
        self.assertEqual(item.value, None)
        self.assertIsInstance(item.argparse, ArgparseItem)
        self.assertEqual(item.argparse.default, 123)
        self.assertEqual(item.argparse.nargs, "*")

    def test_argparse_options(self):
        item = Item(
            type="str",
            value="hello",
            argparse={
                "default": None,
                "action": "append"
            })
        empty_options = {
            "help": " ",
        }
        compare_options = dict(empty_options.items())
        compare_options["default"] = "hello"
        compare_options["action"] = "append"
        compare_options["help"] = " "
        self.assertDictEqual(item.argparse_options(), compare_options)

        item.argparse.type = "int"
        item.argparse.default = 123
        item.argparse.help = "empty"
        compare_options["default"] = 123
        compare_options["help"] = "empty"
        self.assertDictEqual(item.argparse_options(), compare_options)

        compare_options = dict(empty_options.items())
        item = Item(type=list, value="1111")
        compare_options["nargs"] = "*"
        compare_options["default"] = ["1", "1", "1", "1"]
        self.assertDictEqual(item.argparse_options(), compare_options)

        compare_options = dict(empty_options.items())
        item = Item(type=list, value="1111", argparse={"nargs": 2})
        compare_options["nargs"] = 2
        compare_options["default"] = ["1", "1", "1", "1"]
        self.assertDictEqual(item.argparse_options(), compare_options)

        compare_options = dict(empty_options.items())
        item = Item(type=list, value="1", argparse={"type": int})
        compare_options["type"] = int
        compare_options["nargs"] = "*"
        compare_options["default"] = ["1"]
        self.assertDictEqual(item.argparse_options(), compare_options)

        item = Item(type=None, value=1)
        compare_options = dict(empty_options.items())
        compare_options["default"] = 1
        self.assertDictEqual(item.argparse_options(), compare_options)

        item = Item(type=bool, value=True)
        compare_options = dict(empty_options.items())
        compare_options["default"] = True
        compare_options["type"] = str2bool
        self.assertDictEqual(item.argparse_options(), compare_options)
        item = Item(type=bool, value=True, argparse={"type": int})
        compare_options = dict(empty_options.items())
        compare_options["default"] = True
        compare_options["type"] = int
        self.assertDictEqual(item.argparse_options(), compare_options)

        item = Item(
            type=int,
            argparse={
                "action": "store_true",
                "type": int,
                "metavar": "TEST",
                "choices": [True, False],
                "nargs": "*",
                "const": "222"
            })
        compare_options = dict(empty_options.items())
        compare_options["action"] = "store_true"
        self.assertDictEqual(item.argparse_options(), compare_options)

        item = Item(type=int, help="123")
        compare_options = dict(empty_options.items())
        compare_options["type"] = int
        compare_options["help"] = "123"
        self.assertDictEqual(item.argparse_options(), compare_options)
        item.argparse = {"help": "1234"}
        compare_options["help"] = "1234"
        self.assertDictEqual(item.argparse_options(), compare_options)

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

        item.value = 8
        self.assertRaises(AssertionError, item.assert_value, {"max": 6})
        other = Item(type=int, max=7, min=7)
        self.assertRaises(AssertionError, item.assert_value, other)

        item.value = None
        self.assertRaises(AssertionError, item.assert_value, {
            "required": True
        })
