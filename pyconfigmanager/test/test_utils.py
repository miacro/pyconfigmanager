import unittest
from pyconfigmanager.utils import typename, locate_type, convert_type


class TestUtils(unittest.TestCase):
    def test_typename(self):
        self.assertEqual(typename(str), "str")
        self.assertEqual(typename(bool), "bool")
        self.assertEqual(typename(unittest.TestCase), "unittest.case.TestCase")
        self.assertRaises(AssertionError, typename, unittest)

    def test_locate_type(self):
        self.assertEqual(locate_type("str"), str)
        self.assertEqual(locate_type("builtins.bool"), bool)
        self.assertEqual(
            locate_type("unittest.case.TestCase"), unittest.TestCase)
        self.assertEqual(locate_type("module"), type(unittest))

    def test_convert_type(self):
        self.assertEqual(convert_type("12", "int"), 12)
        self.assertEqual(convert_type("12", int), 12)
        self.assertEqual(convert_type("hello", int), None)
        self.assertEqual(convert_type(12.34, list), None)
