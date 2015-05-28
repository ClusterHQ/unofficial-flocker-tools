#!/usr/bin/env python
import sys
import yaml
from utils import Configurator
if __name__ == "__main__":
    c = Configurator(configFile=sys.argv[1])
    if not c.config["users"]:
        print "no users!"
    else:
        node_mapping = yaml.load(open("node_mapping.yml"))
        prefix = ("curl -s --cacert $PWD/cluster.crt --cert $PWD/%(user)s.crt "
                  "--key $PWD/%(user)s.key" % dict(user=c.config["users"][0],))
        url = "https://%(control_node)s:4523/v1" % dict(control_node=c.config["control_node"],)
        header = ' --header "Content-type: application/json"'
        print "\nThis should create a volume on a node:"
        print "NODE_UUID=" + node_mapping.values()[0]
        print prefix + header + """ -XPOST -d '{"primary": "'${NODE_UUID}'", "maximum_size": 107374182400, "metadata": {"name": "mongodb_data"}}' """,
        print url + "/configuration/datasets| jq ."
        print "\nThen record the dataset_id (you'll need it later)..."
        print "DATASET_ID=..."
        print "\nWait for your dataset to show up..."
        print prefix + " " + url + "/state/datasets | jq ."
        print "\nThen create a container with the volume"
        print prefix + header + """ -XPOST -d '{"node_uuid": "'${NODE_UUID}'", "name": "mongodb", """,
        print """"image": "clusterhq/mongodb:latest", "ports": [{"internal": 27017, "external": 27017}], """,
        print """"volumes": [{"dataset_id": "'${DATASET_ID}'", "mountpoint": "/data/db"}]}' """ + url + "/configuration/containers | jq ."
        print "\nThen wait for the container to show up..."
        print prefix + " " + url + "/state/containers | jq ."
        print "Now move the container to another machine, and the dataset will follow!"
        print "NODE_UUID_2=" + node_mapping.values()[1]
        print prefix + header + """ -XPOST -d '{"primary": "'${NODE_UUID_2}'"}' """ + url + "/configuration/containers/mongodb | jq ."
