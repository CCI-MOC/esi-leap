# esi-leap

esi-leap is an OpenStack service for leasing baremetal nodes, designed to run on top of [multi-tenant Ironic](https://docs.openstack.org/ironic/latest/admin/node-multitenancy.html). It consists of an API that provides endpoints for leasing operations and a manager service that updates the status of leases and offers as required. See the [documentation](https://esi.readthedocs.io/en/latest/index.html) for more info on ESI.

## Installation

To install as a package:

```
pip install esi-leap
```

To install from source:

```
git clone https://github.com/CCI-MOC/esi-leap
cd esi-leap
pip install .
```

## Client

esi-leap has a command line client which can be found here: https://github.com/CCI-MOC/python-esileapclient

## Create the esi-leap Database

The esi-leap service requires a database to store its information. To set this up using the MySQL database used by other OpenStack services, run the following commands, replacing `<PASSWORD>` with a suitable password and `<DATABASE_IP>` with the IP address of your MySQL database (if you're not sure, use `localhost` or `127.0.0.1`).

```
$ mysql -u root -p
mysql> CREATE USER 'esi_leap'@'%' IDENTIFIED BY '<PASSWORD>';
mysql> CREATE DATABASE esi_leap CHARACTER SET utf8;
mysql> GRANT ALL PRIVILEGES ON esi_leap.* TO 'esi_leap'@'%';
mysql> FLUSH PRIVILEGES;
```

If you use this method, the resulting database connection string should be:

```
mysql+pymysql://esi_leap:PASSWORD@DATABASE_IP/esi_leap
```

## Configuration

Run the following commands to generate the configuration file and copy it to
the right place:

```
tox -egenconfig
sudo mkdir /etc/esi-leap
sudo cp etc/esi-leap/esi-leap.conf.sample /etc/esi-leap/esi-leap.conf
```

Edit `/etc/esi-leap/esi-leap.conf` with the proper values. (see sample config
template below):

```
[DEFAULT]

log_dir=/var/log/esi-leap
transport_url=<transport URL for messaging>

[database]
connection=<db connection string>

# End-user authentication configuration
[keystone_authtoken]
www_authenticate_uri=<public Keystone endpoint>
auth_type=password
auth_url=<keystone auth URL>
username=admin
password=<password>
user_domain_name=Default
project_name=admin
project_domain_name=Default

# esi-leap internal authentication configuration
[keystone]
api_endpoint=<admin Keystone endpoint>
auth_type=password
auth_url=<keystone auth URL>
username=esi-leap
password=<password>
user_domain_name=Default
project_name=service
project_domain_name=Default

[oslo_concurrency]
lock_path=<lock dir>

[oslo_messaging_notifications]
driver=messagingv2
transport_url=<transport URL for messaging>

[ironic]                              # ONLY NECESSARY IF USING IRONIC NODES
auth_type = password
api_endpoint = <ironic API endpoint>
auth_url = <keystone auth URL>
project_name = service
project_domain_name = Default
user_domain_name = Default
username = ironic
password = <ironic password>

[dummy_node]                          # ONLY NECESSARY IF USING DUMMY NODES
dummy_node_dir=/tmp/nodes
```

## Create the OpenStack Service

```
openstack user create --domain default --password-prompt esi-leap
openstack role add --project service --user esi-leap admin
openstack service create --name esi-leap lease
openstack endpoint create esi-leap --region RegionOne public http://<YOUR_IP>:7777
```

## Run the Services

Start by creating the database schema:

```
esi-leap-dbsync create_schema
```

Once that's done, you can run the manager and API services:


```
esi-leap-manager
esi-leap-api
```

## Container Installation

You can build an `esi-leap` container using the included `Containerfile`:

```
podman build -t esi-leap .
```

Once the container image has been built, you can run it using the `podman run` command. First, make sure you have created an appropriate configuration file following the instructions in the [Configuration](#configuraiton) section, and ensure you have added the appropriate service and endpoint to your OpenStack environment as described in [Create the OpenStack Service](#create-the-openstack-service). Then you can run the image like this:

```
podman run --name <container-name> -p <host-port>:<container-port> -d \
  -v <path-to-esi-leap.conf-file>:/etc/esi-leap/esi-leap.conf esi-leap
```

## Using Dummy Nodes

If you wish to use dummy nodes instead of Ironic nodes, simply specify the `dummy_node_dir` as specified above. Once you do so, add dummy nodes as follows:

```
cat <<EOF > /tmp/nodes/1718
{
    "project_owner_id": "project id of dummy node owner",
    "properties": {
        "new attribute XYZ": "This is just a sample list of free-form attributes used for describing a server.",
        "cpu_type": "Intel Xeon",
        "cores": 16,
        "ram_gb": 512,
        "storage_type": "samsung SSD",
        "storage_size_gb": 204
    }
}
EOF
```

`1718` is the dummy node UUID; replace it with whatever you'd like. When creating an offer for this dummy node, simply specify `resource_type` as `dummy_node` and `resource_uuid` as `1718`.

## Contributing

### Pull requests

When you submit a pull request, your changes will be validated by running a number of automatic tests.

First, we run a series of [linters] and an automatic formatter on the code to check for a variety of minor issues and ensure consistent formatting. As a developer you will want to integrate these same checks into your local development environment:

1. Install the [pre-commit] tool using your favorite package manager.
2. Run `pre-commit install` from inside this repository.

This will enable a git [`pre-commit` hook][hooks] that will run the linters and formatter whenever you commit changes locally. We are using [`ruff`][ruff] for linting and formatting; this can be integrated into many editors to provide live checks as you are writing code.

Next, we run all unit tests across all the Python versions supported by the `esi-leap` code. We expect that any changes introducing new functionality will also include appropriate unit tests to exercise those changes.

[linters]: https://en.wikipedia.org/wiki/Lint_(software)
[pre-commit]: https://pre-commit.com/
[hooks]: https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks
[ruff]: https://github.com/astral-sh/ruff
