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
import treq
import texttable

def get_client():
    pwd = FilePath(os.getcwd())
    cluster = yaml.load(pwd.child("cluster.yml").open())
    return txflocker_get_client(certificates_path=pwd,
        user_certificate_filename="%s.crt" % (cluster["users"][0],),
        user_key_filename="%s.key" % (cluster["users"][0],),
    )


def get_base_url():
    pwd = FilePath(os.getcwd())
    control_config = yaml.load(pwd.child("agent.yml").open())["control-service"]
    control_config["port"] = 4523
    return "https://%(hostname)s:%(port)s/v1" % control_config


def get_table():
    table = texttable.Texttable(max_width=100)
    table.set_deco(0)
    return table


class Version(Options):
    """
    show version information
    """
    def run(self):
        print "flocker-volumes.py prototype version 0.0.1"
        print "see https://docs.clusterhq.com/en/latest/labs/"
        print


class ListNodes(Options):
    """
    show list of nodes in the configured cluster
    """
    def run(self):
        self.client = get_client()
        self.base_url = get_base_url()
        d = self.client.get(self.base_url + "/state/nodes")
        d.addCallback(treq.json_content)
        def print_table(nodes):
            table = get_table()
            table.set_cols_align(["l", "l"])
            table.add_rows([["", ""]] +
                           [["SERVER", "ADDRESS"]] +
                           [[node["uuid"], node["host"]] for node in nodes])
            print table.draw() + "\n"
        d.addCallback(print_table)
        return d


class List(Options):
    """
    list flocker datasets
    """
    optFlags = [
        ("deleted", "d", "Show deleted datasets"),
        #("human", "h", "Human readable numbers"), ?
    ]
    def run(self):
        self.client = get_client()
        self.base_url = get_base_url()
        ds = [self.client.get(self.base_url + "/configuration/datasets"),
              self.client.get(self.base_url + "/state/datasets"),
              self.client.get(self.base_url + "/state/nodes"),]
        for d in ds:
            d.addCallback(treq.json_content)
        d = defer.gatherResults(ds)
        def got_results(results):
            configuration_datasets, state_datasets, state_nodes = results

            # build up a table, based on which datasets are in the
            # configuration, adding data from the state as necessary
            configuration_map = dict((d["dataset_id"], d) for d in configuration_datasets)
            state_map = dict((d["dataset_id"], d) for d in configuration_datasets)
            nodes_map = dict((n["uuid"], n) for n in state_nodes)

            rows = []

            for (key, dataset) in configuration_map.iteritems():
                if dataset["deleted"] and self["deleted"]:
                    if key in state_map:
                        status = "deleting"
                    else:
                        status = "deleted"
                else:
                    if key in state_map:
                        if state_map[key]["primary"] in nodes_map:
                            status = "attached"
                        else:
                            status = "detached"
                    else:
                        # not deleted, not in state, probably waiting for it to
                        # show up.
                        status = "pending"

                meta = []
                for k, v in dataset["metadata"].iteritems():
                    meta.append("%s=%s" % (k, v))

                if dataset["primary"] in nodes_map:
                    primary = nodes_map[dataset["primary"]]
                    node = "%s (%s)" % (primary["uuid"][:8], primary["host"])

                rows.append([dataset["dataset_id"][:8],
                    "%.2fG" % (dataset["maximum_size"] / (1024 * 1024 * 1024.),),
                    ",".join(meta),
                    status,
                    node])

            table = get_table()
            table.set_cols_align(["l", "l", "l", "l", "l"])
            rows = [["", "", "", "", ""]] + [
                    ["DATASET", "SIZE", "METADATA", "STATUS", "SERVER"]] + rows
            table.add_rows(rows)
            print table.draw() + "\n"
        d.addCallback(got_results)
        return d


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
        def err(failure):
            log.err(failure)
            reactor.stop()
        d.addErrback(err)
        return d
    except UsageError, errortext:
        print errortext
        print 'Try --help for usage details.'
        sys.exit(1)


if __name__ == "__main__":
    react(main, sys.argv[1:])
