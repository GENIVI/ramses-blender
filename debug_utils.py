import logging

def setup_logging(fname: str):
    with open(fname, 'w') as f:
        f.truncate()

    logger = logging.getLogger('ramses-scene-exporter')
    logger.setLevel(logging.DEBUG)

    # create file handler which logs even debug messages
    fh = logging.FileHandler(fname)
    fh.setLevel(logging.DEBUG)


    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)

    # add the handlers to the logger
    logger.addHandler(fh)

def get_debug_logger():
    return logging.getLogger('ramses-scene-exporter')
