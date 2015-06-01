#!/usr/bin/env python

# This script will generate a user certificate using flocker-ca and upload it
# ready for the plugin to consume
# It will then upload an experimental build of docker (i.e. one that supports --volume-drvier)
# It will then git clone this repo and configure the plugin to run with the certs

import sys
import yaml

# Usage: plugin.py cluster.yml
from utils import Configurator

# allow env override for where to download the experimental docker binary from
DOCKER_BINARY_URL = os.environ.get("DOCKER_BINARY_URL")

if DOCKER_BINARY_URL is None:
    DOCKER_BINARY_URL = 'http://storage.googleapis.com/experiments-clusterhq/docker-binaries/docker-volumes'

if __name__ == "__main__":
    c = Configurator(configFile=sys.argv[1])
    control_ip = c.config["control_node"]
    print "Generating plugin certs"
    # generate and upload plugin.crt and plugin.key for each node
    for node in c.config["agent_nodes"]:
        # use the node IP to name the local files so they do not overwrite each other
        c.run("flocker-ca create-api-certificate %s" % (node + '-plugin',))
        print "Generated plugin certs for", node
        # upload the .crt and .key
        for ext in ("crt", "key"):
            c.scp("%s-plugin.%s" % (node, ext),
                node, "/etc/flocker/plugin.%s" % (ext,))
        print "Uploaded plugin certs for", node
