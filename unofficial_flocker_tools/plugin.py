#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This script will generate a user certificate using flocker-ca and upload it
# ready for the plugin to consume
# It will then install a build of docker that supports --volume-driver
# It will then pip to install the plugin to run with the certs and set up
# startup scripts according to the platform

import sys
import os
from twisted.internet.task import react
from twisted.internet.defer import gatherResults, inlineCallbacks

# Usage: plugin.py cluster.yml
from utils import Configurator, log

# a dict that holds the default values for each of the env vars
# that can be overriden
settings_defaults = {
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

@inlineCallbacks
def main(reactor, configFile):
    c = Configurator(configFile=configFile)
    control_ip = c.config["control_node"]

    log("Generating plugin certs")
    # generate and upload plugin.crt and plugin.key for each node
    for node in c.config["agent_nodes"]:
        public_ip = node["public"]
        # use the node IP to name the local files
        # so they do not overwrite each other
        c.run("flocker-ca create-api-certificate %s-plugin" % (public_ip,))
        log("Generated plugin certs for", public_ip)

    def report_completion(result, public_ip, message="Completed plugin install for"):
        log(message, public_ip)
        return result

    deferreds = []
    log("Uploading plugin certs...")
    for node in c.config["agent_nodes"]:
        public_ip = node["public"]
        # upload the .crt and .key
        for ext in ("crt", "key"):
            d = c.scp("%s-plugin.%s" % (public_ip, ext,),
                public_ip, "/etc/flocker/plugin.%s" % (ext,), async=True)
            d.addCallback(report_completion, public_ip=public_ip, message=" * Uploaded plugin cert for")
            deferreds.append(d)
    yield gatherResults(deferreds)
    log("Uploaded plugin certs")

    log("Installing flocker plugin")
    # loop each agent and get the plugin installed/running
    # clone the plugin and configure an upstart/systemd unit for it to run

    deferreds = []
    for node in c.config["agent_nodes"]:
        public_ip = node["public"]
        private_ip = node["private"]
        log("Using %s => %s" % (public_ip, private_ip))

        # the full api path to the control service
        controlservice = 'https://%s:4523/v1' % (control_ip,)

        # perhaps the user has pre-compiled images with the plugin
        # downloaded and installed
        if not settings["SKIP_INSTALL_PLUGIN"]:
            if c.config["os"] == "ubuntu":
                log("Installing plugin for", public_ip, "...")
                d = c.runSSHAsync(public_ip,
                        "apt-get install -y --force-yes clusterhq-flocker-docker-plugin && "
                        "service flocker-docker-plugin restart")
                d.addCallback(report_completion, public_ip=public_ip)
                deferreds.append(d)
            elif c.config["os"] == "centos":
                log("Installing plugin for", public_ip, "...")
                d = c.runSSHAsync(public_ip,
                        "yum install -y clusterhq-flocker-docker-plugin && "
                        "systemctl enable flocker-docker-plugin && "
                        "systemctl start flocker-docker-plugin")
                d.addCallback(report_completion, public_ip=public_ip)
                deferreds.append(d)
        else:
            log("Skipping installing plugin: %r" % (settings["SKIP_INSTALL_PLUGIN"],))
    yield gatherResults(deferreds)

    for node in c.config["agent_nodes"]:
        public_ip = node["public"]
        private_ip = node["private"]
        # ensure that the /run/docker/plugins
        # folder exists
        log("Creating the /run/docker/plugins folder")
        c.runSSHRaw(public_ip, "mkdir -p /run/docker/plugins")
        if c.config["os"] == "coreos":
            log("Starting flocker-docker-plugin as docker container on CoreOS on %s" % (public_ip,))
            c.runSSH(public_ip, """echo
docker run --restart=always -d --net=host --privileged \\
-e FLOCKER_CONTROL_SERVICE_BASE_URL=%s \\
-e MY_NETWORK_IDENTITY=%s \\
-v /etc/flocker:/etc/flocker \\
-v /run/docker:/run/docker \\
--name=flocker-docker-plugin \\
clusterhq/flocker-docker-plugin""" % (controlservice, private_ip,))

    log("Done!")

def _main():
    react(main, sys.argv[1:])

if __name__ == "__main__":
    _main()
