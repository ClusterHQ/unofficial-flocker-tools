from utils import Configurator, log
from twisted.internet.defer import gatherResults

def install_swarm(reactor, configFile):
    c = Configurator(configFile)
    if c.config["os"] == "ubuntu":
        # Install swarm
        deferreds = []
        clusterid = c.runSSH(c.config["control_node"], "docker run swarm create").strip()
        log("Created Swarm ID")
        for node in c.config["agent_nodes"]:
            # TODO: sed /etc/default/docker, rather than transiently starting a docker daemon
            d = c.runSSHAsync(node['public'], """
service docker stop
docker daemon -H unix:///var/run/docker.sock -H tcp://0.0.0.0:2375 >> /tmp/dockerlogs 2>&1 &
""")
            d.addCallback(lambda ignored: c.runSSHAsync(
                node['public'],
                "docker run -d swarm join --addr=%s:2375 token://%s""" % (
                    node['private'], clusterid)
                )
            )
            d.addCallback(lambda ignored: log("Started Swarm Agent for %s" % node['public']))
            deferreds.append(d)

        d = gatherResults(deferreds)
        def start_master(ignored):
            d = c.runSSHAsync(c.config["control_node"], """
docker run -d -p 2357:2375 swarm manage token://%s
""" % clusterid)
            log("Starting Swarm Master")
            return d
        d.addCallback(start_master)
        def started_master(ignored):
            log("Swarm Master is at tcp://%s:2357" % c.config["control_node"])
        d.addCallback(started_master)
        return d
