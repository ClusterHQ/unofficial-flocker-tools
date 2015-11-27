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
if docker version >/dev/null 2>&1; then
    SUDO_PREFIX=""
elif sudo docker version >/dev/null 2>&1; then
    SUDO_PREFIX="sudo "
else
    echo "Unable to reach docker daemon with or without sudo. Please check that"
    echo "docker is running and that DOCKER_HOST is set correctly."
    echo
    echo "If you use docker-machine (e.g. as part of docker toolbox) then"
    echo "'eval \\\$(docker-machine env default)' or similar may help."
    echo "In that case, also make sure your docker machine is running, using"
    echo "e.g. echo "'docker-machine start default'."
    exit 1
fi

if ! \$IGNORE_NETWORK_CHECK; then
    if ! \$SUDO_PREFIX docker run -ti gliderlabs/alpine wget -q -O /dev/null -T 5 http://check.clusterhq.com/?source=uft
        then
            echo "Unable to establish network connectivity from inside a container."
            echo "If you see an error message above, that may give you a clue how to fix it."
            echo "If you run docker in a VM, restarting the VM often helps, especially if"
            echo "you have changed network (and/or DNS servers) since starting the VM."
            echo "If you are using docker-machine (e.g. as part of docker toolbox), you can"
            echo "run the following command (or similar) to do that:"
            echo "    docker-machine restart default && eval \\\$(docker-machine env default)"
            echo "To ignore this check, and proceed anyway (e.g. if you know you are offline)"
            echo "set IGNORE_NETWORK_CHECK=1"
            exit 1
        fi
    fi

\$SUDO_PREFIX docker run -ti --rm -e TOKEN="\${TOKEN}" -e CUSTOM_REPO=\${CUSTOM_REPO} -e FORCE_DESTROY=\${FORCE_DESTROY} -e CONTAINERIZED=1 -v /:/host -v \$PWD:/pwd:z $IMAGE $CMD "\$@"
EOF
    sudo chmod +x /usr/local/bin/${PREFIX}${CMD}
    echo "Installed /usr/local/bin/${PREFIX}${CMD}"
done
echo "Pulling Docker image for Flocker installer..."
docker pull $IMAGE
