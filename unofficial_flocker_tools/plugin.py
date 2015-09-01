#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This script will generate a user certificate using flocker-ca and upload it
# ready for the plugin to consume
# It will then install a build of docker that supports --volume-driver
# It will then pip to install the plugin to run with the certs and set up
# startup scripts according to the platform

import sys
import os

# Usage: plugin.py cluster.yml
from utils import Configurator

# a dict that holds the default values for each of the env vars
# that can be overriden
settings_defaults = {
    # allow env override for where to download the experimental
    # docker binary from
    'DOCKER_BINARY_URL': 'https://get.docker.com/builds/Linux/x86_64/docker-latest',
    # perhaps the name of the docker service running on the host is
    # different to 'docker' for example - the clusterhq-flocker-node package
    # installed 'docker.io' depending on OS this translates to
    # start/systemctl calls to this service name
    'DOCKER_SERVICE_NAME': 'docker.io',
    # what repo does the flocker plugin live in
    'PLUGIN_REPO': 'https://github.com/clusterhq/flocker-docker-plugin',
    # what branch to use for the flocker plugin
    'PLUGIN_BRANCH': 'master',
    # skip downloading the docker binary
    # for scenarios where vm images have been pre-baked
    'SKIP_DOCKER_BINARY': '',
    # skip installing the flocker plugin
    'SKIP_INSTALL_PLUGIN': ''
}

# dict that holds our actual env vars once the overrides have been applied
settings = {}

# loop over each of the default vars and check to see if we have been
# given an override in the environment
for field in settings_defaults:
    value = os.environ.get(field)
    if value is None:
        value = settings_defaults[field]
    settings[field] = value

def main():
    c = Configurator(configFile=sys.argv[1])
    control_ip = c.config["control_node"]

    # download and replace the docker binary on each of the nodes
    for node in c.config["agent_nodes"]:

        # don't download a new docker for reasons only the user knows
        if settings["SKIP_DOCKER_BINARY"]:
            break

        public_ip = node["public"]
        print "Replacing docker binary on %s" % (public_ip,)

        # stop the docker service
        print "Stopping the docker service on %s" % (public_ip,)

        if c.config["os"] == "ubuntu":
            c.runSSHRaw(public_ip, "stop %s || true"
                % (settings['DOCKER_SERVICE_NAME'],))
        elif c.config["os"] == "centos":
            c.runSSHRaw(public_ip, "systemctl stop %s.service || true"
                % (settings['DOCKER_SERVICE_NAME'],))
        elif c.config["os"] == "coreos":
            c.runSSHRaw(public_ip, "systemctl stop docker.service || true")

        # download the latest docker binary
        if c.config["os"] == "coreos":
            print "Downloading the latest docker binary on %s - %s" \
                % (public_ip, settings['DOCKER_BINARY_URL'],)
            c.runSSHRaw(public_ip, "mkdir -p /root/bin")
            c.runSSHRaw(public_ip, "wget -O /root/bin/docker %s"
                % (settings['DOCKER_BINARY_URL'],))
            c.runSSHRaw(public_ip, "chmod +x /root/bin/docker")
            c.runSSHRaw(public_ip,
                    "cp /usr/lib/coreos/dockerd /root/bin/dockerd")
            c.runSSHRaw(public_ip,
                    "cp /usr/lib/systemd/system/docker.service /etc/systemd/system/")
            c.runSSHRaw(public_ip,
                    "sed -i s@/usr/lib/coreos@/root/bin@g /etc/systemd/system/docker.service")
            c.runSSHRaw(public_ip,
                    "sed -i 's@exec docker@exec /root/bin/docker@g' /root/bin/dockerd")
        else:
            print "Downloading the latest docker binary on %s - %s" \
                % (public_ip, settings['DOCKER_BINARY_URL'],)
            c.runSSHRaw(public_ip, "wget -O /usr/bin/docker %s"
                % (settings['DOCKER_BINARY_URL'],))

        if c.config["os"] == "ubuntu":
            # newer versions of docker insist on AUFS on ubuntu, probably for good reason.
            c.runSSHRaw(public_ip, "DEBIAN_FRONTEND=noninteractive "
                "'apt-get install -y linux-image-extra-$(uname -r)'")

        # start the docker service
        print "Starting the docker service on %s" % (public_ip,)
        if c.config["os"] == "ubuntu":
            c.runSSHRaw(public_ip, "start %s"
                % (settings['DOCKER_SERVICE_NAME'],))
        elif c.config["os"] == "centos":
            c.runSSHRaw(public_ip, "systemctl start %s.service"
              % (settings['DOCKER_SERVICE_NAME'],))
        elif c.config["os"] == "coreos":
            c.runSSHRaw(public_ip, "systemctl start docker.service")

    print "Generating plugin certs"
    # generate and upload plugin.crt and plugin.key for each node
    for node in c.config["agent_nodes"]:
        public_ip = node["public"]
        # use the node IP to name the local files
        # so they do not overwrite each other
        c.run("flocker-ca create-api-certificate %s-plugin" % (public_ip,))
        print "Generated plugin certs for", public_ip
        # upload the .crt and .key
        for ext in ("crt", "key"):
            c.scp("%s-plugin.%s" % (public_ip, ext,),
                public_ip, "/etc/flocker/plugin.%s" % (ext,))
        print "Uploaded plugin certs for", public_ip

    print "Installing flocker plugin"
    # loop each agent and get the plugin installed/running
    # clone the plugin and configure an upstart/systemd unit for it to run
    for node in c.config["agent_nodes"]:
        public_ip = node["public"]
        private_ip = node["private"]
        
        # the full api path to the control service
        controlservice = 'https://%s:4523/v1' % (control_ip,)

        # perhaps the user has pre-compiled images with the plugin
        # downloaded and installed
        if not settings["SKIP_INSTALL_PLUGIN"]:

            pip_install = False
            if c.config["os"] == "ubuntu":
                print c.runSSHRaw(public_ip, 
                    "apt-get install -y "
                    "python-pip python-dev build-essential "
                    "libssl-dev libffi-dev")
                pip_install = True
            elif c.config["os"] == "centos":
                print c.runSSHRaw(public_ip, 
                    "yum install -y "
                    "python-pip python-devel "
                    "gcc libffi-devel python-devel openssl-devel")
                pip_install = True

            if pip_install:
                # pip install the plugin
                print c.runSSHRaw(public_ip, "pip install git+%s@%s"
                    % (settings['PLUGIN_REPO'], settings['PLUGIN_BRANCH'],))
        else:
            print "Skipping installing plugin: %r" % (settings["SKIP_INSTALL_PLUGIN"],)

        # ensure that the /run/docker/plugins
        # folder exists
        print "Creating the /run/docker/plugins folder"
        c.runSSHRaw(public_ip, "mkdir -p /run/docker/plugins")
        # configure an upstart job that runs the bash script

        if c.config["os"] == "ubuntu":

            print "Writing flocker-docker-plugin upstart job to %s" % (public_ip,)
            c.runSSH(public_ip, """cat <<EOF > /etc/init/flocker-docker-plugin.conf
# flocker-plugin - flocker-docker-plugin job file

description "Flocker Plugin service"
author "ClusterHQ <support@clusterhq.com>"

respawn
env FLOCKER_CONTROL_SERVICE_BASE_URL=%s
env MY_NETWORK_IDENTITY=%s
exec /usr/local/bin/flocker-docker-plugin
EOF
service flocker-docker-plugin restart
""" % (controlservice, private_ip,))
        # configure a systemd job that runs the bash script
        elif c.config["os"] == "centos":
            print "Writing flocker-docker-plugin systemd job to %s" % (public_ip,)
            c.runSSH(public_ip, """# writing flocker-docker-plugin systemd
cat <<EOF > /etc/systemd/system/flocker-docker-plugin.service
[Unit]
Description=flocker-plugin - flocker-docker-plugin job file

[Service]
Environment=FLOCKER_CONTROL_SERVICE_BASE_URL=%s
Environment=MY_NETWORK_IDENTITY=%s
ExecStart=/usr/local/bin/flocker-docker-plugin

[Install]
WantedBy=multi-user.target
EOF
systemctl enable flocker-docker-plugin.service
systemctl start flocker-docker-plugin.service
""" % (controlservice, private_ip,))
        # DOCKER DOCKER DOCKER DOCKER
        elif c.config["os"] == "coreos":
            print "Starting flocker-docker-plugin as docker container on CoreOS on %s" % (public_ip,)
            c.runSSH(node, """echo
docker run --restart=always -d --net=host --privileged \\
-e FLOCKER_CONTROL_SERVICE_BASE_URL=%s \\
-e MY_NETWORK_IDENTITY=%s \\
-v /etc/flocker:/etc/flocker \\
-v /var/run/docker.sock:/var/run/docker.sock \\
--name=flocker-docker-plugin \\
clusterhq/flocker-docker-plugin""" % (controlservice, private_ip,))

if __name__ == "__main__":
    main()
