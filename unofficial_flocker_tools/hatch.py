from twisted.internet import defer
from twisted.internet.task import react
from twisted.python import log
from twisted.python.usage import Options, UsageError
import sys

class Init(Options):
    """
    Deploy a one-off Swarm, Mesos or Kubernetes cluster, optionally with
    Flocker, on local VMs, cloud or managed infrastructure.

    1. First, run `hatch init` with some arguments to create a hatch.yml file.
    2. Optionally edit the file to tweak the settings.
    3. Then run `hatch deploy` to create the infrastructure and install the
       desired software.

    Examples:

    hatch init kubernetes --volmgr=flocker --os=coreos --infra=aws
    hatch init swarm --volmgr=flocker --os=ubuntu --infra=gce
    hatch init mesos-marathon --volmgr=flocker --os=centos --infra=vagrant

    Creates hatch.yml file, prompting for required information (e.g. AWS keys).

    hatch deploy
    """
    optParameters = [
        ("orch", None, "Orchestration framework (kubernetes, swarm, mesos-marathon)"),
        ("volmgr", None, "Volume manager (optional: flocker)"),
        ("infra", None, "Infrastructure (aws, gce, openstack, vsphere, vagrant, managed)"),
        ("os", None, "Operating system (ubuntu, centos, coreos) (default: ubuntu)"),
    ]


class Version(Options):
    """
    show version information
    """
    def run(self):
        print "hatch version 0.6" # TODO get this outta setup.py
        print "see https://docs.clusterhq.com/en/latest/labs/hatch/"
        print


commands = {
    "version": Version,
    "move": Init,
}


class HatchCommands(Options):
    subCommands = [
        (cmd, None, cls, cls.__doc__)
        for cmd, cls
        in sorted(commands.iteritems())]


def main(reactor, *argv):
    try:
        base = HatchCommands()
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
