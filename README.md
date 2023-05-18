# esi-leap

esi-leap is an OpenStack service for leasing baremetal nodes, designed to run
on top of [multi-tenant
Ironic](https://docs.openstack.org/ironic/latest/admin/node-multitenancy.html).
It consists of an API that provides endpoints for leasing operations and a
manager service that updates the status of leases and offers as required. See
the [documentation](https://esi.readthedocs.io/en/latest/index.html) for
more info on ESI.


### Installation

To install as a package:
 - `pip install esi-leap`

To install from source:

```
    $ git clone https://github.com/CCI-MOC/esi-leap
    $ cd esi-leap
    $ sudo python setup.py install
```


### Client

esi-leap has a command line client which can be found here:
https://github.com/CCI-MOC/python-esileapclient


### Create the esi-leap Database

The esi-leap service requires a database to store its information. To set this
up using the MySQL database used by other OpenStack services, run the following
commands, replacing \<PASSWORD\> with a suitable password and \<DATABASE\_IP\>
with the IP address of your MySQL database (if you're not sure, use localhost
or 127.0.0.1).

```
    $ mysql -u root -p
    mysql> CREATE USER 'esi_leap'@'<DATABASE_IP>' IDENTIFIED BY '<PASSWORD>';
    mysql> CREATE USER 'esi_leap'@'%' IDENTIFIED BY '<PASSWORD>';
    mysql> CREATE DATABASE esi_leap CHARACTER SET utf8;
    mysql> GRANT ALL PRIVILEGES ON esi_leap.* TO 'esi_leap'@'<DATABASE_IP>';
    mysql> GRANT ALL PRIVILEGES ON esi_leap.* TO 'esi_leap'@'%';
    mysql> FLUSH PRIVILEGES;
```

If you use this method, the resulting database connection string should be:

```
    mysql+pymysql://esi_leap:PASSWORD@DATABASE_IP/esi_leap
```


### Configuration

Run the following commands to generate the configuration file and copy it to
the right place:

```
    $ tox -egenconfig
    $ sudo mkdir /etc/esi-leap
    $ sudo cp etc/esi-leap/esi-leap.conf.sample /etc/esi-leap/esi-leap.conf
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


### Create the OpenStack Service

```
    $ openstack user create --domain default --password-prompt esi-leap
    $ openstack role add --project service --user esi-leap admin
    $ openstack service create --name esi-leap lease
    $ openstack endpoint create esi-leap --region RegionOne public http://<YOUR_IP>:7777
```


### Run the Services

Start by instantiating the database:

```
    $ sudo esi-leap-dbsync create_schema
```

Once that's done, you can run the manager and API services:


```
    $ sudo esi-leap-manager
    $ sudo esi-leap-api
```

### Installation using Containerization

By encapsulating the ESI Leap into a container, all the necessary dependencies, configurations and services are bundled into a single package.

Please make sure to follow the instructions in the [Configuration](#configuration) section to generate the esi-leap.conf file.

Make sure to follow the instructions in the [Create Openstack Service](#create-the-openstack-service) to create the OpenStack service and endpoint. 

After that build the container image using the podman build command, as Containerfile is located in the current directory. The syntax is as follows:

```
    $ podman build -t <image-name> -f Containerfile . 
```

Once the container image is built, you can run it using the podman run command. The syntax is as follows:

```
    $ podman run --name <container-name> -p <host-port>:<container-port> -d -v <path-to-esi-leap.conf-file>:/etc/esi-leap <image-name>
```


### Using Dummy Nodes

If you wish to use dummy nodes instead of Ironic nodes, simply specify the `dummy_node_dir`
as specified above. Once you do so, add dummy nodes as follows:

```
cat <<EOF > /tmp/nodes/1718
{
    "project_owner_id": "project id of dummy node owner",
    "server_config": {
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

`1718` is the dummy node UUID; replace it with whatever you'd like. When creating an offer
for this dummy node, simply specify `resource_type` as `dummy_node` and `resource_uuid` as
`1718`.
