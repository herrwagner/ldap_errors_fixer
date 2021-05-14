import yaml
import os
import sys

from common import LOGGER

DIR_NAME = os.path.dirname(__file__)


class _ConfigurationLoader:

    def __init__(self):
        try:
            with open(DIR_NAME + "/config.yml", 'r') as config_file:
                self.cfg = yaml.load(config_file, Loader=yaml.FullLoader)
        except:
            LOGGER.exception("Failed to open config file.", exc_info=True)
            sys.exit(1)

    @property
    def config(self):
        return self.cfg


def load_config() -> dict:
    return _ConfigurationLoader().cfg
