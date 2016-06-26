#!/usr/bin/env python

"""
Download and update Slicer extensions source checkouts.

This python CLI allows to download and update sources
checkouts corresponding to a list of Slicer extension
description files.

It also keep track of the initial checkout time for each extension.
Time are stored in file named `ExtensionsCheckoutTimes.json` located
in the checkouts top-level directory.
"""

from __future__ import unicode_literals, print_function, absolute_import
import argparse
import glob
import json
import logging
import os
import re
import shutil
import sys
import time

from libvcs.shortcuts import create_repo

log = logging.getLogger(__name__)


def setup_logger(logger=None, level='INFO'):
    """Setup logging for CLI use.

    :param logger: instance of logger
    :type logger: :py:class:`Logger`

    :param level: logger level 'DEBUG', 'INFO', 'WARNING', 'ERROR' or 'CRITICAL'
    :type level: :class:`str`
    """
    if not logger:
        logger = logging.getLogger()
    if not logger.handlers:
        # pys4ext config
        channel = logging.StreamHandler()
        logger.setLevel(level)
        logger.addHandler(channel)

        # libvcs-level logging
        repo_channel = logging.StreamHandler()
        repo_formatter = logging.Formatter(
            '[%(repo_name)s] (%(repo_vcs)s) %(levelname)1.1s: %(message)s'
        )
        repo_channel.setFormatter(repo_formatter)
        vcslogger = logging.getLogger('libvcs')
        vcslogger.propagate = False
        vcslogger.addHandler(repo_channel)
        vcslogger.setLevel(level)


def time_call(method):
    """Decorate ``method`` so that it returns its execution time."""
    def wrapper(*wrapper_args, **wrapper_kwargs):
        start = time.time()
        call_result = method(*wrapper_args, **wrapper_kwargs)
        call_duration = time.time() - start
        return call_duration, call_result
    return wrapper


def parse_s4ext(ext_file_path):
    """Parse a Slicer extension description file.

    :param ext_file_path: Path to a Slicer extension description file.
    :return: Dictionnary of extension metadata.
    """
    ext_metadata = {}
    with open(ext_file_path) as ext_file:
        for line in ext_file:
            if not line.strip() or line.startswith("#"):
                continue
            fields = [field.strip() for field in line.split(' ', 1)]
            assert(len(fields) <= 2)
            ext_metadata[fields[0]] = fields[1] if len(fields) == 2 else None
    return ext_metadata


def read_dict(json_file_path):
    """Parse a json file and return corresponding dictionary."""
    data = {}
    if os.path.exists(json_file_path):
        with open(json_file_path) as json_file:
            data = json.load(json_file)
    return data


def write_dict(json_file_path, data):
    """Write dictionary to json file."""
    with open(json_file_path, 'w') as json_file:
        json_file.write(json.dumps(data, indent=4))


def progress_callback(output, timestamp):
    """Write ``output`` to ``sys.stdout``."""
    sys.stdout.write(output)
    sys.stdout.flush()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Checkout and update Slicer extension sources.')
    parser.add_argument(
        "--filter",
        default=".*", type=str,
        help="Regular expression to select particular \
        extensions (e.g 'ABC|Slicer.+')")
    parser.add_argument(
        "--delete", action="store_true",
        help="Delete previous source checkout.")
    parser.add_argument(
        '--log-level', dest='log_level',
        default='INFO',
        help='Level of debug verbosity. DEBUG, INFO, WARNING, ERROR, CRITICAL.',
    )

    parser.add_argument("/path/to/ExtensionsIndex")
    parser.add_argument("/path/to/ExtensionsSource")
    args = parser.parse_args()

    def get_path_arg(arg_key):
        """Read command line argument ``arg_key`` as an absolute path."""
        return os.path.abspath(os.path.expanduser(getattr(args, arg_key)))
    extensions_source_dir = get_path_arg("/path/to/ExtensionsSource")
    extensions_index_dir = get_path_arg("/path/to/ExtensionsIndex")

    setup_logger(logger=log, level=args.log_level.upper())

    log.info("extensions_source_dir is [%s]" % extensions_source_dir)
    log.info("extensions_index_dir is [%s]" % extensions_index_dir)

    file_match = "*.s4ext"

    stats_file_name = "ExtensionsCheckoutTimes.json"

    stats_file_path = os.path.join(extensions_source_dir, stats_file_name)
    stats = read_dict(stats_file_path)

    re_file_match = re.compile(args.filter)
    for file_path in glob.glob(os.path.join(extensions_index_dir, file_match)):
        extension_name = os.path.splitext(os.path.basename(file_path))[0]
        if not re_file_match.match(extension_name):
            continue
        metadata = parse_s4ext(file_path)
        log_context = {'repo_name': extension_name, 'repo_vcs': metadata['scm']}
        if args.delete:
            extension_source_dir = \
                os.path.join(extensions_source_dir, extension_name)
            if os.path.exists(extension_source_dir):
                log.warning("Deleting %s" % extension_source_dir,
                            extra=log_context)
                if extension_name in stats:
                    del stats[extension_name]
                    write_dict(stats_file_path, stats)
                shutil.rmtree(extension_source_dir)
        elapsed_time_collected = False
        if extension_name in stats:
            elapsed_time_collected = True
        url = "{scm}+{scmurl}@{scmrevision}".format(**metadata)
        kwargs = {}
        for param_name in ['username', 'password']:
            if 'svn' + param_name in metadata:
                kwargs['svn_' + param_name] = metadata['svn' + param_name]
        repo = create_repo(
            url=metadata['scmurl'],
            vcs=metadata['scm'],
            rev=metadata['scmrevision'],
            repo_dir=os.path.join(extensions_source_dir, extension_name),
            **kwargs)
        repo.progress_callback = progress_callback
        repo.info("Begin timed call")
        duration, result = time_call(repo.update_repo)()
        repo.info("Elapsed time: {:.2f}s\n".format(duration))
        if not elapsed_time_collected:
            stats[extension_name] = duration

        write_dict(stats_file_path, stats)
