import os

import yaml

path = os.environ.get("CONFIG_LOCATION", "webserver-config.yaml")
with open(path, "r") as ymlfile:
    config = yaml.safe_load(ymlfile)
