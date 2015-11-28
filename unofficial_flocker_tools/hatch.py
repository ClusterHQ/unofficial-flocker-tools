from twisted.internet import defer
from twisted.internet.task import react
from twisted.python import log
from twisted.python.usage import Options, UsageError
import sys

class HatchOptions(Options):
    """
    Deploy a one-off Swarm, Mesos or Kubernetes cluster, optionally with
    Flocker, on local VMs, cloud or managed infrastructure.

    Examples:

    hatch --kubernetes --flocker --coreos --aws
    hatch --swarm --flocker --ubuntu --gce
    hatch --mesos --flocker --centos --vagrant
    """
    optFlags = [
        # Orchestration
        ("kubernetes", None, "Orchestration: Kubernetes"),
        ("swarm", None, "Orchestration: Docker Swarm"),
        ("mesos", None, "Orchestration: Mesos"),

        # Volume Management
        ("flocker", None, "Volume Management: Flocker"),

        # Operating System
        ("coreos", None, "Operating System: CoreOS"),
        ("ubuntu", None, "Operating System: Ubuntu"),
        ("centos", None, "Operating System: CentOS"),

        # Infrastructure provider
        ("aws", None, "Infrastructure Provider: Amazon Web Services"),
        ("gce", None, "Infrastructure Provider: Google Compute Engine"),
        ("openstack", None, "Infrastructure Provider: OpenStack"),
        ("vsphere", None, "Infrastructure Provider: VMware vSphere"),
        
        ("vagrant", None, "Infrastructure Provider: Local Vagrant"),
        ("managed", None, "Infrastructure Provider: Specify own IPs"),
        
        # Flocker storage drivers
        ("ebs", None, "Flocker Storage Driver: Amazon EBS"),
        ("openstack", None, "Flocker Storage Driver: OpenStack Cinder"),
        ("gce-pd", None, "Flocker Storage Driver: GCE PD"),
        ("ceph", None, "Flocker Storage Driver: Ceph"),
        ("zfs", None, "Flocker Storage Driver: ZFS (Alpha)"),

        # 3rd party storage drivers
        ("emc-scaleio", None, "Flocker Storage Driver: EMC ScaleIO"),
        ("emc-xtremio", None, "Flocker Storage Driver: EMC XtremIO"),
        ("vsphere", None, "Flocker Storage Driver: VMware vSphere"),
        ("netapp-ontap", None, "Flocker Storage Driver: NetApp OnTap"),
        ("dell-sc", None, "Flocker Storage Driver: Dell Storage SC Series"),
        ("huawei-oceanstor", None, "Flocker Storage Driver: Huawei OceanStor"),
        ("hedvig", None, "Flocker Storage Driver: Hedvig"),
        ("convergeio", None, "Flocker Storage Driver: ConvergeIO"),
        ("nexentaedge", None, "Flocker Storage Driver: NexentaEdge"),
        ("saratoga", None, "Flocker Storage Driver: Saratoga Speed"),
    ]


def main(reactor, *argv):
    try:
        base = HatchOptions()
        base.parseOptions(argv)
        if base.subCommand is not None:
            d = defer.maybeDeferred(base.subOptions.run)
        else:
            raise UsageError("Please specify a command.")
        def usageError(failure):
            failure.trap(UsageError)
            print str(failure.value)
            return # skips verbose exception printing
        d.addErrback(usageError)
        def err(failure):
            log.err(failure)
            reactor.stop()
        d.addErrback(err)
        return d
    except UsageError, errortext:
        print errortext
        print 'Try --help for usage details.'
        sys.exit(1)


def _main():
    react(main, sys.argv[1:])

if __name__ == "__main__":
    _main()
