from twisted.python.filepath import FilePath
from txflocker.client import get_client as txflocker_get_client
import yaml
from twisted.python.usage import Options, UsageError

class FlockerCommands(Options):
    optParameters = [
        ("cluster-yml", None, "./cluster.yml",
            "Location of cluster.yml file "
            "(makes other options unnecessary)"),
        ("certs-path", None, ".",
            "Path to certificates folder"),
        ("user", None, "user",
            "Name of user for which .key and .crt files exist"),
        ("cluster-crt", None, "cluster.crt",
            "Name of cluster cert file"),
        ("control-service", None, None,
            "Hostname or IP of control service"),
        ("control-port", None, 4523,
            "Port for control service REST API"),
    ]
    def __init__(self, commands, *args, **kw):
        self.commands = commands
        self.subCommands = [
            (cmd, None, cls, cls.__doc__)
            for cmd, cls
            in sorted(self.commands.iteritems())]
        return Options.__init__(self, *args, **kw)


def get_client(options):
    cluster = FilePath(options["cluster-yml"])
    if cluster.exists():
        config = yaml.load(cluster.open())
        certificates_path = cluster.parent()
        user = config["users"][0]
        control_service = None # figure it out based on cluster.yml
    else:
        certificates_path = FilePath(options["certs-path"])
        if options["user"] is None:
            raise UsageError("must specify --user")
        user = options["user"]
        if options["control-service"] is None:
            raise UsageError("must specify --control-service")
        control_service = options["control-service"]

    user_certificate_filename = "%s.crt" % (user,)
    user_key_filename = "%s.key" % (user,)

    return txflocker_get_client(
        certificates_path=certificates_path,
        user_certificate_filename=user_certificate_filename,
        user_key_filename=user_key_filename,
        target_hostname=control_service,
    )


def get_base_url(options):
    pwd = FilePath(options["certs-path"])
    if options["control-service"] is not None:
        control_config = {"hostname": options["control-service"]}
    else:
        control_config = yaml.load(
                pwd.child("agent.yml").open())["control-service"]
    control_config["port"] = options["control-port"]
    return "https://%(hostname)s:%(port)s/v1" % control_config


