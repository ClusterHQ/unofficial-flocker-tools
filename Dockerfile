FROM        ubuntu:14.04

# Last build date - this can be updated whenever there are security updates so
# that everything is rebuilt
ENV         security_updates_as_of 2015-08-14

ADD         . /app

# Install security updates and required packages
RUN         apt-get -qy update && \
            apt-get -y install apt-transport-https software-properties-common wget zip && \
            wget -qO /tmp/terraform.zip https://dl.bintray.com/mitchellh/terraform/terraform_0.6.3_linux_amd64.zip && \
            cd /tmp && unzip terraform.zip && rm terraform.zip && mv terraform terraform-provider-aws terraform-provider-template terraform-provisioner-local-exec /usr/local/bin/ && rm * && \
            add-apt-repository -y "deb https://clusterhq-archive.s3.amazonaws.com/ubuntu/$(lsb_release --release --short)/\$(ARCH) /" && \
            apt-get -qy update && \
            apt-get -qy upgrade && \
            apt-get -qy install python-pip python-dev libyaml-dev libffi-dev libssl-dev && \
            apt-get -y --force-yes install python python-setuptools python-requests clusterhq-flocker-cli && \
            cd /app && /opt/flocker/bin/pip install --no-cache-dir . && \
            apt-get remove --purge -y $(apt-mark showauto) && \
            apt-get -y install apt-transport-https software-properties-common && \
            apt-get -y --force-yes install python python-setuptools python-requests clusterhq-flocker-cli && \
            rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /app

ENV         PATH /opt/flocker/bin:$PATH
WORKDIR     /pwd
