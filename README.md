# Hatch: a tool for easily experimenting with container clustering systems

Experimenting with container clustering tools like Swarm, Kubernetes, or Mesos/Marathon?

The setup for these tools can involve some pretty complex processes, which might slow you down.

There are lots of tutorials online, but no single tool which makes it easy to consistenly spin up any and all of them.

Enter `hatch`, a tool for easily experimenting with container clustering systems.

It's not meant for production deployments, rather, for that initial phase where you're playing around with stuff and kicking the tyres.
Maybe you want to deploy something semi-serious, just to get a feel for it.

## Supported Orchestration Frameworks

* Docker Swarm
* Kubernetes
* Mesos/Marathon (coming soon)

You should only install one of these at a time.

## Supported Volume Managers

* Flocker (coming soon: optional)

Flocker integrates with all of the Orchestration Frameworks above to enable support for stateful containers, like databases, queues and key-value stores.

## Supported Operating Systems

* Client side (where you run `hatch`, that's your machine):

    * Any machine that can run Docker which has an internet connection

* Server side (the machines that `hatch` creates for you):

    * Ubuntu 14.04
    * CoreOS
    * CentOS 7 (coming soon)

## Supported Infrastructure Providers

* Amazon EC2
* Google Compute Engine (coming soon)
* Vagrant (coming soon)
* Managed (your own servers - coming soon)

## Example: Kubernetes on CoreOS

Let's hatch a Kubernetes cluster on CoreOS on AWS with Flocker!

## Example: Swarm on AWS

Let's hatch a Swarm cluster on Ubuntu on AWS with Flocker!

```
$ curl -sSL https://get.flocker.io |sh
$ mkdir -p ~/clusters/test; cd ~/clusters/test
$ hatch init --os ubuntu --cloud aws flocker swarm
$ hatch deploy
$ flockerctl status
$ hatch status
$ eval $(hatch env)

$ open http://${NODE1_PUBLIC}/
$ ssh ${REMOTE_USER}@${MASTER_PUBLIC}

master$ git clone https://github.com/clusterhq/hatch
master$ cd hatch/tutorial
master$ export DOCKER_HOST=localhost:<swarm_master-port>
master$ docker-compose up -d -f node1.yml # docker-compose file should say something about constraints
<reload the web page: add some state to app>
master$ docker-compose stop && docker-compose rm -f
master$ docker-compose up -d -f node2.yml
<observe that the app is availble on other IP and that the data is still there!>
```
