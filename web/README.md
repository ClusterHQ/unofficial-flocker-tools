# Trying out the volumes GUI

Prerequisites:

* A Flocker cluster, if you don't have one of these then try [unofficial-flocker-tools](https://github.com/ClusterHQ/unofficial-flocker-tools/)
* Docker
* A web browser (tested on Google Chrome)

## step 1 -- run the container with your local keys

```
export CERTS=/srv/projects/docker-plugins-demo/runner/unofficial-flocker-tools
export CONTROL_SERVICE=54.157.225.189
docker run -p 80:80 \
    -e CONTROL_SERVICE=$CONTROL_SERVICE \
    -e USERNAME=user \
    -e CERTS_PATH=/ \
    -v $CERTS/flockerdemo.key:/user.key \
    -v $CERTS/flockerdemo.crt:/user.crt \
    -v $CERTS/cluster.crt:/cluster.crt \
    clusterhq/experimental-flocker-volumes-gui
```

TODO: test boot2docker

## step 2 -- load up the experimental flocker gui

Go to [http://localhost/client](http://localhost/client).

## step 3

There is no step 3.
