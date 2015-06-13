# Trying out the volumes GUI

Prerequisites:

* A Flocker cluster, if you don't have one of these then try [unofficial-flocker-tools](https://github.com/ClusterHQ/unofficial-flocker-tools/)
* `openssl` client, most OS X and Linux distros should already have this installed

## step 1 -- convert your user key and cert

First convert your user key, user cert and cluster key into a format Chrome can understand:

```
openssl pkcs12 -export -out certificate.p12 -inkey luke.key -in luke.crt -certfile cluster.crt
```

You do not need to specify a password.

Then go to Chrome settings, type "cert" into the search box, click "Manage Certificates", and import the certificate.p12.

## step 2 -- install chrome plugin to disable CORS

Flocker doesn't yet send CORS headers, so we have to workaround.
Install the [Allow-Control-Allow-Origin: * plugin](https://chrome.google.com/webstore/detail/allow-control-allow-origi/nlfbmbojpeacfghkpbjhddihlkkiljbi/related).


