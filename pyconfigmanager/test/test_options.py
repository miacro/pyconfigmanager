import unittest
from pyconfigmanager.options import BasicOptions, ArgumentOptions, Options
from pyconfigmanager.options import str2bool


class TestBasicOptions(unittest.TestCase):
    def test_init(self):
        options = BasicOptions(names=["abc", "cde", "fgh"])
        self.assertTrue(hasattr(options, "abc"))
        self.assertTrue(hasattr(options, "cde"))
        self.assertTrue(hasattr(options, "fgh"))
        self.assertIsNone(options.abc)
        self.assertIsNone(options.cde)
        self.assertIsNone(options.fgh)
        options = BasicOptions(
            names=["abc", "cde", "fgh"], abc=12, cde="ddd", fgh=23.4)
        self.assertEqual(options.abc, 12)
        self.assertEqual(options.cde, "ddd")
        self.assertEqual(options.fgh, 23.4)

    def test_setattr(self):
        options = BasicOptions(names=["abc", "cde", "efg"])
        options.abc = 12
        self.assertEqual(options.abc, 12)
        self.assertRaises(AttributeError, setattr, options, "bbb", 34)

    def test_update_values(self):
        options = BasicOptions(names=["abc", "cde", "fgh"])
        options.update_values(
            {
                "abc": 12,
                "cde": "hello",
                "fgh": 12.4
            }, merge=False)
        self.assertEqual(options.abc, 12)
        self.assertEqual(options.cde, "hello")
        self.assertEqual(options.fgh, 12.4)
        self.assertRaises(AttributeError, options.update_values, {"aaa": 1})

        options.update_values({"abc": None, "cde": 12}, merge=True)
        self.assertEqual(options.abc, 12)
        self.assertEqual(options.cde, 12)


class TestArgumentOptions(unittest.TestCase):
    def test_init(self):
        options = ArgumentOptions()
        self.assertTrue(hasattr(options, "default"))
        self.assertTrue(hasattr(options, "help"))
        self.assertTrue(hasattr(options, "action"))
        self.assertTrue(hasattr(options, "choices"))
        self.assertTrue(hasattr(options, "nargs"))
        self.assertTrue(hasattr(options, "required"))
        self.assertTrue(hasattr(options, "type"))
        self.assertTrue(hasattr(options, "metavar"))
        self.assertTrue(hasattr(options, "dest"))


class TestOptions(unittest.TestCase):
    def test_init(self):
        options = Options()
        self.assertTrue(hasattr(options, "type"))
        self.assertTrue(hasattr(options, "value"))
        self.assertTrue(hasattr(options, "required"))
        self.assertTrue(hasattr(options, "min"))
        self.assertTrue(hasattr(options, "max"))
        self.assertTrue(hasattr(options, "argoptions"))
        self.assertRaises(TypeError, Options, None)

    def test_setattr(self):
        options = Options()
        options.type = "str"
        options.value = "hello"
        self.assertEqual(options.type, "str")
        self.assertEqual(options.value, "hello")
        self.assertEqual(options.argoptions, None)
        options.argoptions = "hello"
        self.assertEqual(options.argoptions, True)
        options.argoptions = []
        self.assertEqual(options.argoptions, False)
        options.argoptions = {
            "default": 123,
            "help": "empty",
            "action": "append"
        }
        self.assertIsInstance(options.argoptions, ArgumentOptions)
        self.assertEqual(options.argoptions.default, 123)
        self.assertEqual(options.argoptions.help, "empty")
        self.assertEqual(options.argoptions.action, "append")
        options.argoptions = None
        self.assertEqual(options.argoptions, False)
        options.type = int
        self.assertEqual(options.type, "int")
        options.value = 12.4
        self.assertEqual(options.value, 12)
        options.max = 0.7
        self.assertEqual(options.max, 0)
        options.min = 12.4
        self.assertEqual(options.min, 12)
        options.value = "hello"
        self.assertEqual(options.value, None)
        options.type = "str"
        options.value = None
        self.assertEqual(options.value, None)

        options.type = None
        options.value = "hello"
        self.assertEqual(options.value, "hello")

        options.type = "float"
        options.value = "123.5"
        self.assertEqual(options.value, 123.5)

        options.type = list
        options.value = 12.4
        self.assertEqual(options.value, None)

        argoptionsoptions = ArgumentOptions(required=True)
        options.argoptions = argoptionsoptions
        self.assertIs(options.argoptions, argoptionsoptions)

    def test_update_values(self):
        options = Options()
        options.update_values({
            "type": "str",
            "value": "hello",
            "required": True,
            "argoptions": [1, 2, 3]
        })
        self.assertEqual(options.type, "str")
        self.assertEqual(options.value, "hello")
        self.assertEqual(options.required, True)
        self.assertEqual(options.argoptions, True)
        options.update_values({
            "type": "int",
            "argoptions": {
                "default": 123,
                "nargs": "*"
            }
        })
        self.assertEqual(options.type, "int")
        self.assertEqual(options.value, None)
        self.assertIsInstance(options.argoptions, ArgumentOptions)
        self.assertEqual(options.argoptions.default, 123)
        self.assertEqual(options.argoptions.nargs, "*")

    def test_argument_options(self):
        options = Options(
            type="str",
            value="hello",
            argoptions={
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
        self.assertDictEqual(options.argument_options(), compare_options)

        options.argoptions.type = "int"
        options.argoptions.default = 123
        options.argoptions.help = "empty"
        compare_options["default"] = 123
        compare_options["help"] = "empty"
        self.assertDictEqual(options.argument_options(), compare_options)

        compare_options = dict(empty_options.items())
        options = Options(type=list, value="1111")
        compare_options["nargs"] = "*"
        compare_options["default"] = ["1", "1", "1", "1"]
        self.assertDictEqual(options.argument_options(), compare_options)

        compare_options = dict(empty_options.items())
        options = Options(type=list, value="1111", argoptions={"nargs": 2})
        compare_options["nargs"] = 2
        compare_options["default"] = ["1", "1", "1", "1"]
        self.assertDictEqual(options.argument_options(), compare_options)

        compare_options = dict(empty_options.items())
        options = Options(type=list, value="1", argoptions={"type": int})
        compare_options["type"] = int
        compare_options["nargs"] = "*"
        compare_options["default"] = ["1"]
        self.assertDictEqual(options.argument_options(), compare_options)

        options = Options(type=None, value=1)
        compare_options = dict(empty_options.items())
        compare_options["default"] = 1
        self.assertDictEqual(options.argument_options(), compare_options)

        options = Options(type=bool, value=True)
        compare_options = dict(empty_options.items())
        compare_options["default"] = True
        compare_options["type"] = str2bool
        self.assertDictEqual(options.argument_options(), compare_options)
        options = Options(type=bool, value=True, argoptions={"type": int})
        compare_options = dict(empty_options.items())
        compare_options["default"] = True
        compare_options["type"] = int
        self.assertDictEqual(options.argument_options(), compare_options)

        options = Options(
            type=int,
            argoptions={
                "action": "store_true",
                "type": int,
                "metavar": "TEST",
                "choices": [True, False],
                "nargs": "*",
                "const": "222"
            })
        compare_options = dict(empty_options.items())
        compare_options["action"] = "store_true"
        self.assertDictEqual(options.argument_options(), compare_options)

        options = Options(type=int, help="123")
        compare_options = dict(empty_options.items())
        compare_options["type"] = int
        compare_options["help"] = "123"
        self.assertDictEqual(options.argument_options(), compare_options)
        options.argoptions = {"help": "1234"}
        compare_options["help"] = "1234"
        self.assertDictEqual(options.argument_options(), compare_options)

    def test_assert_value(self):
        options = Options()
        options.type = None
        options.value = "hello"
        options.type = "int"
        self.assertRaises(AssertionError, options.assert_value)
        options.type = None
        options.required = True
        options.value = None
        self.assertRaises(AssertionError, options.assert_value)

        options.type = int
        options.max = 12
        options.min = 2
        options.value = 0
        self.assertRaises(AssertionError, options.assert_value)
        options.value = 13
        self.assertRaises(AssertionError, options.assert_value)

        options.value = 8
        self.assertRaises(AssertionError, options.assert_value, {"max": 6})
        other = Options(type=int, max=7, min=7)
        self.assertRaises(AssertionError, options.assert_value, other)

        options.value = None
        self.assertRaises(AssertionError, options.assert_value, {
            "required": True
        })
