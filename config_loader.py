import yaml
import os
import sys


DIR_NAME = os.path.dirname(__file__)


class _ConfigurationLoader:

    def __init__(self, logger):
        try:
            with open(DIR_NAME + "/config.yml", 'r') as config_file:
                self.cfg = yaml.load(config_file, Loader=yaml.FullLoader)
        except:
            logger.exception("Failed to open config file.", exc_info=True)
            sys.exit(1)

    @property
    def config(self):
        return self.cfg


def load_config(logger) -> dict:
    return _ConfigurationLoader(logger).cfg
