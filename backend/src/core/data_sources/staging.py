STAGING_SCHEMA = "staging"


def staging_table_name(source_id: str) -> str:
    return "src_" + source_id.replace("-", "")
