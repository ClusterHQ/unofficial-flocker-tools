#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Install catalog agents.

import sys
from twisted.internet.task import react
from twisted.internet.defer import gatherResults, inlineCallbacks
from os import environ

# Usage: plugin.py cluster.yml
from utils import Configurator, log

def report_completion(result, public_ip,
        message="Completed volume hub catalog agents install for"):
    log(message, public_ip)
    return result

@inlineCallbacks
def main(reactor, configFile):
    c = Configurator(configFile=configFile)
    control_ip = c.config["control_node"]

    install_command = ('TOKEN="%s" '
            """sh -c 'curl -H "cache-control: max-age=0" -ssL https://get-volumehub.clusterhq.com/ |sh'""" %
            (environ["TOKEN"],))

    deferreds = [c.runSSHAsync(control_ip,
        "TARGET=control-service " + install_command)]

    first = True
    for node in c.config["agent_nodes"]:
        if first:
            run_flocker_agent_here = "RUN_FLOCKER_AGENT_HERE=1 "
        else:
            run_flocker_agent_here = ""
        deferreds.append(c.runSSHAsync(node["public"],
            run_flocker_agent_here + "TARGET=agent-node " + install_command))
        first = False

    log("Installing volume hub catalog agents...")
    yield gatherResults(deferreds)
    log("Done!")

def _main():
    react(main, sys.argv[1:])

if __name__ == "__main__":
    _main()
