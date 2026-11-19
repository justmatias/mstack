import requests


def do_work(url: str) -> int:
    return requests.get(url, timeout=5).status_code
