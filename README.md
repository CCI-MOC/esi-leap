# esi-leap

esi-leap is an OpenStack service for managing leases on Ironic nodes. It is intended
to work on top of the [esi-common library](https://github.com/CCI-MOC/esi-common), which
supports an OpenStack install that simulates Ironic multi-tenancy through the use of
`project_owner_id` and `project_id` property attributes.


### Installation

Start by installing the python code:

```
    $ git clone https://github.com/CCI-MOC/esi-leap
    $ cd esi-leap
    $ sudo python setup.py install
```

Next, generate the configuration file:

```
    $ tox -egenconfig
    $ sudo mkdir /etc/esi-leap
    $ sudo cp etc/esi-leap/esi-leap.conf.sample /etc/esi-leap/esi-leap.conf
```

Edit `/etc/esi-leap/esi-leap.conf` with the proper values.

Now you can instantiate the database:

```
    $ sudo esi-leap-dbsync create_schema
```

Once that's done, you can run the manager and API services:


```
    $ sudo esi-leap-manager
    $ sudo esi-leap-api
```
