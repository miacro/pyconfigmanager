import unittest
from pyconfigmanager import get_config
import os


class TestGlobal(unittest.TestCase):
    def test_get_config(self):
        filedir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "files")
        schemafile = os.path.join(filedir, "schema.yaml")
        valuesfile = os.path.join(filedir, "values.json")
        schema = {"test": {"a": 12, "b": {"c": 23, "d": "hello"}}}
        values = {"test": {"a": "hello", "b": 56, "c": {"d": 67, "e": "hell"}}}
        config = get_config(schema=schemafile, category="test")
        self.assertEqual(config.a, None)
        self.assertEqual(config.b, 12)
        self.assertEqual(config.c.d, 12)
        self.assertEqual(config.c.e, "hello")

        config = get_config(
            schema=schemafile, values=valuesfile, category="test")
        self.assertEqual(config.a, "text")
        self.assertEqual(config.b, 90)
        self.assertEqual(config.c.d, 76)
        self.assertEqual(config.c.e, "he")

        config = get_config(
            schema=[schema, schemafile],
            values=[valuesfile, values],
            category="test")
        self.assertEqual(config.a, "hello")
        self.assertEqual(config.b, 56)
        self.assertEqual(config.c.d, 67)
        self.assertEqual(config.c.e, "hell")
        self.assertEqual(config.e, 12)