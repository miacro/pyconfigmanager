def get_item_by_catrgory(item, category="", exclude_categories=["metadata"]):
    result = {}
    result.update(item)
    if category:
        result = result[category]
    if not exclude_categories:
        return result
    for exclude_category in exclude_categories:
        if exclude_category in result:
            del result[exclude_category]
    return result
