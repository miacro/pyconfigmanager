import unittest
from pyconfigmanager.options import BasicOptions, ArgumentOptions


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
