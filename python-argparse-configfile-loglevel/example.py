#!/usr/bin/env python

import sys
from argparse import ArgumentParser
from configparser import ConfigParser

import logging


def main(args):
    # setting the log level on the root logger must happen BEFORE any output
    logging_argparse = ArgumentParser(prog=__file__, add_help=False)
    logging_argparse.add_argument('-l', '--log-level', default='WARNING',
                                  help='set log level')
    logging_args, _ = logging_argparse.parse_known_args(args)

    try:
        logging.basicConfig(level=logging_args.log_level)
    except ValueError:
        logging.error("Invalid log level: {}".format(logging_args.log_level))
        sys.exit(1)

    logger = logging.getLogger(__name__)
    logger.info("Log level set: {}"
                .format(logging.getLevelName(logger.getEffectiveLevel())))

    # parse values from a configuration file if provided and use those as the
    # default values for the argparse arguments
    config_argparse = ArgumentParser(prog=__file__, add_help=False)
    config_argparse.add_argument('-c', '--config-file',
                                 help='path to configuration file')
    config_args, _ = config_argparse.parse_known_args(args)

    defaults = {
        'option1': "default value",
        'option2': "default value"
    }

    if config_args.config_file:
        logger.info("Loading configuration: {}".format(config_args.config_file))
        try:
            config_parser = ConfigParser()
            with open(config_args.config_file) as f:
                config_parser.read_file(f)
            config_parser.read(config_args.config_file)
        except OSError as err:
            logger.error(str(err))
            sys.exit(1)

        defaults.update(dict(config_parser.items('options')))

    # parse the program's main arguments using the dictionary of defaults and
    # the previous parsers as "parent' parsers
    parsers = [logging_argparse, config_argparse]
    main_parser = ArgumentParser(prog=__file__, parents=parsers)
    main_parser.set_defaults(**defaults)
    main_parser.add_argument('-1', '--option1')
    main_parser.add_argument('-2', '--option2')
    main_args = main_parser.parse_args(args)

    # where did the value of each argument come from?
    logger.info("Option 1: {}".format(main_args.option1))
    logger.info("Option 2: {}".format(main_args.option2))


if __name__ == "__main__":
    main(sys.argv[1:])
