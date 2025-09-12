import os
import sys
import tomllib


def get_pyproject():
    with open("pyproject.toml", "rb") as f:
        pyproject = tomllib.load(f)
    return pyproject


def parse_url(url: str) -> dict:
    url_parts = url.split("://")
    if len(url_parts) == 1:
        return {"scheme": "sqlite", "database": url}
    else:
        scheme, database = url_parts
        return {"scheme": scheme, "database": database}


def load_all_config():
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
    if PROJECT_ROOT not in sys.path:
        sys.path.append(PROJECT_ROOT)

    from dotenv import load_dotenv, find_dotenv

    dotenv_path = find_dotenv(usecwd=True)
    if not dotenv_path:
        dotenv_path = os.path.join(PROJECT_ROOT, ".env")
    load_dotenv(dotenv_path, override=False)
