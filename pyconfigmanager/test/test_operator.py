import unittest
from pyconfigmanager.config import Config
from pyconfigmanager import errors
from pyconfigmanager import utils
from pyconfigmanager import options
from pyconfigmanager import operator
import os
import tempfile


class TestOperator(unittest.TestCase):
    def test_assert_values(self):
        config = Config({
            "a": 12,
            "b": {
                "_type_": int,
                "_value_": "123",
                "_max_": 12
            }
        })
        self.assertRaises(AssertionError, operator.assert_values, config)
        self.assertRaises(AssertionError, operator.assert_values, config, {
            "a": {
                "b": {
                    "_max_": 12
                }
            }
        })
        self.assertRaises(AssertionError, operator.assert_values, config, {
            "a": {
                "b": {
                    "_min_": 345
                }
            }
        })
        self.assertRaises(AssertionError, operator.assert_values, config, {
            "a": {
                "b": {
                    "_type_": "str"
                }
            }
        })
        config = Config({
            "a": {
                "b": {
                    "c": {
                        "_value_": None,
                        "_required_": True
                    }
                }
            }
        })
        self.assertRaises(AssertionError, operator.assert_values, config)
        operator.assert_values(config.a.b["c"], schema={"_required_": False})
        operator.assert_values(config, schema={"a": True})
        self.assertRaises(AssertionError, operator.assert_values, config, {
            "a": True,
            "b": True
        })
        operator.assert_values(config, schema={"a": {"b": True}})
        self.assertRaises(
            AssertionError,
            operator.assert_values,
            config,
            schema={
                "a": {
                    "b": {
                        "c": {
                            "_required_": True
                        }
                    }
                }
            })
        operator.assert_values(config, schema={"a": {"b": 12}})
        operator.assert_values(config, schema={"a": {"b": {"c": "haha"}}})
        self.assertRaises(
            AssertionError,
            operator.assert_values,
            config,
            schema={
                "a": {
                    "b": {
                        "c": {
                            "d": 12
                        }
                    }
                }
            })
        config = Config({
            "a": {
                "b": {
                    "c": {
                        "_value_": None,
                        "_required_": None
                    }
                }
            }
        })
        self.assertRaises(
            AssertionError,
            operator.assert_values,
            config,
            schema={
                "a": {
                    "b": {
                        "c": {
                            "_required_": True
                        }
                    }
                }
            })
        self.assertRaises(
            AssertionError,
            operator.assert_values,
            config,
            schema={
                "a": {
                    "_required_": True
                }
            })

    def test_argument_options(self):
        self.maxDiff = None
        config = Config({"_value_": "12", "_type_": int, "_help_": "124"})
        self.assertDictEqual(
            operator.argument_options(config), {
                "--": {
                    "default": 12,
                    "help": '124',
                    "type": int
                }
            })
        config = Config({
            "_value_": "12",
            "_type_": int,
            "_help_": "124",
            "_argoptions_": {
                "type": "str",
                "default": 12,
                "help": "345",
                "metavar": "123",
                "action": None,
                "nargs": "test2",
                "const": "test3",
                "choices": "test4",
                "position": 12,
                "short": "a",
                "required": True,
            }
        })
        self.assertDictEqual(
            operator.argument_options(config), {
                "--": {
                    "type": str,
                    "default": 12,
                    "help": "345",
                    "metavar": "123",
                    "nargs": "test2",
                    "const": "test3",
                    "choices": "test4",
                    "position": 12,
                    "short": "a",
                    "required": True
                }
            })
        config = Config({
            "_value_": "12",
            "_type_": int,
            "_help_": "124",
            "_argoptions_": {
                "type": "str",
                "default": 12,
                "help": "345",
                "metavar": "123",
                "action": "test",
                "nargs": "test2",
                "const": "test3",
                "choices": "test4",
                "position": 12,
                "short": "a",
                "required": True,
            }
        })
        self.assertDictEqual(
            operator.argument_options(config), {
                "--": {
                    "default": 12,
                    "help": "345",
                    "action": "test",
                    "position": 12,
                    "short": "a",
                    "required": True
                }
            })

        config = Config({
            "_type_": "list",
            "_value_": [1, 2, 3],
            "_argoptions_": {
                "default": "123"
            }
        })
        self.assertDictEqual(
            operator.argument_options(config), {
                "--": {
                    "nargs": "*",
                    "default": "123",
                    "help": " "
                }
            })
        config = Config({
            "_type_": "list",
            "_value_": [1, 2, 3],
            "_argoptions_": {
                "type": "str",
                "nargs": "345"
            }
        })
        self.assertDictEqual(
            operator.argument_options(config), {
                "--": {
                    "nargs": "345",
                    "default": [1, 2, 3],
                    "help": " ",
                    "type": str,
                    "nargs": "345",
                }
            })
        config = Config({"_type_": "bool"})
        self.assertDictEqual(
            operator.argument_options(config), {
                "--": {
                    "type": operator.str2bool,
                    "help": " "
                }
            })

        config = Config({
            "a": "12",
            "b": 34,
            "_type_": "bool",
            "_value_": "True"
        })
        self.assertDictEqual(
            operator.argument_options(config), {
                "--": {
                    "type": operator.str2bool,
                    "help": " ",
                    "default": True
                },
                "--a": {
                    "type": str,
                    "default": "12",
                    "help": " "
                },
                "--b": {
                    "type": int,
                    "default": 34,
                    "help": " "
                },
            })
        config = Config({
            "a": {
                "_value_": "123",
                "c": False
            },
            "b": {
                "_value_": 567,
                "d": {
                    "_value_": 456,
                    "_argoptions_": {
                        "type": "str"
                    }
                }
            },
            "_type_": "bool",
            "_value_": "True"
        })
        self.assertDictEqual(
            operator.argument_options(config), {
                "--": {
                    "type": operator.str2bool,
                    "help": " ",
                    "default": True
                },
                "--a": {
                    "type": str,
                    "default": "123",
                    "help": " "
                },
                "--a-c": {
                    "type": operator.str2bool,
                    "default": False,
                    "help": " "
                },
                "--b": {
                    "type": int,
                    "default": 567,
                    "help": " "
                },
                "--b-d": {
                    "type": str,
                    "default": 456,
                    "help": " "
                }
            })

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
            operator.dump_config,
            config,
            filename="",
            filename_config="config.file",
            exit=False)
        operator.dump_config(
            config, filename=jsonfile, exit=False, dumpname="test")
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
        operator.dump_config(
            config, filename=yamlfile, exit=False, dumpname="")
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
        operator.dump_config(
            config, filename_config="config.file", exit=False, dumpname="12")
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


"""
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
            command_attrname="subcommand")
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
            command_attrname="subcommand")
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
            command_attrname="subcommand")
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
                        "_type_": list,
                        "argoptions": {
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
                        "_type_": list,
                        "argoptions": {
                            "nargs": 2
                        }
                    }
                },
                "f": 12,
            }
        })
        parser = config.argument_parser()
        args = parser.parse_args(["--c-d-e", "1", "2"])
        self.assertEqual(args.c_d_e, ["1", "2"])

        parser = config.argument_parser(subcommands={"c": {"d": True}})
        args = parser.parse_args(["c", "--f", "34", "d", "--e", "45", "23"])
        self.assertEqual(args.e, ["45", "23"])
        self.assertEqual(args.command, "c.d")
        self.assertEqual(args.f, 34)

        config = Config({
            "c": {
                "d": {
                    "e": {
                        "_type_": list,
                        "argoptions": {
                            "nargs": 2
                        }
                    }
                }
            },
            "a": {
                "d": {
                    "e": 24
                }
            }
        })
        parser = config.argument_parser(subcommands={
            "c": {
                "d": True
            },
            "a": {
                "d": True
            }
        })
        args = parser.parse_args(["c", "d", "--e", "45", "23"])
        self.assertEqual(args.e, ["45", "23"])
        args = parser.parse_args(["a", "d", "--e", "78"])
        self.assertEqual(args.e, 78)

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
            subcommands=("a", "b"), command_attrname="subcommand")
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
        self.assertEqual(config.command, None)

        schema = dict(origin.items())
        schema.update({
            "e": {
                "d": 23,
                "f": {
                    "h": "345"
                }
            },
            "g": {
                "d": "qwe",
                "f": {
                    "h": {
                        "i": 567
                    },
                    "d": "rrrr",
                }
            },
            "command": "",
        })
        config = Config(schema)
        subcommands = {"e": {"f": True}, "g": {"f": {"h": True}}}
        config.update_values_by_argument_parser(
            arguments=["e", "--d", "56", "f", "--h", "dddd"],
            subcommands=subcommands)
        self.assertEqual(config.e.d, 56)
        self.assertEqual(config.e.f.h, "dddd")
        self.assertEqual(config.command, "e.f")

        config = Config(schema)
        config.update_values_by_argument_parser(
            arguments=["g", "--d", "567", "f", "h", "--i", "123"],
            subcommands=subcommands)
        self.assertEqual(config.command, "g.f.h")
        self.assertEqual(config.g.f.h.i, 123)
        # value of args.g.f.d reset by the default value of config.g.f.d
        self.assertEqual(config.g.f.d, "rrrr")
        self.assertEqual(config.g.d, "qwe")

        config = Config(schema)
        config.update_values_by_argument_parser(
            arguments=[
                "g", "--d", "567", "f", "--d", "123", "h", "--i", "123"
            ],
            subcommands=subcommands)
        self.assertEqual(config.command, "g.f.h")
        self.assertEqual(config.g.f.h.i, 123)
        self.assertEqual(config.g.f.d, "123")
        self.assertEqual(config.g.d, "qwe")
"""
