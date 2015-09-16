#!/bin/sh
# XXX remove :terraform from below before merging to master
for CMD in flocker-ca flocker-deploy flocker-config flocker-install flocker-plugin-install flocker-sample-files flocker-tutorial flocker-volumes flocker-get-nodes flocker-destroy-nodes; do
    cat <<EOF |sudo tee /usr/local/bin/uft-$CMD >/dev/null
#!/bin/sh
docker run -ti -e FORCE_DESTROY=\$FORCE_DESTROY -e CONTAINERIZED=1 -v /:/host -v \$PWD:/pwd clusterhq/uft:terraform $CMD \$@
EOF
sudo chmod +x /usr/local/bin/uft-$CMD
echo "Installed /usr/local/bin/uft-$CMD"
done
