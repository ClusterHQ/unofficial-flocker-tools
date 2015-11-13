#!/bin/sh
IMAGE="clusterhq/uft:latest"
for CMD in flockerctl flocker-ca flocker-deploy flocker-config flocker-install flocker-plugin-install flocker-sample-files flocker-tutorial flocker-volumes flocker-get-nodes flocker-destroy-nodes volume-hub-agents-install; do
    if [ "$CMD" = "flockerctl" ] || [ "$CMD" = "volume-hub-agents-install" ]; then
        PREFIX=""
    else
        PREFIX="uft-"
    fi
    cat <<EOF |sudo tee /usr/local/bin/${PREFIX}${CMD} >/dev/null
#!/bin/sh
docker run -ti --rm -e TOKEN="\${TOKEN}" CUSTOM_REPO=\${CUSTOM_REPO} -e FORCE_DESTROY=\${FORCE_DESTROY} -e CONTAINERIZED=1 -v /:/host -v \$PWD:/pwd $IMAGE $CMD "\$@"
EOF
    sudo chmod +x /usr/local/bin/${PREFIX}${CMD}
    echo "Installed /usr/local/bin/${PREFIX}${CMD}"
done
echo "Pulling Docker image for Flocker installer..."
docker pull $IMAGE
