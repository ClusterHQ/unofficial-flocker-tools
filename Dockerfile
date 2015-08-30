FROM        ubuntu:14.04

# Last build date - this can be updated whenever there are security updates so
# that everything is rebuilt
ENV         security_updates_as_of 2014-07-06

# Install security updates and required packages
RUN         apt-get -qy update
RUN         apt-get -y install apt-transport-https software-properties-common
RUN         add-apt-repository -y "deb https://clusterhq-archive.s3.amazonaws.com/ubuntu/$(lsb_release --release --short)/\$(ARCH) /"
RUN         apt-get -qy update
RUN         apt-get -qy upgrade
RUN         apt-get -y --force-yes install clusterhq-flocker-cli
RUN         apt-get -qy install python-pip
RUN         apt-get -qy install python-dev
#RUN         apt-get -qy install python-pyasn1
RUN         apt-get -qy install libyaml-dev
RUN         apt-get -qy install libffi-dev
RUN         apt-get -qy install libssl-dev

ADD         . /app

# Install requirements from the project's setup.py
RUN         cd /app; pip install .

WORKDIR     /pwd
