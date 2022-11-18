# This file will contain the configuration for containerized esi-leap

# Use python as the parent image for esi-leap

FROM python:3

# Use label descriptor

LABEL description="ESI-LEAP container file"

# Maintainer details

MAINTAINER <tzumainn@redhat.com>

# The working directory for esi-leap inside the container

WORKDIR /esi-leap

# Copy the files of esi leap inside the container
# Syntax : COPY <src> <destination>

COPY . .

# Run command to install dependencies for esi-leap

RUN pip install esi-leap

# Expose the default port for esi-leap-api
# Use -p flag while running the image to map ports

EXPOSE 7777

USER root

# Something for esi-leap-api and esi-leap-manager
# Not sure how to link these two here / bring inside the container

# Start processes for esi-leap-api and esi-leap-manager

# What is the entry point / executable for esi-leap?

RUN sudo esi-leap-dbsync create_schema

RUN esi-leap-manager

RUN esi-leap-api
