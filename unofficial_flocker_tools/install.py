#!/usr/bin/env python

# This script will use the correct repo to install packages for clusterhq-flocker-node

import sys

# Usage: deploy.py cluster.yml
from utils import Configurator, verify_socket, log
from twisted.internet.task import react
from twisted.internet.defer import gatherResults, inlineCallbacks
from twisted.python.filepath import FilePath

def report_completion(result, public_ip, message="Completed install for"):
    log(message, public_ip)
    return result

class UsageError(Exception):
    pass

@inlineCallbacks
def main(reactor, configFile):
    c = Configurator(configFile=configFile)

    # Check that key file is accessible. If it isn't, give an error that
    # doesn't include the container-wrapping `/host/` to avoid confusing the
    # user.
    if not FilePath(c.get_container_facing_key_path()).exists():
        raise UsageError(
            "Private key specified in private_key_path in config does not exist at: %s" %
                (c.get_user_facing_key_path(),))

    # Permit root access
    if c.config["os"] == "coreos":
        user = "core"
    elif c.config["os"] == "ubuntu":
        user = "ubuntu"
    elif c.config["os"] == "centos":
        user = "centos"

    # Gather IPs of all nodes
    nodes = c.config["agent_nodes"]
    node_public_ips = [n["public"] for n in nodes]
    node_public_ips.append(c.config["control_node"])

    # Wait for all nodes to boot
    yield gatherResults([verify_socket(ip, 22, timeout=600) for ip in node_public_ips])

    # Enable root access
    cmd1 = "sudo mkdir -p /root/.ssh"
    cmd2 = "sudo cp /home/%s/.ssh/authorized_keys /root/.ssh/authorized_keys" % (user,)
    deferreds = []
    for public_ip in node_public_ips:
        d = c.runSSHAsync(public_ip, cmd1 + " && " + cmd2, username=user)
        d.addCallback(report_completion, public_ip=public_ip, message="Enabled root login for")
        deferreds.append(d)
    yield gatherResults(deferreds)

    # Install flocker node software on all the nodes
    deferreds = []
    for public_ip in node_public_ips:
        if c.config["os"] == "ubuntu":
            log("Running install for", public_ip, "...")
            d = c.runSSHAsync(public_ip, """apt-get -y install apt-transport-https software-properties-common
add-apt-repository -y 'deb https://clusterhq-archive.s3.amazonaws.com/ubuntu-testing/14.04/$(ARCH) /'
apt-get update
curl -sSL https://get.docker.com/ | sh
apt-get -y --force-yes install clusterhq-flocker-node
""")
            d.addCallback(report_completion, public_ip=public_ip)
            deferreds.append(d)
        elif c.config["os"] == "centos":
            d = c.runSSHAsync(public_ip, """if selinuxenabled; then setenforce 0; fi
yum update
curl -sSL https://get.docker.com/ | sh
service docker start
test -e /etc/selinux/config && sed --in-place='.preflocker' 's/^SELINUX=.*$/SELINUX=disabled/g' /etc/selinux/config
yum install -y https://s3.amazonaws.com/clusterhq-archive/centos/clusterhq-release$(rpm -E %dist).noarch.rpm
yum install -y clusterhq-flocker-node
""")
            d.addCallback(report_completion, public_ip=public_ip)
            deferreds.append(d)
    yield gatherResults(deferreds)

    # if the dataset.backend is ZFS then install ZFS and mount a flocker pool
    # then create and distribute SSH keys amoungst the nodes
    if c.config["agent_config"]["dataset"]["backend"] == "zfs":
        # CentOS ZFS installation requires a restart
        # XXX todo - find out a way to handle a restart mid-script
        if c.config["os"] == "centos":
            log("Auto-install of ZFS on CentOS is not currently supported")
            sys.exit(1)
        if c.config["os"] == "coreos":
            log("Auto-install of ZFS on CoreOS is not currently supported")
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
            log("Generating SSH Keys for %s" % (node_public_ip,))
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
                    log("Copying %s key -> %s" % (node_public_ip, othernode_public_ip,))
                    c.runSSH(othernode_public_ip, """cat <<EOF > /tmp/uploadkey.sh
#!/bin/bash
echo "%s" >> /root/.ssh/authorized_keys
EOF
bash /tmp/uploadkey.sh
rm /tmp/uploadkey.sh
""" % (publicKey,))

    log("Installed clusterhq-flocker-node on all nodes")

def _main():
    react(main, sys.argv[1:])

if __name__ == "__main__":
    _main()
