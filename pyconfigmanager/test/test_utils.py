import unittest
from pyconfigmanager.utils import typename, locate_type, convert_type
from pyconfigmanager.utils import get_item_by_category
from pyconfigmanager.utils import load_yaml, load_json, dump_json, dump_yaml
import tempfile
import os


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

    def test_get_item_by_category(self):
        item = {"a": {"b": 1, "c": 3}, "d": 56}
        compare_item = get_item_by_category(
            item, category="", excludes=["b", "c"])
        self.assertDictEqual(compare_item, item)
        self.assertDictEqual(
            get_item_by_category(item, category="a", excludes=["g"]),
            item["a"])
        self.assertDictEqual(
            get_item_by_category(item, category="a", excludes=["b"]), {
                "c": 3
            })
        self.assertDictEqual(
            get_item_by_category(item, category="a", excludes=["b", "c"]), {})
        self.assertDictEqual(
            get_item_by_category(item, category="g", excludes=[]), {})

    def test_load_yaml(self):
        content1 = """
---
a: 1
b:
  c: 12
---
a: 1
b: 12
"""
        content2 = """
c:
  d: 12
  e:
    f: 45
"""
        content3 = """
h: 12
"""
        content4 = """
---
i: 45
j:
  k: 34
---
w: 12
"""
        with tempfile.NamedTemporaryFile(
                mode="wt",
                delete=False) as tempfile1, tempfile.NamedTemporaryFile(
                    mode="wt", delete=False) as tempfile2:
            tempfile1.writelines(content3)
            tempfile1.flush()
            tempfile2.writelines(content4)
            tempfile2.flush()
        result = [item for item in load_yaml(contents=content1)]
        self.assertListEqual(result, [{
            "a": 1,
            "b": {
                "c": 12
            }
        }, {
            "a": 1,
            "b": 12
        }])
        result = [item for item in load_yaml(filenames=tempfile1.name)]
        self.assertListEqual(result, [{"h": 12}])

        result = [
            item
            for item in load_yaml(
                contents=[content1, content2],
                filenames=[tempfile1.name, tempfile2.name])
        ]
        self.assertListEqual(result, [{
            "a": 1,
            "b": {
                "c": 12
            }
        }, {
            "a": 1,
            "b": 12
        }, {
            "c": {
                "d": 12,
                "e": {
                    "f": 45
                }
            }
        }, {
            "h": 12
        }, {
            "i": 45,
            "j": {
                "k": 34
            }
        }, {
            "w": 12
        }])
        os.remove(tempfile1.name)
        os.remove(tempfile2.name)

    def test_load_json(self):
        content1 = """
[{
"a": 12,
"b": {"c": 23}
}]
"""
        content2 = """
{"a": 45, "b": 34}
"""
        content3 = """
{"c": {"d": {"e": 34}}}
"""
        content4 = """
[{"f": 12},{"g": {"h": 34}}]
"""
        with tempfile.NamedTemporaryFile(
                mode="wt",
                delete=False) as tempfile1, tempfile.NamedTemporaryFile(
                    mode="wt", delete=False) as tempfile2:
            tempfile1.writelines(content3)
            tempfile1.flush()
            tempfile2.writelines(content4)
            tempfile2.flush()
        result = [item for item in load_json(contents=content1)]
        self.assertListEqual(result, [{"a": 12, "b": {"c": 23}}])
        result = [item for item in load_json(filenames=tempfile1.name)]
        self.assertListEqual(result, [{"c": {"d": {"e": 34}}}])
        result = [
            item
            for item in load_json(
                contents=[content1, content2],
                filenames=[tempfile1.name, tempfile2.name])
        ]
        self.assertListEqual(result, [{
            "a": 12,
            "b": {
                "c": 23
            }
        }, {
            "a": 45,
            "b": 34
        }, {
            "c": {
                "d": {
                    "e": 34
                }
            }
        }, {
            "f": 12
        }, {
            "g": {
                "h": 34
            }
        }])
        os.remove(tempfile1.name)
        os.remove(tempfile2.name)

    def test_dump_yaml(self):
        def test_one(yaml):
            with tempfile.NamedTemporaryFile(
                    mode="wt", delete=False) as temp_file:
                pass
            dump_yaml(yaml, filename=temp_file.name)
            result = [item for item in load_yaml(filenames=temp_file.name)]
            if isinstance(yaml, list):
                compare_item = yaml
            else:
                compare_item = [yaml]
            self.assertListEqual(result, compare_item)
            os.remove(temp_file.name)

        test_one([{"a": 12, "b": 34, "c": {"d": 78}}])
        test_one({"a": 23, "b": 45, "c": {"d": 5465}})

    def test_dump_json(self):
        def test_one(json):
            with tempfile.NamedTemporaryFile(
                    mode="wt", delete=False) as temp_file:
                pass
            dump_json(json, filename=temp_file.name)
            result = [item for item in load_json(filenames=temp_file.name)]
            if isinstance(json, list):
                compare_item = json
            else:
                compare_item = [json]
            self.assertListEqual(result, compare_item)
            os.remove(temp_file.name)

        test_one([{"a": 12, "b": 34, "c": {"d": 78}}])
        test_one({"a": 23, "b": 45, "c": {"d": 5465}})
