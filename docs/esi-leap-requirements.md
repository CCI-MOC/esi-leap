# ESI-Leap Requirements

## Overview
ESI-Leap is a leasing service for bare metal. Ironic nodes owners can offer up their nodes to other users, while lessees can view offers and create a lease for available nodes.

## Definitions

### Offer
Ironic owners can bring up their nodes to ESI-Leap with an offer. An offer consists of the resource uuid, leasing period, and the status, etc. Here is an example offer schema:
```
    {
        'id': 27,
        'uuid': '534653c9-880d-4c2d-6d6d-f4f2a09e384',
        'name': 'o1',
        'project_id': '01d4e6a72f5c408813e02f664cc8c83e',
        'resource_type': 'ironic_node',
        'resource_uuid': '1718',
        'start_time': datetime.datetime(2016, 7, 16, 19, 20, 30),
        'end_time': datetime.datetime(2016, 8, 16, 19, 20, 30),
        'status': statuses.AVAILABLE,
        'properties': {},
        'created_at': None,
        'updated_at': None
    }
```
The offer data model is designed to support the following basic APIs:
* Get an offer by offer_uuid.
* Get offer(s) with filters: [project_id, status, resource_uuid, resource_type, (start_time, end_time), (available_start_time, available_end_time)].
* Create a new offer with given values.
* Update an offer's fields. Such as update the status to 'available' or 'expired', etc.
* Delete an offer by offer_uuid.
Based on the above APIs, ESI-Leap can provide various of functionalities for users. A lessee can retrieve offers with their requirements and find the suitable offer(s). An owner can check their offers' status and make changes.

The lifecycle of an offer is
* 'available' on offer creation.
* 'expired' once an offer's end_time has passed.
* 'deleted' if an offer is prematurely deleted.

The offer API endpoint can be reached at /v1/offers.

An example offer response is shown below:

```
{
    "uuid": "5d85b8e9-ad32-46b2-874e-969ec78e6e3d",
    "name": "o1,
    "project_id": "a78d93273b134c2fadf208a3e8c2da04",
    "resource_type": "dummy_node",
    "resource_uuid": "1718",
    "start_time": "2030-06-30T00:00:00",
    "end_time": "9999-12-31T23:59:59",
    "status": "available",
    "properties": {},
    "availabilities": [
        [
            "2030-06-30T00:00:00",
            "2050-06-30T00:00:00"
        ],
        [
            "2051-06-30T00:00:00",
            "2060-06-30T00:00:00"
        ],
        [
            "2061-06-30T00:00:00",
            "2070-06-30T00:00:00"
        ],
        [
            "2071-06-30T00:00:00",
            "2080-06-30T00:00:00"
        ],
        [
            "2081-06-30T00:00:00",
            "9999-12-31T23:59:59"
        ]
    ]
}

```
An offer response has the following fields:
* "uuid" is the primary key for an offer entry.
* "name" is an identifier the user may set for an offer on creation. Can be used for offer management instead of 'uuid'. Does not have to be unique.
* "project_id" is the project_id of the owner of the offer.
* "resource_type" is the type of resource being made available for leasing. To use with Ironic, set to 'ironic_node'. This is passed in as a string.
* "start_time" is a datetime representing the time in which the offer can be leased.
* "end_time" is a datetime representing the time in which the offer can no longer be leased.
* "status" is the status of the offer. There are three valid statuses for an offer:
  * available: an offer can be leased. This is the state of an offer on creation.
  * expired: an offer is no longer available for leasing. When an offer's end_time has passed, it's status is set to "expired".
  * deleted: an offer is no longer available for leasing. An offer is set to deleted when it is manually revoked by a user before its end_time has passed.
* "properties" is the baremetal properties of an offer.
* "availabilities" is a list of [start, end] datetime pairings representing a continuous time range in which an offer is available for leasing.
   * "availabilities" is not kept in the schema and is computed when retrieving an offer. 
* "created_at", "updated_at", and "id" are only used in the schema and cannot be read or set.


### Lease
Users can choose available nodes offered up and make leases to lease nodes. A lease example is shown below:
```
    {
        'id': 27,
        'uuid': '534653c9-880d-4c2d-6d6d-f4f2a09e384',
        'name': 'c1',
        'project_id': '01d4e6a72f5c408813e02f664cc8c83e',
        'start_time': '3030-07-08T00:00:00',
        'fulfill_time': '3030-07-08T00:15:00',
        'end_time': '4030-07-08T00:00:00',
        'expire_time': '4030-07-08T00:10:00',
        'status': statuses.OPEN,
        'properties': {},
        'offer_uuid': '534653c9-880d-4c2d-6d6d-f4f2a09e384',
        'created_at': None,
        'updated_at': None
    }
```
The lease data model is designed to support the following basic APIs:
* Get a lease by lease_uuid.
* Get lease(s) with filters: [project_id, status, start_time, end_time, offer_uuid, owner].
* List an offer's relevant leases.
* Create a new lease with given values.
* Update a lease's fields. Such as update the status to 'active' or 'expired', etc.
* Delete a lease by lease_uuid.

The lifecycle of a lease is
* 'created' on lease creation.
* 'active' once a lease's start_time has passed and its end_time has not yet passed.
* 'expired' once a lease's end_time has passed.
* 'cancelled' if a lease is prematurely deleted.

The lease API endpoint can be reached at /v1/leases.

An example lease response is shown below.

```
{
    "uuid": "ea5edb74-cafa-4281-913c-0a9fc66309d5",
    "name": "c1",
    "project_id": "a78d93273b134c2fadf208a3e8c2da04",
    "start_time": "3030-07-08T00:00:00",
    "fulfill_time": "3030-07-08T00:15:00",
    "end_time": "4030-07-08T00:00:00",
    "expire_time": "4030-07-08T00:10:00",
    "status": "open",
    "properties": {},
    "offer_uuid": "c02c686e-e248-490e-9ba1-fdf9531d5d37"
}
```

A lease response has the following fields:
* "uuid" is the primary key for a lease entry.
* "name" is an identifier the user may set for a lease on creation. Can be used for offer management instead of 'uuid'. Does not have to be unique.
* "project_id" is the project_id of the owner of the lease and the that is leasing the offer.
* "start_time" is a datetime representing the time in which the offer is being leased.
* "fulfill_time" is a datetime representing the time in which the lease is set to active and the user gains access to the node.
* "end_time" is a datetime representing the time in which the offer is no longer being leased.
* "expire_time" is a datetime representing the time in which the lessee no longer has access to the resource.
* "status" is the status of the lease. There are three valid statuses for a lease.
  * open: a lease is set. This is the state of a lease on creation.
  * fulfilled: a user has leased the offer. When a lease's end_time has passed, it's status is set to "fulfilled".
  * cancelled: a lease is no longer valid. A lease is set to cancelled when it is manually revoked by a user before its end_time has passed.
* "properties" is the baremetal properties of a lease.
* "offer_uuid" is the uuid of the offer which the lease is leased against.
* "created_at", "updated_at", and "id" are only used in the schema and cannot be read or set.



### Manager Service
An ESI-Leap manager has periodic jobs to manage offers and leases. 
* expire offers: out-of-date offers, i.e, the current timestamp > offer's end_time, will be updated with an 'EXPIRED' status.
* fulfill leases: if a lease's start_time <= the current timestamp and is not expired, the manager service will fulfill the resources in the leases and update the status of the leases to 'active'. 
* expire leases: same as 'expire offers', ESI-Leap will expire leases based on timestamp.
* update offers: after the manager fulfills and expires leases, it will update the relevant offers' status. The offers in a fulfilled lease should be unavailable to others. Likewise, when a lease expires, offers in the lease should be updated and be available again. 

## Reporting API
ESI-Leap admin queries this API to learn about the usage of nodes given a period. The admin enters a date range to get all leases' information within that range. The results could be like this:
```
    [
        {
        'lease_uuid':'634653c9-880d-4c2d-6d6d-f4f2a09e384',
        'project_id': '01d4e6a72f5c408813e02f664cc8c83e',
        'offer_uuid': '534653c9-880d-4c2d-6d6d-f4f2a09e384',
        'resource_uuid': '1718',
        'resource_type': 'ironic_node',
        'start_time': "3030-07-08T00:00:00",
        'fulfill_time': "3030-07-08T00:15:00",
        'end_time': "4030-07-08T00:00:00",
        'expire_time': "4030-07-08T00:10:00",
        'status': statuses.OPEN,
        'created_at': None,
        'updated_at': None
        },
        {
        'lease_uuid':...,
        ...
        }
    ]
```
With the leases and nodes information, the admin can inform owners about the status of the node and who leases their nodes during a date range.
