from utils import Configurator, log
from twisted.internet.defer import gatherResults

def install_kubernetes(reactor, configFile):
    c = Configurator(configFile)
    if c.config["os"] == "ubuntu":
        # Install kubernetes
        deferreds = []

        log("Installing Kubernetes master...")
        d = c.runSSHAsync(
                c.config["control_node"],
                # Install kubernetes
                ("K8S_VERSION=1.1.2 MASTER_IP=%(master_ip)s sh -c '"
                     "curl -sSL https://raw.githubusercontent.com/kubernetes/kubernetes"
                     "/v1.1.2/docs/getting-started-guides/docker-multinode/master.sh |bash"
                 "' "
                 # Install kubectl on the master for convenience for user
                 "&& curl -sSL https://storage.googleapis.com/kubernetes-release/"
                 "release/v1.1.2/bin/linux/amd64/kubectl -o /usr/local/bin/kubectl && "
                 "chmod +x /usr/local/bin/kubectl") % dict(master_ip=c.config["control_node"],)
        )
        d.addCallback(lambda ignored: log("Installed master."))
        deferreds.append(d)

        for node in c.config["agent_nodes"]:
            log("Installing Kubernetes worker on %s..." % (node['public'],))
            d = c.runSSHAsync(
                    node['public'],
                    ("K8S_VERSION=1.1.2 MASTER_IP=%(master_ip)s sh -c '"
                         "curl -sSL https://raw.githubusercontent.com/kubernetes/kubernetes"
                         "/v1.1.2/docs/getting-started-guides/docker-multinode/worker.sh |bash"
                     "' ") % dict(master_ip=c.config["control_node"],)
            )
            d.addCallback(lambda ignored: log("Installed worker on %s." % (node['public'],)))
            deferreds.append(d)

        return gatherResults(deferreds)
