import subprocess
from pipes import quote
import yaml
import os
from twisted.internet.utils import getProcessOutput

class Configurator(object):
    def __init__(self, configFile):
        self.config = yaml.load(open(configFile))
        # set some defaults
        self.config["private_key_path"] = self.config.get("private_key_path", "~/.ssh/id_rsa")
        if "CONTAINERIZED" in os.environ:
            self.config["private_key_path"] = "/host" + self.config["private_key_path"]
        self.config["remote_server_username"] = self.config.get("remote_server_username", "root")

    def runSSH(self, ip, command, username=None):
        command = 'ssh -o LogLevel=error -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i %s %s@%s %s' % (self.config["private_key_path"],
                username if username is not None else self.config["remote_server_username"],
                ip, " ".join(map(quote, ["sh", "-c", command])))
        return subprocess.check_output(command, shell=True)

    def runSSHAsync(self, ip, command, username=None):
        """
        Use Twisted APIs, assuming a reactor is running, to return a deferred
        which fires with the result.
        """
        executable = "/usr/bin/ssh"
        command = ['-o', 'LogLevel=error', '-o', 'UserKnownHostsFile=/dev/null', '-o',
                   'StrictHostKeyChecking=no', '-i',
                   self.config["private_key_path"], "%s@%s" % (
                       username if username is not None else self.config["remote_server_username"], ip),
                   " ".join(map(quote, ["sh", "-c", command]))]
        return getProcessOutput(executable, command, errortoo=True)

    def runSSHRaw(self, ip, command, username=None):
        command = 'ssh -o LogLevel=error -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i %s %s@%s %s' % (self.config["private_key_path"],
                username if username is not None else self.config["remote_server_username"],
                ip, command)
        return subprocess.check_output(command, shell=True)

    def runSSHPassthru(self, ip, command, username=None):
        command = 'ssh -o LogLevel=error -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i %s %s@%s %s' % (self.config["private_key_path"],
                username if username is not None else self.config["remote_server_username"],
                ip, " ".join(map(quote, command)))
        return os.system(command)

    def run(self, command):
        return subprocess.check_output(command, shell=True)

    def pushConfig(self, text, instances):
        f = open("master_address", "w")
        f.write(text)
        f.close()

        print "Written master address"
        for (externalIP, internalIP) in instances:
            self.runSSH(externalIP, ['sudo', 'mkdir', '-p', '/etc/flocker'])

            f = open("my_address", "w")
            f.write(externalIP)
            f.close()

            # push the list of minions to the master (for later firewalling of control
            # port and minion port) [might as well push list of minions to all
            # nodes at this point...]
            f = open("minions", "w")
            f.write("\n".join([e for (e, i) in instances]))
            f.close()

            for f in ('master_address', 'my_address', 'minions'):
                self.scp(f, externalIP, "/tmp/%s" % (f,))
                self.runSSH(externalIP, ['sudo', 'mv', '/tmp/%s' % (f,), '/etc/flocker/%s' % (f,)])
                print "Pushed", f, "to", externalIP

        print "Finished telling all nodes about the master."

    def scp(self, local_path, external_ip, remote_path,
            private_key_path=None, remote_server_username=None):
        if private_key_path is not None:
            private_key_path = self.config["private_key_path"]
        if remote_server_username is not None:
            remote_server_username = self.config["remote_server_username"]
        scp = ("scp -o LogLevel=error -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i %(private_key_path)s %(local_path)s "
               "%(remote_server_username)s@%(external_ip)s:%(remote_path)s") % dict(
                    private_key_path=self.config["private_key_path"],
                    remote_server_username=self.config["remote_server_username"],
                    external_ip=external_ip, remote_path=remote_path,
                    local_path=local_path)
        return subprocess.check_output(scp, shell=True)
