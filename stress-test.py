#!/usr/bin/env python

"""
Stress test Flocker via the API in an attempt to expose stability bugs in a
more reproducible way (and improve confidence in stability).
"""

from twisted.internet import defer
from twisted.internet.task import react
from twisted.python.usage import Options, UsageError
from twisted.python import log
import sys
import treq
import json
from common import get_client, get_base_url, FlockerCommands
import random
import time

def print_timing(result, start_time):
    print "API request completed in %.2f" % (time.time() - start_time)
    return result

def get_json(parent, url):
    # TODO optional timeout
    client = get_client(parent)
    start_time = time.time()
    d = client.get(get_base_url(parent) + url)
    d.addCallback(treq.json_content)
    d.addBoth(print_timing, start_time=start_time)
    return d

def post_json(parent, url, data):
    # TODO optional timeout
    client = get_client(parent)
    start_time = time.time()
    d = client.post(get_base_url(parent) + url,
            json.dumps(data),
            headers={'Content-Type': ['application/json']})
    d.addCallback(treq.json_content)
    d.addBoth(print_timing, start_time=start_time)
    return d

EVENT_TIMEOUT = 300

class CreateContainers(Options):
    """
    create a configurable number of stateful containers spread evenly across
    all nodes.
    fail if any flocker API request takes longer than configurable timeout.
    """
    optParameters = [
        ("number", "n", 800, "Number of containers"),
        ("timeout", "t", 20, "Timeout in seconds"),
    ]
    @defer.inlineCallbacks
    def run(self):
        self.number = int(self["number"])
        self.timeout = int(self["timeout"])

        nodes = sorted((yield get_json(self.parent, "/state/nodes")))

        for run in range(self.number):
            port = 10000 + run
            target_node = nodes[run % len(nodes)]
            # Create a dataset and wait for it to show up in the
            # configuration
            dataset_name = "run_%d" % (run,)
            print "STARTING RUN %d" % (run,)
            print "Creating volume on %s" % (target_node,)
            response = yield post_json(self.parent,
                    "/configuration/datasets",
                    dict(
                        primary=target_node["uuid"],
                        metadata=dict(name=dataset_name)))
            print response
            dataset_id = response["dataset_id"].encode("ascii")
            # Create a container with a realistic amount of configuration
            # and wait for it to show up in the configuration
            print "Creating container on %s" % (target_node,)
            response = yield post_json(self.parent,
                    "/configuration/containers",
                    {"node_uuid": target_node["uuid"],
                        "name": "mongo_%d" % (run,), "image": "mongodb",
                        "ports": [{"external": port, "internal": 27017}],
                        "environment": {"ADMIN_PASS": "xxxxxxxxxxxxxxxx",
                            "ADMIN_USER": "xxxxxxxxxxxxxxxx",
                            "CONSUL_ACL_TOKEN": "xxxxxxxxxxxxxxxxxxxxxxxxxx"
                                               "xxxxxxxxxx",
                            "CONSUL_PASS": "xxxxxxxxxxxxxxxxxxxxxxxx",
                            "CONSUL_PREFIX": "xxxxxxxxxx",
                            "CONSUL_USER": "xxxxxxxxx",
                            "CONTAINERNAME": "xxxxxxxxxxxxxxxx",
                            "MAX_CONNECTIONS": "10",
                            "MGD_HOST": "xxxxxxxxxxxxxxxx",
                            "MGD_PORT": "10000",
                            "MGMT_PASS": "xxxxxxxxxxxxxxxx",
                            "MGMT_USER": "xxxxxxxxxxxxxxxx",
                            "MONGODB_ROLE": "xxxxxxxxxx",
                            "MONITORING_PASS": "xxxxxxxxxxxxxxxx",
                            "MONITORING_USER": "xxxxxxxxxxxxxxxx",
                            "SDM_ADAPTER": "xxxxxx",
                            "SDM_HOST": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                                       "xxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                            "SERVICE_PERSISTENCY": "true"},
                        "volumes": [{"dataset_id": dataset_id,
                            "mountpoint": "/data/db"}]})
            print response


class MoveVolumes(Options):
    """
    create a volume and move it around forever.
    log if it ever gets stuck for more than five minutes.
    """
    optParameters = [
        ("dataset", "d", None, "Dataset to move (uuid)"),
        ("destination", "t", None, "New primary node (uuid) "
            "to move the dataset to"),
    ]
    @defer.inlineCallbacks
    def run(self):
        volume_name = "stress_" + str(random.randrange(10000, 99999))
        print "Going to create", volume_name
        nodes = sorted((yield get_json(self.parent, "/state/nodes")))
        print nodes

        current_node_index = 0
        initial = nodes[current_node_index]
        print "Creating volume on %s" % (initial,)

        response = yield post_json(self.parent, "/configuration/datasets",
                dict(primary=initial["uuid"], metadata=dict(name=volume_name)))
        print response

        dataset_id = response["dataset_id"].encode("ascii")
        print "Waiting for dataset to appear in state"
        found = False
        start_time = time.time()
        while not found:
            time.sleep(1)
            sys.stdout.write(".")
            sys.stdout.flush()

            if time.time() - EVENT_TIMEOUT > start_time:
                print "TIMED OUT :("
                sys.exit(1)

            state = yield get_json(self.parent, "/state/datasets")
            for dataset in state:
                if (dataset["dataset_id"] == dataset_id
                        and "primary" in dataset
                        and dataset["primary"] == initial["uuid"]):
                    print "found dataset on initial node in %.2f seconds!" % (time.time() - start_time,)
                    found = True

        while True:
            # move to the next node
            current_node_index += 1
            next_node = nodes[current_node_index % len(nodes)]
            print "Moving to", next_node

            response = yield post_json(self.parent, "/configuration/datasets/%s" % (dataset_id,),
                    dict(primary=next_node["uuid"]))
            print response

            found = False
            start_time = time.time()
            while not found:
                state = yield get_json(self.parent, "/state/datasets")

                matching_datasets = []
                for dataset in state:
                    if dataset["dataset_id"] == dataset_id:
                        matching_datasets.append(dataset)

                sys.stdout.write(str(len(matching_datasets)) + " ")
                sys.stdout.flush()

                if len(matching_datasets) == 1:
                    if ("primary" in matching_datasets[0] and
                            matching_datasets[0]["primary"] == next_node["uuid"]):
                        print "found dataset uniquely on next node in %.2f seconds!" % (time.time() - start_time,)
                        found = True

                time.sleep(1)
                if time.time() - EVENT_TIMEOUT > start_time:
                    print "TIMED OUT :("
                    sys.exit(1)


commands = {
    "move-volumes": MoveVolumes,
    "create-containers": CreateContainers,
}

def main(reactor, *argv):
    try:
        base = FlockerCommands(commands)
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
