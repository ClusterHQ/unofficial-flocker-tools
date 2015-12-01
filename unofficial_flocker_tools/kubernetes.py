from utils import Configurator, log
from twisted.internet.defer import gatherResults

def install_kubernetes(reactor, configFile):
    c = Configurator(configFile)
    if c.config["os"] == "ubuntu":
        # Install kubernetes
        deferreds = []
        log("Starting etcd...")
        c.runSSHRaw(c.config["control_node"],
                "docker run --restart=always --net=host -d "
                "gcr.io/google_containers/etcd:2.0.9 "
                "/usr/local/bin/etcd --addr=127.0.0.1:4001 --bind-addr=0.0.0.0:4001 "
                "--data-dir=/var/etcd/data")
        log("Started etcd.")

        log("Starting k8s master...")
        c.runSSHRaw(c.config["control_node"],
                "docker run --restart=always --net=host -d "
                "-v /var/run/docker.sock:/var/run/docker.sock "
                "gcr.io/google_containers/hyperkube:v1.1.1 /hyperkube kubelet "
                "--api_servers=http://localhost:8080 --v=2 --address=0.0.0.0 "
                "--enable_server --hostname_override=127.0.0.1 "
                "--config=/etc/kubernetes/manifests")
        log("Started k8s master.")

        log("Starting k8s service proxy...")
        c.runSSHRaw(c.config["control_node"],
                "docker run -d --restart=always --net=host --privileged "
                "gcr.io/google_containers/hyperkube:v1.1.1 "
                "/hyperkube proxy --master=http://localhost:8080 --v=2")
        log("Started k8s service proxy")

        for node in c.config["agent_nodes"]:
            d = c.runSSHAsync(
                node['public'],
                "docker -H unix:///var/run/docker-bootstrap.sock run -d "
                "--restart=always --net=host --privileged -v /dev/net:/dev/net "
                " --name=flannel quay.io/coreos/flannel:0.5.0 /opt/bin/flanneld "
                "--etcd-endpoints=http://%(master_address)s:4001" %
                dict(
                    master_address=c.config["control_node"],
                )
            )
            d.addCallback(lambda ignored:
                    log("Started Flannel on %s" % (node['public'],)))

            d.addCallback(lambda ignored:
                    c.runSSHAsync(
                        node['public'],
                        """eval $(docker -H unix:///var/run/docker-bootstrap.sock
                        exec flannel cat /run/flannel/subnet.env) &&
                        sed -i s/XXX/--bip=${FLANNEL_SUBNET} \
                                --mtu=${FLANNEL_MTU}/ /etc/docker/default &&
                        service docker restart
                        /sbin/ifconfig docker0 down &&
                        brctl delbr docker0 &&
                        docker run --volume=/:/rootfs:ro \
                                   --volume=/sys:/sys:ro \
                                   --volume=/dev:/dev \
                                   --volume=/var/lib/docker/:/var/lib/docker:rw \
                                   --volume=/var/lib/kubelet/:/var/lib/kubelet:rw \
                                   --volume=/var/run:/var/run:rw \
                                   --net=host \
                                   --privileged=true \
                                   --pid=host \
                                   --restart=always \
                                   -d \
                                   gcr.io/google_containers/hyperkube:v1.0.1
                                   /hyperkube kubelet
                                       --api-servers=http://${MASTER_IP}:8080 --v=2
                                       --address=0.0.0.0 --enable-server
                                       --hostname-override=$(hostname -i)
                                       --cluster-dns=10.0.0.10
                                       --cluster-domain=cluster.local"""
                    )
            )
            deferreds.append(d)

        return gatherResults(deferreds)
