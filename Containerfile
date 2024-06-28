# This file contains the configuration for containerized esi-leap

# Use python as the parent image for esi-leap
FROM docker.io/python:3.11

LABEL description="ESI-LEAP -- ESI lease policy manager"

# Indicate that service listens on this port
EXPOSE 7777

# The working directory for esi-leap inside the container
WORKDIR /esi-leap

# Copy the requirements file and install dependencies
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy the entire local directory contents to the container
COPY . ./

# Install the local version of esi-leap
RUN pip install .

# Create necessary directories and files
RUN mkdir -p /var/log/esi-leap
RUN touch /var/log/esi-leap/esi-leap-dbsync.log

# Command to run the services
CMD ["bash", "./run_services.sh"]
