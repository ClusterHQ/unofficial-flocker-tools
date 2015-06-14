# Trying out the volumes GUI

Prerequisites:

* A Flocker cluster, if you don't have one of these then try [unofficial-flocker-tools](https://github.com/ClusterHQ/unofficial-flocker-tools/)
* Docker
* A web browser (tested on Google Chrome)

## step 1 -- run the container with your local keys

```
cd unofficial-flocker-tools/web
export CERTS=$PWD/..
export CONTROL_SERVICE=your.control.service
export USERNAME=certuser
docker run -ti -p 80:80 \
    -e CONTROL_SERVICE=$CONTROL_SERVICE \
    -e USERNAME=user \
    -e CERTS_PATH=/ \
    -v $CERTS/$USERNAME.key:/user.key \
    -v $CERTS/$USERNAME.crt:/user.crt \
    -v $CERTS/cluster.crt:/cluster.crt \
    clusterhq/experimental-volumes-gui
```

TODO: test boot2docker

## step 2 -- load up the experimental flocker gui

Go to [http://localhost](http://localhost).

## step 3

There is no step 3.
