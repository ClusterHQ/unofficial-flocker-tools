# Unofficial Flocker Tools

This repository contains several ClusterHQ Labs projects.

* [Experimental Installer](https://docs.clusterhq.com/en/latest/labs/installer.html)
* [Prototype Volumes CLI](https://docs.clusterhq.com/en/latest/labs/volumes-cli.html)
* [Prototype Volumes GUI](https://docs.clusterhq.com/en/latest/labs/volumes-gui.html)

## Running dockerized

You can run any UFT command dockerized by:

### 1. Write out some wrapper scripts

```
$ for CMD in flocker-{ca,deploy,config,install,plugin-install,sample-files,tutorial,volumes}; do
    cat <<EOF |sudo tee /usr/local/bin/uft-$CMD >/dev/null
#!/bin/sh
docker run -ti -v \$PWD:/pwd clusterhq/uft $CMD \$@
EOF
sudo chmod +x /usr/local/bin/uft-$CMD; done
```

### 2. You now have access to all the unofficial flocker tools in your path with `uft-` prefixes

```
$ uft-flocker-ca --help
```

## Documentation

Please refer to the individual projects above for instructions on how to use this repo.
You may want to start with the installer docs.
