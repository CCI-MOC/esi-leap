# This file contains the configuration for containerized esi-leap

# Use python as the parent image for esi-leap
FROM python:3.11

LABEL description="ESI-LEAP -- ESI lease policy manager"

# The working directory for esi-leap inside the container
WORKDIR /esi-leap

# Copy the files of esi leap inside the container
COPY run_services.sh run_services.sh

RUN mkdir -p /var/log/esi-leap
RUN touch /var/log/esi-leap/esi-leap-dbsync.log

# Run command to install dependencies for esi-leap
RUN apt update -y && apt install -y python3-pymysql
RUN pip3 install esi-leap mysql-connector pymysql

# Indicate that service listens on this port
EXPOSE 7777

CMD ["bash", "./run_services.sh"]
