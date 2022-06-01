import logging
import os

def define_logging_parser_args(parser):
    parser.add_argument('--log-level', dest='log_level', help='log level')
    parser.add_argument('--log-filename', dest='log_filename', help='filename of the log')

def setup_logging(args):
    log_filename = None
    log_level = logging.WARNING
    
    if args.log_filename:
        if os.path.exists(args.log_filename):
            log_filename = args.log_filename
        else:
            return False
    
    if args.log_level:
        log_level = logging._nameToLevel[str(args.log_level).upper()]
        if not log_level:
            return False

    if log_filename:
        logging.basicConfig(filename=log_filename, encoding='utf-8', level=log_level)
    else:
        logging.basicConfig(level=log_level)

    return True
    

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