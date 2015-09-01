#!/bin/sh
for CMD in flocker-{ca,deploy,config,install,plugin-install,sample-files,tutorial,volumes}; do
    cat <<EOF |sudo tee /usr/local/bin/uft-$CMD >/dev/null
#!/bin/sh
docker run -ti -v \$PWD:/pwd clusterhq/uft $CMD \$@
EOF
sudo chmod +x /usr/local/bin/uft-$CMD; done
