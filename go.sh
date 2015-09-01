#!/bin/sh
for CMD in flocker-ca flocker-deploy flocker-config flocker-install flocker-plugin-install flocker-sample-files flocker-tutorial flocker-volumes; do
    cat <<EOF |sudo tee /usr/local/bin/uft-$CMD >/dev/null
#!/bin/sh
docker run -ti -e CONTAINERIZED=1 -v /:/host -v \$PWD:/pwd clusterhq/uft $CMD \$@
EOF
sudo chmod +x /usr/local/bin/uft-$CMD
echo "Installed /usr/local/bin/uft-$CMD"
done
