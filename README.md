# unofficial-flocker-tools

## deploy.py

*Automate key generation and push to nodes via SCP.*

Assuming you have root SSH access to some machines you want to set up as a flocker cluster, this will automate the flocker key generation and pushing.

Prerequisites:

* flocker-cli for your system (from http://build.clusterhq.com/results/omnibus/storage-driver-configuration-FLOC-1925/ for now)
* python 2.7
* pyyaml module (`sudo pip install pyyaml`)

```
git clone https://github.com/lukemarsden/unofficial-flocker-tools
cd unofficial-flocker-tools
mv cluster.yml.sample cluster.yml
vim cluster.yml # customize for your cluster
./install.py cluster.yml
./deploy.py cluster.yml
```

