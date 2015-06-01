#!/usr/bin/env python

# This script will generate a user certificate using flocker-ca and upload it
# ready for the plugin to consume
# It will then upload an experimental build of docker (i.e. one that supports --volume-drvier)
# It will then git clone this repo and configure the plugin to run with the certs

import sys
import yaml
import os

# Usage: plugin.py cluster.yml
from utils import Configurator

# allow env override for where to download the experimental docker binary from
DOCKER_BINARY_URL = os.environ.get("DOCKER_BINARY_URL")

if DOCKER_BINARY_URL is None:
    DOCKER_BINARY_URL = 'http://storage.googleapis.com/experiments-clusterhq/docker-binaries/docker-volumes'

# perhaps the name of the docker service running on the host is different to 'docker'
# for example - the clusterhq-flocker-node package installed 'docker.io'
DOCKER_SERVICE_NAME = os.environ.get("DOCKER_SERVICE_NAME")

if DOCKER_SERVICE_NAME is None:
    DOCKER_SERVICE_NAME = 'docker'

if __name__ == "__main__":
    c = Configurator(configFile=sys.argv[1])
    control_ip = c.config["control_node"]
    print "Generating plugin certs"
    # generate and upload plugin.crt and plugin.key for each node
    for node in c.config["agent_nodes"]:
        break;
        # use the node IP to name the local files so they do not overwrite each other
        c.run("flocker-ca create-api-certificate %s" % (node + '-plugin',))
        print "Generated plugin certs for", node
        # upload the .crt and .key
        for ext in ("crt", "key"):
            c.scp("%s-plugin.%s" % (node, ext),
                node, "/etc/flocker/plugin.%s" % (ext,))
        print "Uploaded plugin certs for", node

    # download and replace the docker binary on each of the nodes
    for node in c.config["agent_nodes"]:

        # stop the docker service
        print "Stopping the docker service on %s - %s" % (node, DOCKER_SERVICE_NAME)
        if c.config["os"] == "ubuntu":
          c.runSSHRaw(node, "stop %s" % (DOCKER_SERVICE_NAME))
        elif c.config["os"] == "centos":
          c.runSSHRaw(node, "systemctl stop %s.service" % (DOCKER_SERVICE_NAME))

        # download the latest docker binary\
        print "Downloading the latest docker binary on %s - %s" % (node, DOCKER_BINARY_URL)
        c.runSSHRaw(node, "wget -O /usr/bin/docker %s" % (DOCKER_BINARY_URL))

        # stop the docker service
        print "Starting the docker service on %s" % (node)
        if c.config["os"] == "ubuntu":
          c.runSSHRaw(node, "start %s" % (DOCKER_SERVICE_NAME))
        elif c.config["os"] == "centos":
          c.runSSHRaw(node, "systemctl start %s.service" % (DOCKER_SERVICE_NAME))