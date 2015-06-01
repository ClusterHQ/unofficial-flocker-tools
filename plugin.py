#!/usr/bin/env python

# This script will generate a user certificate using flocker-ca and upload it
# ready for the plugin to consume
# It will then upload an experimental build of docker (i.e. one that supports --volume-drvier)
# It will then git clone this repo and configure the plugin to run with the certs

import sys
import yaml

# Usage: plugin.py cluster.yml
from utils import Configurator

if __name__ == "__main__":
    c = Configurator(configFile=sys.argv[1])
    control_ip = c.config["control_node"]
    print "Generating plugin certs"
    for node in c.config["agent_nodes"]:
        c.run("flocker-ca create-api-certificate %s" % (node + '-plugin',))
        print "Generated plugin certs for", node
        for ext in ("crt", "key"):
            c.scp("%s-plugin.%s" % (node, ext),
                node, "/etc/flocker/plugin.%s" % (ext,))
        print "Uploaded plugin certs for", node
