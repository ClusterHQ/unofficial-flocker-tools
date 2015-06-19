#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This script will generate a user certificate using flocker-ca and upload it
# ready for the plugin to consume
# It will then upload an experimental build of docker
# (i.e. one that supports --volume-drvier)
# It will then git clone this repo and configure the plugin to run
# with the certs

import sys
import os

# Usage: plugin.py cluster.yml
from utils import Configurator

# a dict that holds the default values for each of the env vars
# that can be overriden
settings_defaults = {
    # allow env override for where to download the experimental
    # docker binary from
    # the docker-volumes binary is a buid from latest docker/master:
    # 4caa9392f8aa4e57bfe43880b5f67d15b00ed8a7
    'DOCKER_BINARY_URL': 'http://storage.googleapis.com/experiments-clusterhq/docker-binaries/docker-volumes', # noqa
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
        print "Stopping the docker service on %s - %s" \
            % (public_ip, settings['DOCKER_SERVICE_NAME'],)

        if c.config["os"] == "ubuntu":
            c.runSSHRaw(public_ip, "stop %s || true"
                % (settings['DOCKER_SERVICE_NAME'],))
        elif c.config["os"] == "centos":
            c.runSSHRaw(public_ip, "systemctl stop %s.service || true"
                % (settings['DOCKER_SERVICE_NAME'],))

        # download the latest docker binary\
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

            if c.config["os"] == "ubuntu":
                print c.runSSHRaw(public_ip, 
                    "apt-get install -y "
                    "python-pip python-dev build-essential "
                    "libssl-dev libffi-dev")
            elif c.config["os"] == "centos":
                print c.runSSHRaw(public_ip, 
                    "yum install -y "
                    "python-pip python-devel "
                    "gcc libffi-devel python-devel openssl-devel")

            # pip install the plugin
            print c.runSSHRaw(public_ip, "pip install git+%s@%s"
                % (settings['PLUGIN_REPO'], settings['PLUGIN_BRANCH'],))
        else:
            print "Skipping installing plugin: %r" % (settings["SKIP_INSTALL_PLUGIN"],)

        # ensure that the /usr/share/docker/plugins
        # folder exists
        print "Creating the /usr/share/docker/plugins folder"
        c.runSSHRaw(public_ip, "mkdir -p /usr/share/docker/plugins")
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

if __name__ == "__main__":
    main()
