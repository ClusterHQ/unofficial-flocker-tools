#!/usr/bin/env python

"""
A prototype version of a CLI tool which shows off flocker's first class
volumes capabilities.

Run me from a directory containing a cluster.yml and appropriate cluster
certificates, or specify --cluster-crt, --user-crt, --user-key, and
--control-service.
"""

from twisted.internet import defer
from twisted.internet.task import react
from twisted.python.usage import Options, UsageError
from twisted.python import log
from twisted.python.filepath import FilePath
from txflocker.client import get_client as txflocker_get_client
import sys
import yaml
import treq
import texttable

def get_client(options):
    cluster = FilePath(options["cluster-yml"])
    if cluster.exists():
        config = yaml.load(cluster.open())
        certificates_path = cluster.parent()
        user_certificate_filename = "%s.crt" % (config["users"][0],)
        user_key_filename = "%s.key" % (config["users"][0],)
        control_service = None # figure it out based on cluster.yml
    else:
        certificates_path = FilePath(options["certs-path"])
        certificates_path = FilePath(options["certs-path"])
        if options["user"] is None:
            raise UsageError("must specify --user")
        user_certificate_filename = "%s.crt" % (options["user"],)
        user_key_filename = "%s.key" % (options["user"],)
        if options["control-service"] is None:
            raise UsageError("must specify --control-service")
        control_service = options["control-service"]

    return txflocker_get_client(certificates_path=certificates_path,
        user_certificate_filename=user_certificate_filename,
        user_key_filename=user_key_filename,
        target_hostname=control_service,
    )


def get_base_url(options):
    pwd = FilePath(options["certs-path"])
    if options["control-service"] is not None:
        control_config = {"hostname": options["control-service"]}
    else:
        control_config = yaml.load(
                pwd.child("agent.yml").open())["control-service"]
    control_config["port"] = options["control-port"]
    return "https://%(hostname)s:%(port)s/v1" % control_config


def get_table():
    table = texttable.Texttable(max_width=140)
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
    optFlags = [
        ("long", "l", "Show long UUIDs"),
    ]
    def run(self):
        self.client = get_client(self.parent)
        self.base_url = get_base_url(self.parent)
        uuid_length = get_uuid_length(self["long"])
        d = self.client.get(self.base_url + "/state/nodes")
        d.addCallback(treq.json_content)
        def print_table(nodes):
            table = get_table()
            table.set_cols_align(["l", "l"])
            table.add_rows([["", ""]] +
                           [["SERVER", "ADDRESS"]] +
                           [[node["uuid"][:uuid_length], node["host"]] for node in nodes])
            print table.draw() + "\n"
        d.addCallback(print_table)
        return d


def get_uuid_length(long_):
    if long_:
        uuid_length = 100
    else:
        uuid_length = 8
    return uuid_length


class List(Options):
    """
    list flocker datasets
    """
    optFlags = [
        ("deleted", "d", "Show deleted datasets"),
        ("long", "l", "Show long UUIDs"),
        #("human", "h", "Human readable numbers"), ?
    ]
    def run(self):
        self.client = get_client(self.parent)
        self.base_url = get_base_url(self.parent)
        uuid_length = get_uuid_length(self["long"])

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
            state_map = dict((d["dataset_id"], d) for d in state_datasets)
            nodes_map = dict((n["uuid"], n) for n in state_nodes)

            rows = []

            for (key, dataset) in configuration_map.iteritems():
                if dataset["deleted"]:
                    # the user has asked to see deleted datasets
                    if self["deleted"]:
                        if key in state_map:
                            status = "deleting"
                        else:
                            status = "deleted"
                    # we are hiding deleted datasets
                    else:
                        continue
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
                    node = "%s (%s)" % (primary["uuid"][:uuid_length], primary["host"])

                if dataset.get("maximum_size"):
                    size = "%.2fG" % (dataset["maximum_size"] / (1024 * 1024 * 1024.),)
                else:
                    # must be a backend with quotas instead of sizes
                    size = "<no quota>"

                rows.append([dataset["dataset_id"][:uuid_length],
                    size,
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


def parse_num(num, unit):
    unit = unit.lower()
    if unit == 'tb' or unit == 't' or unit =='tib':
        return int(float(num)*1024*1024*1024*1024)
    elif unit == 'gb' or unit == 'g' or unit =='gib':
        return int(float(num)*1024*1024*1024)
    elif unit == 'mb' or unit == 'm' or unit =='mib':
        return int(float(num)*1024*1024)
    elif unit == 'kb' or unit == 'k' or unit =='kib':
        return int(float(num)*1024)
    else:
        return int(float(num))


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
        # TODO search the list of nodes for one prefix
        self.client = get_client(self.parent)
        self.base_url = get_base_url(self.parent)
        d = self.client.post(self.base_url + "/configuration/datasets",
                {"maximum_size": parse_num(self["size"])})
        d.addCallback(treq.json_content)
        return d


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
    optParameters = [
        ("cluster-yml", None, "./cluster.yml",
            "Location of cluster.yml file"),
        ("certs-path", None, ".",
            "Path to certificates folder"),
        ("user", None, "user",
            "Name of user (expects user.key and user.crt)"
            "(if no cluster.yml)"),
        ("cluster-crt", None, "cluster.crt",
            "Name of cluster cert file "
            "(if no cluster.yml)"),
        ("control-service", None, None,
            "Hostname or IP of control service "
            "(if no cluster.yml)"),
        ("control-port", None, 4523,
            "Port for control service REST API"),
    ]
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
        def usageError(failure):
            failure.trap(UsageError)
            print str(failure.value)
            return # skips verbose exception printing
        d.addErrback(usageError)
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
