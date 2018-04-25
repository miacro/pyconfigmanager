from .utils import load_config
from . import utils
import os

DEFAULT_HELPER_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "helper.yaml")


def get_helpers(filenames=[DEFAULT_HELPER_FILE],
                category="helper",
                excludes=[]):
    result = {}
    for _, item in enumerate(load_config(filename=filenames)):
        item = utils.get_item_by_category(
            item, category=category, excludes=excludes)
        result.update(item)

    return result


if __name__ == "__main__":
    print(get_helpers())
