# This file will contain the configuration for containerized esi-leap

# Use python as the parent image for esi-leap

FROM python:3.11

# Use label descriptor

LABEL description="ESI-LEAP container file"

# Maintainer details

MAINTAINER <tzumainn@redhat.com>

# The working directory for esi-leap inside the container

WORKDIR /esi-leap

# Copy the files of esi leap inside the container
# Syntax : COPY <src> <destination>

COPY run_services.sh run_services.sh

# Run command to install dependencies for esi-leap

RUN pip install esi-leap

RUN pip install mysql-connector

RUN mkdir -p /var/log/esi-leap

RUN touch /var/log/esi-leap/esi-leap-dbsync.log

# Run command to install dependencies for esi-leap
RUN apt update -y && apt install -y python3-pymysql

RUN pip3 install pymysql

# Expose the default port for esi-leap-api
# Use -p flag while running the image to map ports

EXPOSE 7777
RUN ["chmod", "+x", "./run_services.sh"]
CMD ./run_services.sh
