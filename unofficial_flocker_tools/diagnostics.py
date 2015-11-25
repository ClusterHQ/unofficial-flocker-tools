import sys
import time
from twisted.internet.task import react
from twisted.internet.defer import inlineCallbacks, gatherResults

# Usage: diagnostics.py cluster.yml
from utils import Configurator, log

def report_completion(result, public_ip, message=""):
    log(message, public_ip)
    return result

@inlineCallbacks
def main(reactor, *args):
    c = Configurator(configFile=sys.argv[1])

    # Run flocker-diagnostics 
    deferreds = []
    log("Running Flocker-diagnostics on agent nodes.")
    for node in c.config["agent_nodes"]:
        d = c.runSSHAsync(node["public"], "rm -rf /tmp/diagnostics; mkdir /tmp/diagnostics; cd /tmp/diagnostics; flocker-diagnostics")
        d.addCallback(report_completion, public_ip=node["public"], message=" * Ran diagnostics on agent node.")
        deferreds.append(d)
    d = c.runSSHAsync(c.config["control_node"], "rm -rf /tmp/diagnostics; mkdir /tmp/diagnostics; cd /tmp/diagnostics; flocker-diagnostics")
    d.addCallback(report_completion, public_ip=c.config["control_node"], message=" * Ran diagnostics on control node.")
    deferreds.append(d)
    yield gatherResults(deferreds)

    # Let flocker diagnostics run
    time.sleep(5)

    # Gather flocker-diagnostics 
    deferreds = []
    log("Gathering Flocker-diagnostics on agent nodes.")
    for node in c.config["agent_nodes"]:
        d = c.scp("./", node["public"], "/tmp/diagnostics/clusterhq_flocker_logs_*.tar", async=True, reverse=True)
        d.addCallback(report_completion, public_ip=node["public"], message=" * Gathering diagnostics on agent node.")
        deferreds.append(d)
    d =  c.scp("./", c.config["control_node"], "/tmp/diagnostics/clusterhq_flocker_logs_*.tar", async=True, reverse=True)
    d.addCallback(report_completion, public_ip=c.config["control_node"], message=" * Gathering diagnostics on control node.")
    deferreds.append(d)
    yield gatherResults(deferreds)

def _main():
    react(main, sys.argv[1:])

if __name__ == "__main__":
    _main()
