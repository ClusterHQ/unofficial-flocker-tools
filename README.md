# so you want a flocker cluster quickly?

## what is here

this repo makes it easy to install flocker on some nodes and configure the requisite keys.

see the [official docs](http://doc-dev.clusterhq.com/using/installing/index.html) for the full long-form installation instructions.

prerequisites:

* flocker-cli for your local system (from http://build.clusterhq.com/results/omnibus/storage-driver-configuration-FLOC-1925/ for now)
* python 2.7
* pyyaml module (`sudo pip install pyyaml`)

## get the repo

```
git clone https://github.com/lukemarsden/unofficial-flocker-tools
cd unofficial-flocker-tools
```

## get some nodes

provision some machines, somehow. use ubuntu 14.04 or centos 7.

* Amazon EC2 if you want to use our EBS backend (note VMs must be in the same AZ)
* OpenStack deployment (e.g. Rackspace, private cloud) if you want to use our OpenStack backend
* ~~Any other infrastructure if you want to try out our alpha ZFS backend~~ (does not work yet)

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
./install.py cluster.yml
```

this will install the packages on your nodes

## deploy

```
./deploy.py cluster.yml
```

this will configure certificates, push them to your nodes, and set up firewall rules for the control service

## tutorial

```
./tutorial.py cluster.yml
```

this will print out a tutorial customized to your deployment.

## notes

* you need to ensure that machines can be SSH'd into as root
* you need a private key to access the machines - you can configure this in the `private_key_path` of cluster.yml
