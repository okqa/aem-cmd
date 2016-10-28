# coding: utf-8
import optparse
import os
import sys

import requests

from acmd import OK, SERVER_ERROR
from acmd import tool, error, log
from acmd.tools.tool_utils import get_argument, get_command

parser = optparse.OptionParser("acmd assets <import|touch> [options] <file>")
parser.add_option("-r", "--raw",
                  action="store_const", const=True, dest="raw",
                  help="output raw response data")
parser.add_option("-D", "--dry-run",
                  action="store_const", const=True, dest="dry_run",
                  help="Do not change repository")
parser.add_option("-d", "--destination", dest="destination_root",
                  help="The root directory to import to")


@tool('assets')
class AssetsTool(object):
    """ Manage AEM DAM assets """

    @staticmethod
    def execute(server, argv):
        options, args = parser.parse_args(argv)
        action = get_command(args)
        actionarg = get_argument(args)

        if action == 'import':
            return import_path(server, options, actionarg)
        return OK


def import_path(server, options, path):
    if os.path.isdir(path):
        return import_directory(server, options, path)
    else:
        return import_file(server, options, path)


def import_directory(server, options, rootdir):
    log("Importing file {}".format(rootdir))
    for subdir, dirs, files in os.walk(rootdir):
        # _create_dir(server, subdir)
        for filename in files:
            filepath = os.path.join(subdir, filename)
            if _filter(filename):
                log("Skipping {}".format(filepath))
                continue
            status = import_file(server, options, rootdir, filepath)
            if status != OK:
                return status


def _filter(filename):
    return filename.startswith(".")


def import_file(server, options, import_root, filepath):
    assert os.path.isfile(filepath)

    local_dir = os.path.dirname(filepath)

    dest_dir = options.destination_root
    if dest_dir is None:
        dest_dir = os.path.join('/content/dam', os.path.basename(import_root))

    dam_path = local_dir.replace(import_root, dest_dir)
    log("Uplading {} to {}".format(filepath, dam_path))

    if options.dry_run:
        return OK
    status = _create_dir(server, dam_path)
    if status != OK:
        return status
    status = _post_file(server, filepath, dam_path)
    return status


# curl -s -u admin:admin -X POST -F "jcr:primaryType=sling:OrderedFolder" $HOST$dampath > /dev/null
def _create_dir(server, path):
    form_data = {'jcr:primaryType': 'sling:OrderedFolder'}
    url = server.url(path)
    log("POSTing to {}".format(url))
    resp = requests.post(url, auth=server.auth, data=form_data)
    if not _ok(resp.status_code):
        error("Failed to create directory {}\n{}".format(url, resp.content))
        return SERVER_ERROR
    return OK


# curl -v -u admin:admin -X POST -i -F "file=@\"$FILENAME\"" $HOST$dampath.createasset.html &> $tempfile
def _post_file(server, filepath, dst_path):
    filename = os.path.basename(filepath)
    form_data = dict(
        file=(filename, open(filepath, 'rb'), "application/octet-stream", dict()),
        fileName=filename
    )

    url = server.url("{path}.createasset.html".format(path=dst_path, filename=os.path.basename(filepath)))
    log("POSTing to {}".format(url))
    resp = requests.post(url, auth=server.auth, data=form_data)
    if not _ok(resp.status_code):
        error("Failed to upload file {}\n{}".format(filepath, resp.content))
        return SERVER_ERROR
    sys.stdout.write("{}/{}\n".format(dst_path, os.path.basename(filepath)))
    return OK


def _ok(status_code):
    return status_code == 200 or status_code == 201