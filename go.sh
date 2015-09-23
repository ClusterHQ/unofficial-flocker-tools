#!/bin/sh
IMAGE="clusterhq/uft:latest"
for CMD in flocker-ca flocker-deploy flocker-config flocker-install flocker-plugin-install flocker-sample-files flocker-tutorial flocker-volumes flocker-get-nodes flocker-destroy-nodes; do
    cat <<EOF |sudo tee /usr/local/bin/uft-$CMD >/dev/null
#!/bin/sh
docker run -ti -e CUSTOM_REPO=\${CUSTOM_REPO} -e FORCE_DESTROY=\${FORCE_DESTROY} -e CONTAINERIZED=1 -v /:/host -v \$PWD:/pwd $IMAGE $CMD \$@
EOF
sudo chmod +x /usr/local/bin/uft-$CMD
echo "Installed /usr/local/bin/uft-$CMD"
done
echo "Pulling Docker image for Flocker installer..."
docker pull $IMAGE
