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
from txflocker.client import combined_state, parse_num, process_metadata
import sys
import yaml
import treq
import texttable
import json
import os

def get_client(options):
    cluster_yml = options["cluster-yml"]
    if "CONTAINERIZED" in os.environ:
        if cluster_yml.startswith("/"):
            cluster_yml = "/host" + cluster_yml
    cluster = FilePath(cluster_yml)
    if cluster.exists():
        config = yaml.load(cluster.open())
        certificates_path = cluster.parent()
        user = config["users"][0]
        control_service = None # figure it out based on cluster.yml
    else:
        certs_path = options["certs-path"]
        if "CONTAINERIZED" in os.environ:
            if certs_path.startswith("/"):
                certs_path = "/host" + certs_path
        certificates_path = FilePath(certs_path)
        if options["user"] is None:
            raise UsageError("must specify --user")
        user = options["user"]
        if options["control-service"] is None:
            raise UsageError("must specify --control-service")
        control_service = options["control-service"]

    user_certificate_filename = "%s.crt" % (user,)
    user_key_filename = "%s.key" % (user,)

    return txflocker_get_client(
        certificates_path=certificates_path,
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
    show list of nodes in the cluster
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
                           [[node["uuid"][:uuid_length], node["host"]]
                               for node in nodes])
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
        ("human", "h", "Human readable numbers"),
    ]
    def run(self):
        client = get_client(self.parent)
        base_url = get_base_url(self.parent)
        uuid_length = get_uuid_length(self["long"])

        d = combined_state(client, base_url, self["deleted"])
        def got_results(results):
            rows = []
            for result in results:
                rows.append([result["dataset_id"],
                    result["size"],
                    result["meta"],
                    result["status"],
                    ("<missing>" if result["node"] is None else
                        result["node"]["uuid"][:uuid_length]
                        + " (" + result["node"]["host"] + ")")])
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
    optParameters = [
        ("node", "n", None,
            "Initial primary node for dataset "
            "(any unique prefix of node uuid, see "
            "flocker-volumes list-nodes)"),
        ("metadata", "m", None,
            "Set volume metadata (\"a=b,c=d\")"),
        ("size", "s", None,
            "Set size in bytes (default), k, M, G, T"),
    ]
    def run(self):
        if not self.get("node"):
            raise UsageError("must specify --node")
        self.client = get_client(self.parent)
        self.base_url = get_base_url(self.parent)

        d = self.client.get(self.base_url + "/state/nodes")
        d.addCallback(treq.json_content)
        def got_nodes(nodes):
            args = {}

            # size
            if self["size"]:
                args["maximum_size"] = parse_num(self["size"])

            # primary node
            args["primary"] = filter_primary_node(self["node"], nodes)

            # metadata
            args["metadata"] = process_metadata(self["metadata"])

            # TODO: don't allow non-unique name in metadata (by
            # convention)

            d = self.client.post(
                    self.base_url + "/configuration/datasets",
                    json.dumps(args),
                    headers={'Content-Type': ['application/json']})
            d.addCallback(treq.json_content)
            return d
        d.addCallback(got_nodes)
        def created_dataset(result):
            print "created dataset in configuration, manually poll",
            print "state with 'flocker-volumes list' to see it",
            print "show up."
            print
            # TODO: poll the API until it shows up, give the user a nice
            # progress bar.
            # TODO: investigate bug where all datasets go to pending
            # during waiting for a dataset to show up.
        d.addCallback(created_dataset)
        return d


class Destroy(Options):
    """
    mark a dataset to be deleted
    """
    optParameters = [
        ("dataset", "d", None, "Dataset to destroy"),
    ]
    def run(self):
        if not self.get("dataset"):
            raise UsageError("must specify --dataset")

        self.client = get_client(self.parent)
        self.base_url = get_base_url(self.parent)
        d = self.client.get(self.base_url + "/configuration/datasets")
        d.addCallback(treq.json_content)
        def got_configuration(datasets):
            victim = filter_datasets(self["dataset"], datasets)
            d = self.client.delete(self.base_url +
                    "/configuration/datasets/%s"
                        % (victim,))
            d.addCallback(treq.json_content)
            return d
        d.addCallback(got_configuration)
        def done_deletion(result):
            print "marked dataset as deleted. poll list manually to see",
            print "it disappear."
            print
        d.addCallback(done_deletion)
        return d


def filter_primary_node(prefix, nodes):
    candidates = []
    for node in nodes:
        if node["uuid"].startswith(prefix):
            candidates.append(node)
    if len(candidates) == 0:
        raise UsageError("no node uuids matching %s" %
                (prefix,))
    if len(candidates) > 1:
        raise UsageError("%s is ambiguous node" %
                (prefix,))
    return candidates[0]["uuid"].encode("ascii")


def filter_datasets(prefix, datasets):
    candidates = []
    for dataset in datasets:
        if dataset["dataset_id"].startswith(prefix):
            candidates.append(dataset)
    if len(candidates) == 0:
        raise UsageError("no dataset uuids matching %s" %
                (prefix,))
    if len(candidates) > 1:
        raise UsageError("%s is ambiguous dataset" % (prefix,))
    return candidates[0]["dataset_id"].encode("ascii")


class Move(Options):
    """
    move a dataset from one node to another
    """
    optParameters = [
        ("dataset", "d", None, "Dataset to move (uuid)"),
        ("destination", "t", None, "New primary node (uuid) "
            "to move the dataset to"),
    ]
    def run(self):
        if not self.get("dataset"):
            raise UsageError("must specify --dataset")
        if not self.get("destination"):
            raise UsageError("must specify --destination")
        self.client = get_client(self.parent)
        self.base_url = get_base_url(self.parent)

        d1 = self.client.get(self.base_url + "/state/nodes")
        d1.addCallback(treq.json_content)
        d2 = self.client.get(self.base_url + "/configuration/datasets")
        d2.addCallback(treq.json_content)
        def got_results((nodes, datasets)):
            dataset = filter_datasets(self["dataset"], datasets)
            primary = filter_primary_node(self["destination"], nodes)
            args = {"primary": primary}
            d = self.client.post(
                    self.base_url
                        + "/configuration/datasets/%s" % (dataset,),
                    json.dumps(args),
                    headers={'Content-Type': ['application/json']})
            d.addCallback(treq.json_content)
            return d
        d = defer.gatherResults([d1, d2])
        d.addCallback(got_results)
        def initiated_move(result):
            print "initiated move of dataset, please check state",
            print "to observe it actually move."
            print
        d.addCallback(initiated_move)
        return d


commands = {
    "version": Version,
    "list-nodes": ListNodes,
    "list": List,
    "status": ListNodes,
    "ls": List,
    "create": Create,
    "destroy": Destroy,
    "move": Move,
}


class FlockerVolumesCommands(Options):
    optParameters = [
        ("cluster-yml", None, "./cluster.yml",
            "Location of cluster.yml file "
            "(makes other options unnecessary)"),
        ("certs-path", None, ".",
            "Path to certificates folder"),
        ("user", None, "user",
            "Name of user for which .key and .crt files exist"),
        ("cluster-crt", None, "cluster.crt",
            "Name of cluster cert file"),
        ("control-service", None, None,
            "Hostname or IP of control service"),
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
        # Fake some commandline args based on env vars
        argv = list(argv)
        if os.environ.get("FLOCKER_CERTS_PATH"):
            argv = ["--certs-path", os.environ["FLOCKER_CERTS_PATH"]] + argv
        if os.environ.get("FLOCKER_USER"):
            argv = ["--user", os.environ["FLOCKER_USER"]] + argv
        if os.environ.get("FLOCKER_CONTROL_SERVICE"):
            argv = ["--control-service", os.environ["FLOCKER_CONTROL_SERVICE"]] + argv
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


def _main():
    react(main, sys.argv[1:])

if __name__ == "__main__":
    _main()
