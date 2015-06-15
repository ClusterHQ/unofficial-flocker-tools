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

def get_json(parent, url):
    client = get_client(parent)
    d = client.get(get_base_url(parent) + url)
    d.addCallback(treq.json_content)
    return d

def post_json(parent, url, data):
    client = get_client(parent)
    d = client.post(get_base_url(parent) + url,
            json.dumps(data),
            headers={'Content-Type': ['application/json']})
    d.addCallback(treq.json_content)
    return d

EVENT_TIMEOUT = 120

class MoveVolumes(Options):
    """
    create a volume and move it around forever.
    log if it ever gets stuck for more than a minute.
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
                for dataset in state:
                    if (dataset["dataset_id"] == dataset_id
                            and "primary" in dataset
                            and dataset["primary"] == next_node["uuid"]):
                        print "found dataset on next node in %.2f seconds!" % (time.time() - start_time,)
                        found = True
                time.sleep(1)
                sys.stdout.write(".")
                sys.stdout.flush()
                if time.time() - EVENT_TIMEOUT > start_time:
                    print "TIMED OUT :("
                    sys.exit(1)



commands = {
    "move-volumes": MoveVolumes,
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
