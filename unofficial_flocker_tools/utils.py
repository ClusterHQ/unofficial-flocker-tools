import subprocess
from pipes import quote
import yaml
import os
import time
from twisted.internet.utils import getProcessOutput
from contextlib import closing
from socket import socket
from twisted.internet import reactor
from twisted.internet.defer import maybeDeferred
from twisted.internet.task import deferLater

def verify_socket(host, port, timeout=60, connect_timeout=5):
    """
    Wait until the destionation can be connected to.

    :param bytes host: Host to connect to.
    :param int port: Port to connect to.

    :return Deferred: Firing when connection is possible.
    """
    def can_connect():
        with closing(socket()) as s:
            s.settimeout(connect_timeout)
            conn = s.connect_ex((host, port))
            return conn == 0

    print "Attempting to connect to %s:%s..." % (host, port)
    dl = loop_until(can_connect, timeout=timeout)
    then = time.time()
    def print_success(result, ip, port):
        print "Connected to %s:%s after %.2f seconds!" % (ip, port, time.time() - then)
    def print_failure(result, ip, port):
        print "Failed to connect to %s:%s after %.2f seconds :(" % (ip, port, time.time() - then)
    dl.addCallback(print_success, ip=host, port=port)
    dl.addErrback(print_failure, ip=host, port=port)
    return dl


class TimeoutError(Exception):
    pass


def loop_until(predicate, timeout=None):
    """Call predicate every 0.1 seconds, until it returns something ``Truthy``.

    :param predicate: Callable returning termination condition.
    :type predicate: 0-argument callable returning a Deferred.

    :return: A ``Deferred`` firing with the first ``Truthy`` response from
        ``predicate``.
    """
    d = maybeDeferred(predicate)
    then = time.time()
    def loop(result):
        if timeout and time.time() - then > timeout:
            raise TimeoutError()
        if not result:
            d = deferLater(reactor, 0.1, predicate)
            d.addCallback(loop)
            return d
        return result
    d.addCallback(loop)
    return d


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
                ip, " ".join(map(quote, ["bash", "-c", "echo; " + command])))
        print "running command:"
        print command
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
                   " ".join(map(quote, ["bash", "-c", "echo; " + command]))]
        return getProcessOutput(executable, command, errortoo=True)

    def runSSHRaw(self, ip, command, username=None):
        command = 'ssh -o LogLevel=error -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i %s %s@%s %s' % (self.config["private_key_path"],
                username if username is not None else self.config["remote_server_username"],
                ip, command)
        return subprocess.check_output(command, shell=True)

    def runSSHPassthru(self, ip, command, username=None):
        command = 'ssh -o LogLevel=error -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i %s %s@%s %s' % (self.config["private_key_path"],
                username if username is not None else self.config["remote_server_username"],
                ip, " ".join(map(quote, "echo; " + command)))
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
            private_key_path=None, remote_server_username=None, async=False):
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
        if async:
            return getProcessOutput("/bin/bash", ["-c", scp], errortoo=True)
        else:
            return subprocess.check_output(scp, shell=True)
