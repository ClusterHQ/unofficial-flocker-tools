#!/usr/bin/env python

# This script will use the correct repo to install packages for clusterhq-flocker-node

import sys

# Usage: deploy.py cluster.yml
from utils import Configurator

def main():
    c = Configurator(configFile=sys.argv[1])

    # Permit root access
    if c.config["os"] == "coreos":
        user = "core"
    elif c.config["os"] == "ubuntu":
        user = "ubuntu"
    elif c.config["os"] == "centos":
        user = "centos"
    cmd1 = "sudo mkdir -p /root/.ssh"
    cmd2 = "sudo cp /home/%s/.ssh/authorized_keys /root/.ssh/authorized_keys" % (user,)
    ips = []
    for node in c.config["agent_nodes"]:
        ips.append(node["public"])
    for public_ip in ips:
        c.runSSHRaw(public_ip, cmd1, username=user)
        c.runSSHRaw(public_ip, cmd2, username=user)
        print "Enabled root access to %s" % (public_ip,)
    if c.config["control_node"] not in ips:
        c.runSSHRaw(c.config["control_node"], cmd1, username=user)
        c.runSSHRaw(c.config["control_node"], cmd2, username=user)
        print "Enabled root access to %s" % (c.config["control_node"],)

    # Install flocker node software on all the nodes
    nodes = c.config["agent_nodes"]
    node_public_ips = [c["public"] for c in nodes]
    node_public_ips.append(c.config["control_node"])

    for public_ip in node_public_ips:
        if c.config["os"] == "ubuntu":
            c.runSSH(public_ip, """apt-get -y install apt-transport-https software-properties-common
add-apt-repository -y 'deb https://clusterhq-archive.s3.amazonaws.com/ubuntu-testing/14.04/$(ARCH) /'
apt-get update
curl -sSL https://get.docker.com/ | sh
apt-get -y --force-yes install clusterhq-flocker-node
""")
        elif c.config["os"] == "centos":
            c.runSSH(public_ip, """if selinuxenabled; then setenforce 0; fi
yum update
curl -sSL https://get.docker.com/ | sh
service docker start
test -e /etc/selinux/config && sed --in-place='.preflocker' 's/^SELINUX=.*$/SELINUX=disabled/g' /etc/selinux/config
yum install -y https://s3.amazonaws.com/clusterhq-archive/centos/clusterhq-release$(rpm -E %dist).noarch.rpm
yum install -y clusterhq-flocker-node
""")

    # if the dataset.backend is ZFS then install ZFS and mount a flocker pool
    # then create and distribute SSH keys amoungst the nodes
    if c.config["agent_config"]["dataset"]["backend"] == "zfs":
        # CentOS ZFS installation requires a restart
        # XXX todo - find out a way to handle a restart mid-script
        if c.config["os"] == "centos":
            print >> sys.stderr, (
                "Auto-install of ZFS on CentOS is "
                "not currently supported")
            sys.exit(1)
        if c.config["os"] == "coreos":
            print >> sys.stderr, (
                "Auto-install of ZFS on CoreOS is "
                "not currently supported")
            sys.exit(1)

        for node in c.config["agent_nodes"]:
            node_public_ip = node["public"]
            if c.config["os"] == "ubuntu":
                c.runSSH(node_public_ip, """echo installing-zfs
add-apt-repository -y ppa:zfs-native/stable
apt-get update
apt-get -y --force-yes install libc6-dev zfsutils
mkdir -p /var/opt/flocker
truncate --size 10G /var/opt/flocker/pool-vdev
zpool create flocker /var/opt/flocker/pool-vdev
""")

        """
        Loop over each node and generate SSH keys
        Then get the public key so we can distribute it to other nodes
        """
        for node in c.config["agent_nodes"]:
            node_public_ip = node["public"]
            print "Generating SSH Keys for %s" % (node_public_ip,)
            publicKey = c.runSSH(node_public_ip, """cat <<EOF > /tmp/genkeys.sh
#!/bin/bash
ssh-keygen -q -f /root/.ssh/id_rsa -N ""
EOF
bash /tmp/genkeys.sh
cat /root/.ssh/id_rsa.pub
rm /tmp/genkeys.sh
""")

            publicKey = publicKey.rstrip('\n')
            """
            Now we have the public key for the node we loop over all the other
            nodes and append it to /root/.ssh/authorized_keys
            """
            for othernode in c.config["agent_nodes"]:
                othernode_public_ip = othernode["public"]
                if othernode_public_ip != node_public_ip:
                    print "Copying %s key -> %s" % (
                        node_public_ip, othernode_public_ip,)
                    c.runSSH(othernode_public_ip, """cat <<EOF > /tmp/uploadkey.sh
#!/bin/bash
echo "%s" >> /root/.ssh/authorized_keys
EOF
bash /tmp/uploadkey.sh
rm /tmp/uploadkey.sh
""" % (publicKey,))

    print "Installed clusterhq-flocker-node on all nodes"
    print "To configure and deploy the cluster:"
    print "flocker-config cluster.yml"

if __name__ == "__main__":
    main()
