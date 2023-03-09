#!/usr/bin/env python

import yaml
import requests

"""
Post migration
Compares the old url redirected url path to expected mapped path in the redirects.yaml
If mapping does not match it will log
"""

OLD_URL = "https://blog.junaideffendi.com"
NEW_URL = "https://www.junaideffendi.com"
PATH = "../outputs/redirects.yaml"

with open(PATH, "r") as stream:
    redirects = yaml.safe_load(stream)
    i = 1
    for o,n in redirects[301].items():
        o = f'{OLD_URL}{o}'
        n = f'{NEW_URL}{n}'

        resp = requests.get(o)
        if resp.url != n:
            print(f"mismatch between old and new url {o} -> {n}")
        i = i + 1