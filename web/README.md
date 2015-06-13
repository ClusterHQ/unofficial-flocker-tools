# Trying out the volumes GUI

Prerequisites:

* A Flocker cluster, if you don't have one of these then try [unofficial-flocker-tools](https://github.com/ClusterHQ/unofficial-flocker-tools/)
* Docker
* A web browser (tested on Google Chrome)

## step 1 -- run the container with your local keys

```
docker run -p 80 -e CONTROL_SERVICE=my.control.service -v $(PWD)/user.key:/user.key $(PWD)/user.crt:/user.crt $(PWD)/cluster.crt:/cluster.crt clusterhq/experimental-flocker-volumes-gui
```

TODO: test boot2docker

## step 2 -- load up the experimental flocker gui

Go to [http://localhost](http://localhost).

## step 3

There is no step 3.
