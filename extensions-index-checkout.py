#!/usr/bin/env python

import argparse
import glob
import json
import logging
import os
import re
import shutil
import time

from libvcs.log import RepoLogFormatter
from libvcs.shortcuts import create_repo_from_pip_url as create_repo

logger = logging.getLogger(__name__)

logger.propagate = False
channel = logging.StreamHandler()
channel.setFormatter(RepoLogFormatter())
logger.setLevel('INFO')
logger.addHandler(channel)

def timecall(method):
    """Wrap ``method`` and return its execution time.
    """

    def wrapper(*args, **kwargs):
        start = time.time()
        result = method(*args, **kwargs)
        duration = time.time() - start
        return duration, result
    return wrapper


def parse_s4ext(filepath):
    metadata = {}
    with open(filepath) as file:
        for line in file:
            if not line.strip() or line.startswith("#"):
                continue
            fields = [field.strip() for field in line.split(' ', 1)]
            assert(len(fields) <= 2)
            metadata[fields[0]] = fields[1] if len(fields) == 2 else None
    return metadata


def read_dict(json_file):
    data = {}
    if os.path.exists(json_file):
        with open(json_file) as file:
            data = json.load(file)
    return data


def write_dict(json_file, data):
    with open(json_file, 'w') as file:
        file.write(json.dumps(data, indent=4))


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Checkout and update Slicer extension sources.')
    parser.add_argument("--filter",  default=".*", type=str,
                        help="Regular expression to select particular extensions (e.g 'ABC|Slicer.+')")
    parser.add_argument("--delete", action="store_true",
                        help="Delete previous source checkout.")
    parser.add_argument("/path/to/ExtensionsIndex")
    parser.add_argument("/path/to/ExtensionsSource")
    args = parser.parse_args()

    extensions_source_dir = os.path.abspath(os.path.expanduser(getattr(args, "/path/to/ExtensionsSource")))
    extensions_index_dir = os.path.abspath(os.path.expanduser(getattr(args, "/path/to/ExtensionsIndex")))

    log_context = {'repo_name' : 'None', 'repo_vcs': 'None'}

    logger.info("extensions_source_dir is [%s]" % extensions_source_dir, extra=log_context)
    logger.info("extensions_index_dir is [%s]" % extensions_index_dir, extra=log_context)

    file_match = "*.s4ext"

    stats_file = os.path.join(extensions_source_dir, "ExtensionsCheckoutTimes.json")
    stats = read_dict(stats_file)

    re_file_match = re.compile(args.filter)
    for filepath in glob.glob(os.path.join(extensions_index_dir, file_match)):
        extension_name = os.path.splitext(os.path.basename(filepath))[0]
        if not re_file_match.match(extension_name):
            continue
        metadata = parse_s4ext(filepath)
        log_context = {'repo_name' : extension_name, 'repo_vcs': metadata['scm']}
        if args.delete:
            extension_source_dir = os.path.join(extensions_source_dir, extension_name)
            if os.path.exists(extension_source_dir):
                logger.warning("Deleting %s" % extension_source_dir, extra=log_context)
                if extension_name in stats:
                    del stats[extension_name]
                    write_dict(stats_file, stats)
                shutil.rmtree(extension_source_dir)
        elapsed_time_collected = False
        if extension_name in stats:
            elapsed_time_collected = True
        url = metadata["scm"] + '+' + metadata["scmurl"] + "@" + metadata["scmrevision"]
        kwargs = {}
        for param_name in ['username', 'password']:
            if 'svn' + param_name in metadata:
                kwargs['svn_' + param_name] = metadata['svn' + param_name]
        repo = create_repo(url=url, parent_dir=extensions_source_dir, name=extension_name, **kwargs)
        duration, result = timecall(repo.update_repo)()
        repo.info("Elapsed time: {:.2f}s\n".format(duration))
        if not elapsed_time_collected:
            stats[extension_name] = duration

        write_dict(stats_file, stats)
