#!/usr/bin/env python
import os
import configparser

class Config:
    _config = None
    
    def __init__(self):
        if not Config._config:
            _config = configparser.ConfigParser()
            _config.readfp(open('resources/config.conf'))

            # Load cfg
            # config = utils.create_config_file('resources/config.conf')

    #!/usr/bin/env python
    TRELLO_KEY = os.environ['TRELLO_KEY']
    TRELLO_TOKEN = os.environ['TRELLO_TOKEN']
    #Board for "Sprint BI"
    TRELLO_BOARD = os.environ['TRELLO_BOARD']