#!/usr/bin/env python

"""
A prototype version of a CLI tool which shows off flocker's first class volumes
capabilities.

Run me from a directory containing a cluster.yml and appropriate cluster
certificates.
"""

from twisted.internet import defer
from twisted.internet.task import react
from twisted.python.usage import Options, UsageError
from twisted.python import log
from twisted.python.filepath import FilePath
from txflocker.client import get_client as txflocker_get_client
import sys
import os
import yaml

def get_client():
    pwd = FilePath(os.getcwd())
    cluster = yaml.load(pwd.child("cluster.yml").open())
    return txflocker_get_client(certificates_path=pwd,
        user_certificate_filename="%s.crt" % (cluster["users"][0],),
        user_key_filename="%s.key" % (cluster["users"][0],),
    )

class Version(Options):
    """
    show version information
    """
    def run(self):
        print "flocker-volumes.py prototype version 0.0.1"


class ListNodes(Options):
    """
    show list of nodes in the configured cluster
    """
    def run(self):
        self.client = get_client()


class List(Options):
    """
    list flocker datasets
    """
    optFlags = [
        ("deleted", "d", "Show deleted datasets")
    ]
    def run(self):
        pass


class Create(Options):
    """
    create a flocker dataset
    """
    optFlags = [
        ("host", "h", "Initial host for dataset to appear on"),
        ("metadata", "m", "Set volume metadata"),
        ("size", "s", "Size", "Set size in bytes (default), k, M, G, T"),
    ]
    def run(self):
        pass


class Destroy(Options):
    """
    mark a dataset to be deleted
    """
    synopsis = '<dataset_uuid>'
    def run(self):
        pass


class Move(Options):
    """
    move a dataset from one host to another
    """
    synopsis = '<dataset_uuid> <host_uuid>'
    def run(self):
        pass


commands = {
    "version": Version,
    "list-nodes": ListNodes,
    "list": List,
    "create": Create,
    "destroy": Destroy,
    "move": Move,
}


class FlockerVolumesCommands(Options):
    subCommands = [
        (cmd, None, cls, cls.__doc__)
        for cmd, cls
        in sorted(commands.iteritems())]


def main(reactor, *argv):
    try:
        base = FlockerVolumesCommands()
        base.parseOptions(argv)
        if base.subCommand is not None:
            d = defer.maybeDeferred(base.subOptions.run)
        else:
            raise UsageError("Please specify a command.")
        d.addErrback(log.err)
        return d
    except UsageError, errortext:
        print errortext
        print 'Try --help for usage details.'
        sys.exit(1)


if __name__ == "__main__":
    react(main, sys.argv[1:])