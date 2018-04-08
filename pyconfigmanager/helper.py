from . import yaml
from . import utils
import os

DEFAULT_HELPER_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "helper.yaml")


def get_helpers(filenames=[DEFAULT_HELPER_FILE],
                category="helper",
                exclude_categories=[]):
    result = {}
    for _, item in enumerate(yaml.load_yaml(filenames=filenames)):
        item = utils.get_item_by_catrgory(
            item, category=category, exclude_categories=exclude_categories)
        result.update(item)

    return result


if __name__ == "__main__":
    print(get_helpers())
