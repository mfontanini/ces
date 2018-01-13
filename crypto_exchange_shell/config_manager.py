import yaml

class ConfigException(Exception):
    pass

class KeyMissingConfigException(ConfigException):
    def __init__(self, missing):
        ConfigException.__init__(self, '"{0}" key not found in config file')

class ConfigManager:
    def __init__(self):
        pass

    def _ensure_key_is_present(self, config, key):
        if key not in config:
            raise KeyMissingConfigException(key)

    def load(self, config_file):
        config = yaml.safe_load(open(config_file))
        self._ensure_key_is_present(config, 'exchange')
        self._ensure_key_is_present(config['exchange'], 'api_key')
        self._ensure_key_is_present(config['exchange'], 'api_secret')
        self.api_key = config['exchange']['api_key']
        self.api_secret = config['exchange']['api_secret']
