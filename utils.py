import subprocess
from pipes import quote
import yaml
import os

class Configurator(object):
    def __init__(self, configFile):
        self.config = yaml.load(open(configFile))
        # set some defaults
        self.config["private_key_path"] = self.config.get("private_key_path", "~/.ssh/id_rsa")
        self.config["remote_server_username"] = self.config.get("remote_server_username", "root")

    def runSSH(self, ip, command):
        command = 'ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i %s %s@%s %s' % (self.config["private_key_path"],
                self.config["remote_server_username"],
                ip, " ".join(map(quote, ["sh", "-c", command])))
        return subprocess.check_output(command, shell=True)

    def runSSHRaw(self, ip, command):
        command = 'ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i %s %s@%s %s' % (self.config["private_key_path"],
                self.config["remote_server_username"],
                ip, command)
        return subprocess.check_output(command, shell=True)

    def runSSHPassthru(self, ip, command):
        command = 'ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i %s %s@%s %s' % (self.config["private_key_path"],
                self.config["remote_server_username"],
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
        scp = ("scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i %(private_key_path)s %(local_path)s "
               "%(remote_server_username)s@%(external_ip)s:%(remote_path)s") % dict(
                    private_key_path=self.config["private_key_path"],
                    remote_server_username=self.config["remote_server_username"],
                    external_ip=external_ip, remote_path=remote_path,
                    local_path=local_path)
        return subprocess.check_output(scp, shell=True)
