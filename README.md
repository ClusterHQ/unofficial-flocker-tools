# Unofficial Flocker Tools

This repository contains several ClusterHQ Labs projects.

* [Experimental Installer](https://docs.clusterhq.com/en/latest/labs/installer.html)
* [Prototype Volumes CLI](https://docs.clusterhq.com/en/latest/labs/volumes-cli.html)
* [Prototype Volumes GUI](https://docs.clusterhq.com/en/latest/labs/volumes-gui.html)

## Running dockerized

### 1. Write out some wrapper scripts

```
$ curl https://get.flocker.io | sudo sh
```

### 2. You now have access to all the unofficial flocker tools in your path with `uft-` prefixes

```
$ uft-flocker-ca --help
```

## Documentation

Please refer to the individual projects above for instructions on how to use this repo.
You may want to start with the installer docs.

## Running tests

Run an integration test for the installer thus:

```
$ trial test_integration.py
```

Note the comment at the top of the `test_integration.py` file before running the test.
