#!/usr/bin/env python

# This script will generate some certificates using flocker-ca and upload them
# to the servers specified in a cluster.yml

import sys
import yaml

# Usage: deploy.py cluster.yml
from utils import Configurator

if __name__ == "__main__":
    c = Configurator(configFile=sys.argv[1])
    c.run("flocker-ca initialize %s" % (c.config["cluster_name"],))
    print "Initialized cluster CA."
    c.run("flocker-ca create-control-certificate %s" % (c.config["control_node"],))
    print "Created control cert."
    node_mapping = {}
    for node in c.config["agent_nodes"]:
        public_ip = node["public"]
        # Created 8eab4b8d-c0a2-4ce2-80aa-0709277a9a7a.crt. Copy ...
        uuid = c.run("flocker-ca create-node-certificate").split(".")[0].split(" ")[1]
        node_mapping[public_ip] = uuid
        print "Generated", uuid, "for", public_ip
    for user in c.config["users"]:
        c.run("flocker-ca create-api-certificate %s" % (user,))
        print "Created user key for", user
    print "Uploading keys to respective nodes:"

    # Copy cluster cert, and control cert and key to control node.
    c.runSSHRaw(c.config["control_node"], "mkdir -p /etc/flocker")
    c.scp("cluster.crt", c.config["control_node"], "/etc/flocker/cluster.crt")
    print " * Uploaded cluster cert to control node."
    for ext in ("crt", "key"):
        c.scp("control-%s.%s" % (c.config["control_node"], ext),
                c.config["control_node"], "/etc/flocker/control-service.%s" % (ext,))
    print " * Uploaded control cert & key to control node."

    # Dump agent_config into a file and scp it to /etc/flocker/agent.yml on the
    # nodes.
    f = open("agent.yml", "w")
    agent_config = yaml.dump(c.config["agent_config"], f)
    f.close()

    # Record the node mapping for later.
    f = open("node_mapping.yml", "w")
    agent_config = yaml.dump(node_mapping, f)
    f.close()

    # Copy cluster cert, and agent cert and key to agent nodes.
    for node, uuid in node_mapping.iteritems():
        c.runSSHRaw(node, "mkdir -p /etc/flocker")
        c.scp("cluster.crt", node, "/etc/flocker/cluster.crt")
        c.scp("agent.yml", node, "/etc/flocker/agent.yml")
        print " * Uploaded cluster cert to %s." % (node,)
        for ext in ("crt", "key"):
            c.scp("%s.%s" % (uuid, ext), node, "/etc/flocker/node.%s" % (ext,))
        print " * Uploaded node cert and key to %s." % (node,)

    for node, uuid in node_mapping.iteritems():
        if c.config["os"] == "ubuntu":
            c.runSSH(node, """apt-get -y install apt-transport-https software-properties-common
service flocker-container-agent restart
service flocker-dataset-agent restart
""")
        elif c.config["os"] == "centos":
            c.runSSH(node, """if selinuxenabled; then setenforce 0; fi
systemctl enable docker.service
systemctl start docker.service
""")

    if c.config["os"] == "ubuntu":
        c.runSSH(c.config["control_node"], """cat <<EOF > /etc/init/flocker-control.override
start on runlevel [2345]
stop on runlevel [016]
EOF
echo 'flocker-control-api       4523/tcp                        # Flocker Control API port' >> /etc/services
echo 'flocker-control-agent     4524/tcp                        # Flocker Control Agent port' >> /etc/services
service flocker-control restart
ufw allow flocker-control-api
ufw allow flocker-control-agent
""")
    elif c.config["os"] == "centos":
        c.runSSH(c.config["control_node"], """systemctl enable flocker-control
systemctl start flocker-control
firewall-cmd --permanent --add-service flocker-control-api
firewall-cmd --add-service flocker-control-api
firewall-cmd --permanent --add-service flocker-control-agent
firewall-cmd --add-service flocker-control-agent
""")
    print "Configured and started control service, opened firewall."

    if c.config["users"]:
        print "\nYou should now be able to communicate with the control service, for example:\n"
        prefix = ("curl -s --cacert $PWD/cluster.crt --cert $PWD/%(user)s.crt "
                  "--key $PWD/%(user)s.key" % dict(user=c.config["users"][0],))
        url = "https://%(control_node)s:4523/v1" % dict(control_node=c.config["control_node"],)
        header = ' --header "Content-type: application/json"'
        print "This should give you a list of your nodes:"
        print prefix + " " + url + "/state/nodes | jq ."
        print "Try running tutorial.py cluster.yml for more..."
