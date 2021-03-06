#!/bin/sh
do_install() {
IMAGE="clusterhq/uft:latest"
DEPRECATION_WARNING=$(cat <<EOF
deprecated in Flocker 1.14.0 and will be removed in future versions of Flocker.
Use the official installation methods and tools instead.
See https://docs.clusterhq.com.
EOF
)

for CMD in flockerctl flocker-ca flocker-deploy flocker-config flocker-install flocker-plugin-install flocker-sample-files flocker-tutorial flocker-volumes flocker-get-nodes flocker-destroy-nodes volume-hub-agents-install; do
    if [ "$CMD" = "flockerctl" ] || [ "$CMD" = "volume-hub-agents-install" ]; then
        PREFIX=""
        DEPRECATED="FALSE"
    else
        PREFIX="uft-"
        # Deprecate all the uft-* tools.
        DEPRECATED="TRUE"
    fi
    cat <<EOF |sudo tee /usr/local/bin/${PREFIX}${CMD} >/dev/null
#!/bin/sh
DEPRECATED="${DEPRECATED}"
DEPRECATION_WARNING=\$(cat <<END_WARNING
${DEPRECATION_WARNING}
END_WARNING
)
if [ "\${DEPRECATED}" = "TRUE" ]; then
    echo "WARNING: ${PREFIX}${CMD} was \${DEPRECATION_WARNING}" >&2
    echo "" >&2
fi
if docker version >/dev/null 2>&1; then
    SUDO_PREFIX=""
elif sudo docker version >/dev/null 2>&1; then
    SUDO_PREFIX="sudo "
else
    echo "==========================================================================="
    echo "Unable to reach docker daemon with or without sudo. Please check that"
    echo "docker is running and that DOCKER_HOST is set correctly."
    echo
    echo "If you use docker-machine (e.g. as part of docker toolbox) then"
    echo "'eval \\\$(docker-machine env default)' or similar may help."
    echo
    echo "In that case, also make sure your docker machine is running, using e.g."
    echo "'docker-machine start default'."
    echo "==========================================================================="
    exit 1
fi

if [ ! "\$IGNORE_NETWORK_CHECK" = "1" ]; then
    if ! \$SUDO_PREFIX docker run --rm gliderlabs/alpine wget -q -O /dev/null -T 5 http://check.clusterhq.com/uft.txt
    then
        echo "==========================================================================="
        echo "Unable to establish network connectivity from inside a container."
        echo
        echo "If you see an error message above, that may give you a clue how to fix it."
        echo
        echo "If you run docker in a VM, restarting the VM often helps, especially if"
        echo "you have changed network (and/or DNS servers) since starting the VM."
        echo
        echo "If you are using docker-machine (e.g. as part of docker toolbox), you can"
        echo "run the following command (or similar) to do that:"
        echo
        echo "    docker-machine restart default && eval \\\$(docker-machine env default)"
        echo
        echo "To ignore this check, and proceed anyway (e.g. if you know you are offline)"
        echo "set IGNORE_NETWORK_CHECK=1"
        echo "==========================================================================="
        exit 1
    fi
fi


\$SUDO_PREFIX docker run -ti --rm -e FLOCKER_CERTS_PATH="\${FLOCKER_CERTS_PATH}" -e FLOCKER_USER="\${FLOCKER_USER}" -e FLOCKER_CONTROL_SERVICE="\${FLOCKER_CONTROL_SERVICE}" -e EARLY_DOCKER="\${EARLY_DOCKER}" -e TOKEN="\${TOKEN}" -e CUSTOM_REPO=\${CUSTOM_REPO} -e FORCE_DESTROY=\${FORCE_DESTROY} -e CONTAINERIZED=1 -v /:/host -v \$PWD:/pwd:z $IMAGE $CMD "\$@"
EOF
    sudo chmod +x /usr/local/bin/${PREFIX}${CMD}
    if [ "${DEPRECATED}" = "TRUE" ]; then
        EXTRA=" (deprecated)"
    else
        EXTRA=""
    fi
    echo "Installed /usr/local/bin/${PREFIX}${CMD}${EXTRA}"
done

if docker version >/dev/null 2>&1; then
    SUDO_PREFIX=""
elif sudo docker version >/dev/null 2>&1; then
    SUDO_PREFIX="sudo "
else
    echo "==========================================================================="
    echo "Unable to reach docker daemon with or without sudo. Please check that"
    echo "docker is running and that DOCKER_HOST is set correctly."
    echo
    echo "If you use docker-machine (e.g. as part of docker toolbox) then"
    echo "'eval \$(docker-machine env default)' or similar may help."
    echo
    echo "In that case, also make sure your docker machine is running, using e.g."
    echo "'docker-machine start default'."
    echo "==========================================================================="
    exit 1
fi

echo "Verifying internet connectivity inside container..."
if [ ! "$IGNORE_NETWORK_CHECK" = "1" ]; then
    if ! $SUDO_PREFIX docker run --rm gliderlabs/alpine wget -q -O /dev/null -T 5 http://check.clusterhq.com/uft-install.txt
    then
        echo "==========================================================================="
        echo "Unable to establish network connectivity from inside a container."
        echo
        echo "If you see an error message above, that may give you a clue how to fix it."
        echo
        echo "If you run docker in a VM, restarting the VM often helps, especially if"
        echo "you have changed network (and/or DNS servers) since starting the VM."
        echo
        echo "If you are using docker-machine (e.g. as part of docker toolbox), you can"
        echo "run the following command (or similar) to do that:"
        echo
        echo "    docker-machine restart default && eval \$(docker-machine env default)"
        echo
        echo "To ignore this check, and proceed anyway (e.g. if you know you are offline)"
        echo "set IGNORE_NETWORK_CHECK=1"
        echo "==========================================================================="
        exit 1
    fi
fi

echo "Pulling Docker image for Flocker installer..."
$SUDO_PREFIX docker pull $IMAGE
if [ -n "${DEPRECATION_WARNING}" ]; then
    echo "" >&2
    echo "WARNING: Some of these commands were ${DEPRECATION_WARNING}" >&2
fi
echo ""
}

# wrapped up in a function so that we have some protection against only getting
# half the file during "curl | sh"
do_install
