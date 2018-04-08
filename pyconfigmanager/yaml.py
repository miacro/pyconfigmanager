import yaml
import os


def load_yaml(contents=[], filenames=[]):
    def load_content(content):
        for item in yaml.load_all(content):
            if item is not None:
                yield item

    if isinstance(contents, str):
        contents = [contents]
    elif contents is None:
        contents = []

    if isinstance(filenames, str):
        filenames = [filenames]
    elif filenames is None:
        filenames = []

    for content in contents:
        for item in load_content(content):
            yield item

    for filename in filenames:
        with open(os.path.abspath(filename), "r") as stream:
            for item in load_content(stream):
                yield item


def dump_yaml(data, filename=""):
    if isinstance(data, list):
        dump = yaml.dump_all
    else:
        dump = yaml.dump
    output = dump(
        data,
        default_style="",
        canonical=False,
        indent=2,
        default_flow_style=False,
        encoding="utf-8",
        allow_unicode=True)
    if not filename:
        return output
    with open(filename, "wb") as stream:
        stream.write(output)
    return output
