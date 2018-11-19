#!/usr/bin/env python
# import logging.config
import traceback
from datetime import date
import logging
from logging import config
import yaml

from resources.config import Config
import utils
from services.burnup_service import burnup_service

logger = None

if __name__ == '__main__':
    try:
        script_arguments = utils.get_script_arguments()

        # Logger
        # with open('resources/logging.yaml', 'rt') as f:
        #     logger = yaml.safe_load(f.read())
        #     logging.config.dictConfig(logger)

        # logging.config.fileConfig('./resources/config.conf')
        # logger.info("Starting Job [ {job_name} ] and Environment \
        #     [ {environment} ]".format(**script_arguments))
        
        # TODO: GET SPRINT START BY ARGS
        sprint_dt_start = date(2018, 11, 5)
        burnup_service(sprint_dt_start, Config.TRELLO_BOARD)

        print('Uhul! We finished successfully')
    except Exception as e:
        logging.error(e, exc_info=True)
        # logger.error("ERROR while processing plot-trello - {}: {}"\
        #     .format(e, traceback.format_exc()))
