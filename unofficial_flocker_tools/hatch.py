from twisted.internet import defer
from twisted.internet import reactor
from twisted.internet.defer import succeed
from twisted.internet.task import react
from twisted.python import log
from twisted.python.usage import Options, UsageError
from twisted.python.filepath import FilePath
import sys
import yaml
import json

from utils import container_facing_key_path

from sample_files import main as sample_files
from get_nodes import main as get_nodes
from destroy_nodes import main as destroy_nodes
from install import main as install_flocker
from config import main as configure_flocker
from plugin import main as install_flongle
from hub_agents import main as install_hub_agents
from swarm import install_swarm
from kubernetes import install_kubernetes

class Flocker(object):
    name = "flocker"
    config_vars = [
        ("volume_hub_token", (
            "Volume hub token for displaying Flocker cluster metadata and logs "
            "in our hosted volume hub service.\nGet one from https://volumehub.clusterhq.com/",
            None,
            str,
            True,
        )),
    ]
    config_key = "flocker_options"
    checks = []

class Kubernetes(object):
    name = "kubernetes"
    config_vars = []
    config_key = "kubernetes_options"
    checks = []

class Swarm(object):
    name = "swarm"
    config_vars = []
    config_key = "swarm_options"
    checks = []

DEPLOYABLE_THINGS = [
    Flocker,
    Kubernetes,
    Swarm,
#    Mesos,
#    Marathon,
]

MUTUALLY_EXCLUSIVE = [
    # Everything except Flocker, basically
    Kubernetes,
    Swarm,
]

def _deployables_list():
    return ", ".join(d.name for d in DEPLOYABLE_THINGS)

# TODO IGatherable
class AWSInfrastructure(object):
    name = "aws"
    config_key = "aws_options"
    config_vars = [
        ("access_key", ("Your AWS access key", None, str, False)),
        ("secret_key", ("Your AWS secret key", None, str, False)),

        ("region", ("Region you want nodes deployed", "us-east-1", str, False)),
        ("availability_zone", ("Zone you want nodes deployed", "us-east-1a", str, False)),

        ("key_name", (
            "Name of EC2 keypair in this region; create one at https://aws.amazon.com/",
            None,
            str,
            False,
        )),
        ("private_key_path", (
            "Absolute path to .pem key on your local machine",
            None,
            str,
            False,
        )),

        ("instance_type", ("Instance type" ,"m3.large", str, False)),

        ("agent_nodes", (
            "Number of agent nodes; will launch this + 1 for master node",
            2,
            int,
            False,
        )),
    ]
    def _check_private_key_path(private_key_path):
        if not FilePath(container_facing_key_path(private_key_path)).exists():
            raise UsageError(
                "Private key specified does not exist at: %s" %
                    (private_key_path,))
    checks = {
        "private_key_path": _check_private_key_path,
    }


INFRASTRUCTURY_THINGS = [
    AWSInfrastructure,
]

def _infrastructure_list():
    return ", ".join(i.name for i in INFRASTRUCTURY_THINGS)


OS_LIST = ["ubuntu", "coreos"]

def _operating_system_list():
    return ", ".join(OS_LIST)

FILENAME = "hatch.yml"

class Init(Options):
    optParameters = [
        # In future, aim to support:
        #("on", None, "Infrastructure: aws, gce, openstack, vsphere, vagrant, managed"),
        #("os", None, "Operating system: ubuntu, centos, coreos (default: ubuntu)"),

        ("on", None, None, "Infrastructure: %s" % (_infrastructure_list(),)),
        ("os", None, None, "Operating system: %s" % (_operating_system_list(),)),
    ]
    def parseArgs(self, *args):
        self._deployables = args

    def run(self):
        example = "hatch init --on aws --os ubuntu flocker swarm"
        if not self.get("on"):
            raise UsageError("must specify --on for infrastructure (one of: %s)\n\n%s" %
                    (_infrastructure_list(), example))
        if not self.get("os"):
            raise UsageError(
                "must specify --os for operating system (one of: %s)\n\n%s" %
                    (_operating_system_list(), example))
        self.infrastructure = self["on"]
        if self.infrastructure not in [
                i.name for i in INFRASTRUCTURY_THINGS]:
            raise UsageError(
                "infrastructure must be one of: %s" %
                (_operating_system_list(),))
        self.operating_system = self["os"]
        if self.operating_system not in OS_LIST:
            raise UsageError(
                "operating system must be one of: %s" %
                (_operating_system_list(),))
        if not self._deployables:
            raise UsageError(
                    "must specify some deployables, one or more of: %s\n\n%s" %
                    (_deployables_list(),))
        configuration = Configuration(
                operating_system=self.operating_system,
                infrastructure=self.infrastructure,
                deployables=self._deployables,
        )
        # Validation
        configuration.check_file_not_exists()
        configuration.check_mutually_exclusive_deployables()
        # Construct configuration, asking user as necessary
        configuration.gather_configuration()
        # Save the file
        configuration.persist_configuration()


class Deploy(Options):
    synopsis = "hatch deploy [hatch.yml]"
    def parseArgs(self, filename=None):
        if filename is None:
            filename = FILENAME
        self.filename = filename

    def run(self):
        # Put terraform files into pwd.
        hatch_config = FilePath(".").child(self.filename)
        if not hatch_config.exists():
            raise UsageError("File %r does not exist. Please run `hatch init` if you "
                             "haven't already, and check you're in the same directory "
                             "you were when you did that.")
        hatch = yaml.load(hatch_config.getContent())
        if hatch["operating_system"] != "ubuntu":
            # TODO support more OSes, in particular CoreOS
            raise UsageError("Don't know how to install on anything but Ubuntu "
                             "(those are all the AMIs I know about)")
        if "flocker" not in hatch["deploy"]:
            # TODO split docker installation out into its own bit ("common
            # installation"?), maybe even make it optional
            raise UsageError("Sorry, at the moment I don't know how to not install Flocker.")
        if hatch["infrastructure"] != "aws":
            # TODO support more than just AWS
            raise UsageError("I don't know how to install on anything but AWS at the moment.")
        if "swarm" in hatch["deploy"] and hatch["operating_system"] != "ubuntu":
            # TODO support Swarm on all platforms
            raise UsageError("Sorry, I can only install Swarm on Ubuntu")
        if "kubernetes" in hatch["deploy"] and hatch["operating_system"] != "ubuntu":
            # TODO support Kubernetes on all platforms
            raise UsageError("Sorry, I can only install Kubernetes on Ubuntu")
        # OK, we're good.
        sample_files()
        terraform_template = FilePath(".").child("terraform").child("terraform.tfvars.json")
        # Write the terraform config; ok to clobber from previous run
        terraform_template.setContent(json.dumps(
            {"aws_access_key": hatch["aws_options"]["access_key"],
             "aws_secret_key": hatch["aws_options"]["secret_key"],
             "aws_region": hatch["aws_options"]["region"],
             "aws_availability_zone": hatch["aws_options"]["availability_zone"],
             "aws_key_name": hatch["aws_options"]["key_name"],
             "private_key_path": hatch["aws_options"]["private_key_path"]}))
        print "======================================"
        print "Running terraform to provision nodes"
        print "======================================"
        get_nodes()
        d = succeed(None)
        if "flocker" in hatch["deploy"]:
            print "========================================================"
            print "Installing and configuring Flocker and the Docker plugin"
            print "========================================================"
            d.addCallback(lambda ignored: install_flocker(reactor, "cluster.yml"))
            d.addCallback(lambda ignored: configure_flocker(reactor, "cluster.yml"))
            d.addCallback(lambda ignored: install_flongle(reactor, "cluster.yml"))
            token = hatch["flocker_options"]["volume_hub_token"]
            if token is not None:
                d.addCallback(lambda ignored: install_hub_agents(reactor, "cluster.yml", token))
        if "swarm" in hatch["deploy"]:
            def print_swarm(passthru):
                print "========================================================"
                print "Installing and configuring Docker Swarm"
                print "========================================================"
                return passthru
            d.addCallback(print_swarm)
            d.addCallback(lambda ignored: install_swarm(reactor, "cluster.yml"))
        if "kubernetes" in hatch["deploy"]:
            def print_kubernetes(passthru):
                print "========================================================"
                print "Installing and configuring Kubernetes"
                print "========================================================"
                return passthru
            d.addCallback(print_kubernetes)
            d.addCallback(lambda ignored: install_kubernetes(reactor, "cluster.yml"))
        return d


class Configuration(object):
    """
    A thing that knows how to persist its configuration and attempt to deploy
    itself.
    """
    FILENAME = "hatch.yml"

    def __init__(self, operating_system, infrastructure, deployables):
        self.deployables = deployables
        self.infrastructure = infrastructure
        self.operating_system = operating_system
        self._configuration = {}

    def check_file_not_exists(self):
        if FilePath(self.FILENAME).exists():
            raise UsageError("File %r already exists. "
                "Edit file directly or delete/move it to start again from scratch."
                % (self.FILENAME,))

    def check_mutually_exclusive_deployables(self):
        count = 0
        exclusive = []
        # Check that there is 0 or 1 from the mutually exclusive list.
        for desired in self.deployables:
            for deployable in MUTUALLY_EXCLUSIVE:
                if deployable.name == desired:
                    count += 1
                    exclusive.append(desired)
        if count > 1:
            raise UsageError("%s are mutually exclusive, please only specify one of them"
                             % (", ".join(exclusive)))

    def _find_infrastructure(self):
        for infra in INFRASTRUCTURY_THINGS:
            if infra.name == self.infrastructure:
                return infra

    def _find_deployables(self):
        deployables = []
        for desired in self.deployables:
            for deployable in DEPLOYABLE_THINGS:
                if deployable.name == desired:
                    deployables.append(deployable)
        return deployables

    def _ask_user(self, gatherable):
        if gatherable.config_vars:
            print "======================================"
            print "Configuration for", gatherable.name
            print "======================================"
        def user_response_acceptable(var, default, type_, optional):
            default_words = ""
            if default is not None:
                default_words = " [default: %r]" % (default,)
            message = "%(description)s (%(variable)s)%(default_words)s\n-> " % dict(
                    description=description, variable=var, default_words=default_words)
            sys.stdout.write(message)
            sys.stdout.flush()
            user_response = raw_input()
            if not user_response:
                if default is None and not optional:
                    print "Please enter something!"
                    return False
                else:
                    return default
            return type_(user_response)
        def get_acceptable_response(var, default, type_, checker, optional):
            while True:
                response = user_response_acceptable(var, default, type_, optional)
                if checker is not None:
                    try:
                        checker(response)
                    except UsageError, errortext:
                        print errortext
                        continue
                return response
        response = {}
        for (var, (description, default, type_, optional)) in gatherable.config_vars:
            if var in gatherable.checks:
                checker = gatherable.checks[var]
            else:
                checker = None
            response[var] = get_acceptable_response(var, default, type_, checker, optional)
        return response

    def gather_configuration(self):
        self._configuration["operating_system"] = self.operating_system
        self._configuration["deploy"] = self.deployables
        self._configuration["infrastructure"] = self.infrastructure

        infra = self._find_infrastructure()
        self._configuration[infra.config_key] = self._ask_user(infra)

        for deployable in self._find_deployables():
            self._configuration[deployable.config_key] = self._ask_user(deployable)

    def persist_configuration(self):
        FilePath(self.FILENAME).setContent(
                yaml.safe_dump(self._configuration, default_flow_style=False))
        print "Saved configuration to %r" % (self.FILENAME,)


class Version(Options):
    def run(self):
        print "hatch version 0.6" # TODO get this outta setup.py
        print "See https://docs.clusterhq.com/en/latest/labs/hatch/"
        print


class Status(Options):
    """
    Parse the cluster.yml and render a nice table showing public and private IP
    addresses of nodes, along with info on how to log into them.
    """
    def run(self):
        1/0


class Destroy(Options):
    optFlags = [('force', 'f', 'Force destruction')]
    def run(self):
        # TODO clean up flocker volumes before destroying the VMs, see kludge
        # in test_integration.py
        destroy_nodes(force=self["force"])


commands = {
    "version": Version,
    "init": Init,
    "deploy": Deploy,
#    "status": Status,
    "destroy": Destroy,
}


"""
Deploy a one-off Swarm, Mesos or Kubernetes cluster, optionally with
Flocker, on local VMs, cloud or managed infrastructure.

    hatch init --os ubuntu --on aws flocker
    hatch init --os ubuntu --on gce swarm flocker
    hatch init --os coreos --on openstack kubernetes flocker
    hatch init --os centos --on vagrant mesos marathon flocker

TODO
    hatch status
        Display a summary of the current cluster, what was deployed on it, how
        to log into the master, and some links to some fun tutorials you can
        try.

"""

class HatchCommands(Options):
    __doc__ = """Usage: hatch command [options]
    Deploy a one-off Swarm or Kubernetes cluster, optionally with Flocker, on cloud
    infrastructure.

    1. First, run `hatch init` with some arguments to create a hatch.yml file
       in the current ("cluster") directory.
    2. Then run `hatch deploy` to create the infrastructure and install the
       desired software.

Subcommands:
    hatch init --os [operating-system] --on [infrastructure] deployable_1 [d_2 ...]
        Creates hatch.yml file, prompting for required information (e.g. AWS keys).

        Supported deployables: %(deployables)s
        Supported operating systems: %(operating_systems)s
        Supported infrastructures: %(infrastructures)s

        Examples:
        hatch init --os ubuntu --on aws flocker
        hatch init --os ubuntu --on aws swarm flocker
        hatch init --os coreos --on aws kubernetes flocker

    hatch deploy
        Provisions nodes, deploys and configure the deployables described in
        hatch.yml on the nodes.

    hatch destroy
        Destroys and cleans up nodes as deployed by a previous run of `hatch
        deploy`.

    hatch version
        Display version information.

Options:
    hatch --help: display this help text
""" % (dict(deployables=_deployables_list(),
          operating_systems=_operating_system_list(),
          infrastructures=_infrastructure_list()))
    subCommands = [
        (cmd, None, cls, cls.__doc__)
        for cmd, cls
        in sorted(commands.iteritems())]

    def opt_help(self):
        raise UsageError(self.__doc__)


def main(reactor, *argv):
    try:
        base = HatchCommands()
        base.parseOptions(argv)
        if base.subCommand is not None:
            d = defer.maybeDeferred(base.subOptions.run)
        else:
            raise UsageError(HatchCommands.__doc__)
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
        sys.exit(1)


def _main():
    react(main, sys.argv[1:])

if __name__ == "__main__":
    _main()
