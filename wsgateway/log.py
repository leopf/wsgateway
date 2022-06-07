from __future__ import annotations

import logging
import os
import configparser
from wsgateway.config import WSGWConfigParser

def setup_logging(config: WSGWConfigParser):
    if config.logFilename:
        logging.basicConfig(filename=config.logFilename, encoding='utf-8', level=config.logLevel)
    else:
        logging.basicConfig(level=config.logLevel)
    

def log_internal_warn(text: str):
    logging.warning("[internal] {}".format(text))

def log_internal(text: str):
    logging.debug("[internal] {}".format(text))

def log_inbound(text: str):
    logging.info("[inbound]  {}".format(text))

def log_outbound(text: str):
    logging.info("[outbound] {}".format(text))

def log_outbound_msg_open_connection():
    log_outbound("MSG: open")

def log_outbound_msg_close_connection():
    log_outbound("MSG: close")

def log_outbound_msg_data():
    log_outbound("MSG: data")

def log_inbound_msg_open_connection():
    log_inbound("MSG: open")

def log_inbound_msg_close_connection():
    log_inbound("MSG: close")

def log_inbound_msg_data():
    log_inbound("MSG: data")