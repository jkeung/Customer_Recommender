# food_finder.config
# Loads configuration data from a YAML file.
#
# Author:   Jason Keung <jason.s.keung@gmail.com>

"""
Loads configuration data from a YAML file.
"""

##########################################################################
## Imports
##########################################################################

import os
import yaml

##########################################################################
## Settings Base Class
##########################################################################

class Settings(object):

    CONF_PATHS = []                                 # Search path for configuration files

    @classmethod
    def load(klass):
        """
        Instantiates the settings by attempting to load the configuration
        from YAML files specified by the CONF_PATHS variable. This should
        be the main entry point for accessing settings.
        """
        settings = klass()
        for path in klass.CONF_PATHS:
            if os.path.exists(path):
                with open(path, 'r') as conf:
                    settings.configure(yaml.load(conf))
        return settings

    def configure(self, conf=None):
        """
        Allows updating of the settings via a dictionary of settings or
        another settings object. Generally speaking, this method is used
        to configure the object from JSON or YAML.
        """
        if not conf: return                         # Don't do anything with empty conf
        self.__dict__.update(conf)                  # Update internal dict with new data


    def get(self, key, default=None):
        """
        Fetches a key from the settings without raising a KeyError and if
        the key doesn't exist on the config, it returns a default instead.
        """
        try:
            return self[key]
        except KeyError:
            return default

    def __getitem__(self, key):
        """
        Main settings access method. This performs a case insensitive
        lookup of the key on the class, but filters methods and anything
        that starts with an underscore.
        """
        key = key.lower()                                   # Case insensitive lookup
        if not key.startswith('_') and hasattr(self, key):  # Ignore _vars and ensure attr exists
            attr = getattr(self, key)
            if not callable(attr):                          # Ignore any methods
                return attr
        raise KeyError("%s has no setting '%s'" % (self.__class__.__name__, key))

    def __str__(self):
        """
        Pretty print the configuration
        """
        s = ""
        for param in self.__dict__.items():
            if param[0].startswith('_'): continue
            s += "%s: %s\n" % param
        return s

##########################################################################
## FoodFinder Settings
##########################################################################

class FoodFinderSettings(Settings):

    # Search path for configuration files
    CONF_PATHS = [
        os.path.expandvars('$HOME/.yelp/.config.yaml'),  # User specific configuration
        os.path.abspath('conf/config.yaml'),             # Local directory configuration
        os.path.abspath('config.yaml'),                  # Local directory configuration
    ]

    def __init__(self):
        # self.debug                = False
        # self.htdocs               = os.path.abspath("output/business_dicts/")
        # self.database             = os.path.abspath("output/food_finder.db")
        # self.model_pickle         = os.path.abspath("output/reccod.pickle")
        self.consumer_key = os.environ.get("CONSUMER_KEY", None)
        self.consumer_secret = os.environ.get("CONSUMER_SECRET", None)
        self.access_token = os.environ.get("ACCESS_TOKEN", None)
        self.access_token_secret = os.environ.get("ACCESS_TOKEN_SECRET", None)


##########################################################################
## On Import, Load Settings
##########################################################################

settings = FoodFinderSettings.load()

if __name__ == '__main__':
    print settings
