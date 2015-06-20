# so you want a flocker cluster quickly?

## what is here

this repo makes it easy to install and use flocker on some nodes and configure the requisite keys.

see the [official docs](https://docs.clusterhq.com/en/1.0.0/using/installing/index.html) for the full long-form installation instructions.

prerequisites:

* flocker-cli for your local system (from https://docs.clusterhq.com/en/1.0.0/using/installing/index.html#installing-flocker-cli)
* python 2.7
* pip
* OS packages:
  * Ubuntu/Debian: `build-essential libssl-dev libffi-dev python-dev`
  * RHEL/Fedora: `gcc libffi-devel python-devel openssl-devel`
* optional: virtualenv

## get the repo and install dependencies

**note**: You may wish to [make a virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/):

```
virtualenv venv
source venv/bin/activate
```

download the repo and install

```
git clone https://github.com/ClusterHQ/unofficial-flocker-tools
cd unofficial-flocker-tools
pip install .
```

this will install the following scripts in your `$PATH`:

* flocker-config
* flocker-install
* flocker-plugin-install
* flocker-tutorial
* flocker-volumes

## get some nodes

provision some machines, somehow. use ubuntu 14.04 or centos 7.

* Amazon EC2 if you want to use our EBS backend (note VMs must be in the same AZ)
* OpenStack deployment (e.g. Rackspace, private cloud) if you want to use our OpenStack backend
* ~~Any other infrastructure if you want to try out our alpha ZFS backend~~ (does not work yet)

make sure you can log into the nodes as **root** with a private key. (e.g. on ubuntu on AWS, `sudo cp .ssh/authorized_keys /root/.ssh/authorized_keys`)

you may want to pick a node to be the control node and give it a DNS name (set up an A record for it with your DNS provider). using a DNS name is optional -- you can also just use its IP address.

## cluster.yml

there are 3 example configuration files that correspond to the backend Flocker will use - base your cluster.yml on one of these files:

 * [AWS EBS](cluster.yml.ebs.sample)
 * [Openstack Cinder](cluster.yml.openstack.sample)
 * [ZFS](cluster.yml.zfs.sample)

for example:

```
mv cluster.yml.ebs.sample cluster.yml
vim cluster.yml # customize for your cluster
```

## install

```
flocker-install cluster.yml
```

this will install the packages on your nodes

at this point you will need to manually install the latest (highest numbered) packages from http://build.clusterhq.com/results/omnibus/master/ onto your nodes as well.


## config

```
flocker-config cluster.yml
```

this will configure certificates, push them to your nodes, and set up firewall rules for the control service

on AWS, you'll need to add a firewall rule for TCP port 4523 and 4524 if you want to access the control service/API remotely.

## plugin

```
flocker-plugin-install cluster.yml
```

this will configure api certificates for the docker-plugin and push them to your nodes - it will name them `/etc/flocker/plugin.{crt,key}`

it will git clone the plugin repo, checkout a branch and install the dependencies (pip install) and write a service file (upstart/systemd) for the plugin

it will also download a customized docker binary that supports the `--volume-driver` flag and restart the docker service.

The environment variables that control this are:

 * `DOCKER_BINARY_URL` - the url to download a customized docker binary from
 * `DOCKER_SERVICE_NAME` - the name of the service docker is installed with (docker, docker.io etc)
 * `PLUGIN_REPO` - the repo to install the docker plugin from
 * `PLUGIN_BRANCH` - the branch of the plugin repo to use

## tutorial

```
flocker-tutorial cluster.yml
```

this will print out a tutorial customized to your deployment.

## volumes cli

A CLI tool to interact with the Flocker REST API.

```
$ flocker-volumes --help
Usage: flocker-volumes [options]
Options:
      --cluster-yml=      Location of cluster.yml file (makes other options
                          unnecessary) [default: ./cluster.yml]
      --certs-path=       Path to certificates folder [default: .]
      --user=             Name of user for which .key and .crt files exist
                          [default: user]
      --cluster-crt=      Name of cluster cert file [default: cluster.crt]
      --control-service=  Hostname or IP of control service
      --control-port=     Port for control service REST API [default: 4523]
      --version           Display Twisted version and exit.
      --help              Display this help and exit.
Commands:
    create          create a flocker dataset
    destroy         mark a dataset to be deleted
    list            list flocker datasets
    list-nodes      show list of nodes in the cluster
    move            move a dataset from one node to another
    version         show version information
```

## sample files

A tool to copy the sample configuration files into the current working directory.

```
$ flocker-sample-files
```

## notes

* you need to ensure that machines can be SSH'd into as root
* you need a private key to access the machines - you can configure this in the `private_key_path` of cluster.yml
