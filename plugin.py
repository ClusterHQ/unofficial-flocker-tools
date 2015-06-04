#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This script will generate a user certificate using flocker-ca and upload it
# ready for the plugin to consume
# It will then upload an experimental build of docker
# (i.e. one that supports --volume-drvier)
# It will then git clone this repo and configure the plugin to run 
# with the certs

import sys
import yaml
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
    'DOCKER_SERVICE_NAME': 'docker',
    # what repo does the flocker plugin live in
    'PLUGIN_REPO': 'https://github.com/clusterhq/flocker-docker-plugin',
    # what branch to use for the flocker plugin
    'PLUGIN_BRANCH': 'txflocker-env-vars'
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

if __name__ == "__main__":
    c = Configurator(configFile=sys.argv[1])
    control_ip = c.config["control_node"]

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
        # we need this so we know what folder to cd into
        plugin_repo_folder = settings['PLUGIN_REPO'].split('/').pop()

        # the full api path to the control service
        controlservice = 'https://%s:4523/v1' % (control_ip,)
        c.runSSHRaw(public_ip, "rm -rf %s" % (plugin_repo_folder,))
        # clone the right repo and checkout the branch
        print "Cloning the plugin repo on %s - %s" \
            %(public_ip, settings['PLUGIN_REPO'],)
        c.runSSHRaw(public_ip, "git clone -b %s %s || true" 
            % (settings['PLUGIN_BRANCH'], settings['PLUGIN_REPO'],))

        # install pip and python-dev
        if c.config["os"] == "ubuntu":
            c.runSSHRaw(public_ip, "apt-get install -y python-dev python-pip")
        # configure a systemd job that runs the bash script
        elif c.config["os"] == "centos":
            c.runSSHRaw(public_ip, "yum install -y python-devel python-pip")

        # pip install the plugin
        c.runSSHRaw(public_ip, "pip install -r /root/%s/requirements.txt" 
            % (plugin_repo_folder,))

        # configure an upstart job that runs the bash script
        if c.config["os"] == "ubuntu":

            # ensure that the /usr/share/${DOCKER_SERVICE_NAME}/plugins
            # folder exists
            print "Creating the /usr/share/%s/plugins folder" \
                % (settings['DOCKER_SERVICE_NAME'],)
            c.runSSHRaw(public_ip, "mkdir -p /usr/share/%s/plugins" \
                % (settings['DOCKER_SERVICE_NAME'],))

            print "Writing flocker-plugin upstart job to %s" % (public_ip,)
            c.runSSH(public_ip, """cat <<EOF > /etc/init/flocker-plugin.conf
# flocker-plugin - flocker-plugin job file

description "Flocker Plugin service"
author "ClusterHQ <support@clusterhq.com>"

respawn
env FLOCKER_CONTROL_SERVICE_BASE_URL=%s
env MY_NETWORK_IDENTITY=%s
chdir /root/%s
exec /usr/bin/twistd -noy powerstripflocker.tac
EOF
service flocker-plugin restart
""" % (controlservice, private_ip, plugin_repo_folder,))
        # configure a systemd job that runs the bash script
        elif c.config["os"] == "centos":
            print "Writing flocker-plugin systemd job to %s" % (public_ip,)
            c.runSSH(public_ip, """# writing flocker-plugin systemd
cat <<EOF > /etc/systemd/system/flocker-plugin.service
[Unit]
Description=flocker-plugin - flocker-plugin job file

[Service]
Environment=FLOCKER_CONTROL_SERVICE_BASE_URL=%s
Environment=MY_NETWORK_IDENTITY=%s
ExecStart=/usr/bin/twistd -noy powerstripflocker.tac
WorkingDirectory=/root/%s

[Install]
WantedBy=multi-user.target
EOF
systemctl enable flocker-plugin.service
systemctl start flocker-plugin.service
""" % (controlservice, private_ip, plugin_repo_folder,))

    print "Replacing docker binary"
    # download and replace the docker binary on each of the nodes
    for node in c.config["agent_nodes"]:
        public_ip = node["public"]
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

        # stop the docker service
        print "Starting the docker service on %s" % (public_ip,)
        if c.config["os"] == "ubuntu":
            c.runSSHRaw(public_ip, "start %s" 
                % (settings['DOCKER_SERVICE_NAME'],))
        elif c.config["os"] == "centos":
            c.runSSHRaw(public_ip, "systemctl start %s.service" 
              % (settings['DOCKER_SERVICE_NAME'],))