from twisted.internet import defer
from twisted.internet.task import react
from twisted.python import log
from twisted.python.usage import Options, UsageError
import sys

class HatchOptions(Options):
    """
    Deploy a one-off Swarm, Mesos or Kubernetes cluster, optionally with
    Flocker, on local VMs, cloud or managed infrastructure.

    1. First, run `hatch init` with some arguments to create a hatch.yml file.
    2. Optionally edit the file to tweak the settings.
    3. Then run `hatch deploy` to create the infrastructure and install the
       desired software.

    Examples:

    hatch init --kubernetes --flocker --coreos --aws
    hatch init --swarm --flocker --ubuntu --gce
    hatch init --mesos --flocker --centos --vagrant

    Creates hatch.yml file, prompting for required information (e.g. AWS keys).

    hatch deploy
    """
    optFlags = [
        # Orchestration
        ("swarm", None, "Orchestration: Docker Swarm"),
        ("mesos-marathon", None, "Orchestration: Mesos with Marathon"),
        ("kubernetes", None, "Orchestration: Kubernetes"),

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
        
        """
        """
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
