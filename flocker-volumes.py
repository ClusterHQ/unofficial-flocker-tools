#!/usr/bin/env python

"""
A prototype version of a CLI tool which shows off flocker's first class volumes
capabilities.
"""

from twisted.python.usage import Options, UsageError
import sys
from twisted.internet.task import react

class Version(Options):
    def run(self):
        print "Ho ho ho"


class List(Options):
    optFlags = [
        ("deleted", "d", "Show deleted datasets")
    ]
    def run(self):
        pass


class ListNodes(Options):
    def run(self):
        pass


class Create(Options):
    optFlags = [
        ("host", "h", "Initial host for dataset to appear on"),
        ("metadata", "m", "Set volume metadata"),
        ("size", "s", "Size", "Set size in bytes (default), k, M, G, T"),
    ]
    def run(self):
        pass


class Destroy(Options):
    synopsis = '<dataset_uuid>'
    def run(self):
        pass

class Move(Options):
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
    except UsageError as e:
        raise SystemExit(str(e))


if __name__ == "__main__":
    react(main, sys.argv[1:])

"""
Later ideas:

TODO: make it possible to see which containers are using which volumes via metadata updates.

$ ./flocker-volumes.py list
DATASET    SERVER   CONTAINERS      SIZE    METADATA
1921edea   1.2.3.4  pgsql7,pgsql9   30GB    name=postgresql_7
14f2fa0c   1.2.3.5  pgsql8          30GB    name=postgresql_8
b31a0311   <none>   <none>          30GB    name=nonmanifest

$ ./flocker-volumes.py destroy name=badger
Volume c548725a is currently in use. Please stop it first.

TODO: make metadata name be special/unique.

$ ./flocker-volumes.py create --size 30g name=badger
Volume "badger" already exists. Please choose another name.
"""
