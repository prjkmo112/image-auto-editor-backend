def tags_str_depends(tags: str):
    tags = tags.strip()
    if len(tags) == 0:
        return []

    return tags.split(",")