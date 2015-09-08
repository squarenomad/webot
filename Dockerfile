################################################
# Dockerfile to build panyabot container images
# Based on raspbian
################################################
#Set the base image to raspbian
FROM resin/rpi-raspbian:jessie

# File Author / Maintainer
MAINTAINER Wachira Ndaiga

# Update the repository sources list and install dependancies
RUN sudo apt-get update && apt-get install -y \
    python \
    python-dev \
    python-pip \
    usbutils \
    bluetooth \
    bluez \
    python-bluez

# Set application directory tree
COPY . /panyabot
WORKDIR /panyabot
RUN cd /panyabot

# Create running environment
RUN pip install virtualenv
RUN virtualenv flask --system-site-packages
RUN flask/bin/pip install -r requirements.txt
RUN chmod 755 run.sh
RUN flask/bin/python db_create.py
RUN flask/bin/python db_migrate.py
RUN flask/bin/python tests.py

# Expose ports
EXPOSE 5000

# Start web app
 CMD ["/bin/bash", "run.sh"]