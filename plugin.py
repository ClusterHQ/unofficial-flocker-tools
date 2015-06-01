#!/usr/bin/env python

# This script will generate a user certificate using flocker-ca and upload it
# ready for the plugin to consume
# It will then upload an experimental build of docker (i.e. one that supports --volume-drvier)
# It will then git clone this repo and configure the plugin to run with the certs

import sys
import yaml

# Usage: deploy.py cluster.yml
from utils import Configurator

if __name__ == "__main__":
    c = Configurator(configFile=sys.argv[1])
    control_ip = c.config["control_node"]
    for node in c.config["agent_nodes"]:
        node_uuid = c.runSSHRaw(node, "python -c \"import json; print json.load(open('/etc/flocker/volume.json'))['uuid']\"")
        print "Installing flocker-docker-plugin on %s" % (node) 