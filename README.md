# esi-leap

esi-leap is an OpenStack service for acting as a FLOCX provider to communicate with a FLOCX
marketplace. It is intended to work on top of the
[esi-common library](https://github.com/CCI-MOC/esi-common), which supports an OpenStack
install that simulates Ironic multi-tenancy through the use of `project_owner_id` and
`project_id` property attributes.


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

The esi-leap service requires a database to store its information. To set this up using
the MySQL database used by other OpenStack services, run the following, replacing
\<PASSWORD\> with a suitable password and \<DATABASE\_IP\> with the IP address of your
MySQL database (if you're not sure, use localhost or 127.0.0.1).

```
    $ mysql -u root -p
    mysql> CREATE USER 'esi_leap'@'<DATABASE_IP>' IDENTIFIED BY '<PASSWORD>';
    mysql> CREATE DATABASE esi_leap CHARACTER SET utf8;
    mysql> GRANT ALL PRIVILEGES ON esi_leap.* TO 'esi_leap'@'<DATABASE_IP>';
    mysql> FLUSH PRIVILEGES;
```

If you use this method, the resulting database connection string should be:

```
    mysql+pymysql://esi_leap:PASSWORD@DATABASE_IP/esi_leap
```


### Configuration

Run the following to generate the configuration file and copy it to the right place:

```
    $ tox -egenconfig
    $ sudo mkdir /etc/esi-leap
    $ sudo cp etc/esi-leap/esi-leap.conf.sample /etc/esi-leap/esi-leap.conf
```

Edit `/etc/esi-leap/esi-leap.conf` with the proper values. Some useful values include:

```
[DEFAULT]

debug=True
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
username=admin
password=<password>
user_domain_name=Default
project_name=admin
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
    $ openstack service create --name esi-leap lease
    $ openstack endpoint create esi-leap --region RegionOne public http://localhost:7777
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
