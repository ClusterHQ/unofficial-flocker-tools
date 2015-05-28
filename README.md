# unofficial-flocker-tools

## what is here

This repo makes it easy to install flocker on some nodes and configure the requisite keys.

See the [official docs](http://doc-dev.clusterhq.com/) for the full long-form installation instructions.

Prerequisites:

* flocker-cli for your local system (from http://build.clusterhq.com/results/omnibus/storage-driver-configuration-FLOC-1925/ for now)
* python 2.7
* pyyaml module (`sudo pip install pyyaml`)

## get the repo

```
git clone https://github.com/lukemarsden/unofficial-flocker-tools
cd unofficial-flocker-tools
```

## get some nodes

provision some machines, somehow.

* Amazon EC2 if you want to use our EBS backend (note VMs must be in the same AZ)
* OpenStack deployment (e.g. Rackspace, private cloud) if you want to use our OpenStack backend
* ~~Any other infrastructure if you want to try out our alpha ZFS backend~~ (does not work yet)

## cluster.yml

There are 3 example configuration files that correspond to the backend Flocker will use - base your cluster.yml on one of these files:

 * [AWS EBS](cluster.yml.ebs.sample)
 * [Opentstack Cinder](cluster.yml.openstack.sample)
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

 * You need to ensure that machines can be SSH'd into as root
 * You need a private key to access the machines - you can configure this in the `private_key_path` of cluster.yml

