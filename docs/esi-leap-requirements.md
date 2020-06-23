# ESI Leap Requirements

## Overview
ESI Leap is a leasing service for bare metal. Ironic nodes owners can offer up their nodes to other users, while lesees can view offers and create a contract for available nodes.

## Definitions

### Offer
Ironic owners can bring up their nodes to ESI Leap with an offer. An offer consists of the resource uuid, leasing period, and the status, etc. Here is an example offer schema:
```
    {
        'id': 27,
        'uuid': '534653c9-880d-4c2d-6d6d-f4f2a09e384',
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
* Get offer(s) with filters: [status, project_id, resource_uuid].
* Create a new offer with given values.
* Update an offer's fields. Such as update the status to 'AVAILABLE' or 'EXPIRED', etc.
* Delete an offer by offer_uuid.
Based on the aboving APIs, ESI Leap can provide various of functionalities for users. A leese can retrieve offers with their requirements and find the suitable offer(s). An owner can check their offers' status and make changes.


### Contract
Users can choose available nodes offered up and make contracts to lease nodes. A contract example is shown below:
```
    {
        'id': 27,
        'uuid': '534653c9-880d-4c2d-6d6d-f4f2a09e384',
        'project_id': '01d4e6a72f5c408813e02f664cc8c83e',
        'start_time': datetime.datetime(2016, 7, 16, 19, 20, 30),
        'end_time': datetime.datetime(2016, 7, 16, 19, 20, 30),
        'status': statuses.OPEN,
        'properties': {},
        'offer_uuid': '534653c9-880d-4c2d-6d6d-f4f2a09e384',
        'created_at': None,
        'updated_at': None
    }
```
The contract data model is designed to support the following basic APIs:
* Get a contract by contract_uuid.
* Get contract(s) with filters: [project_id, status, offer_uuid].
* List a contract's relevant offers.
* Create a new contract with given values.
* Update a contract's fields. Such as update the status to 'OPEN' or 'FULFILLED', etc.
* Delete a contract by contract_uuid.


### Manager Service
An ESI Leap manager has periodic jobs to manage offers and contracts. 
* expire offers: out-of-date offers, i.e, the current timestamp > offer's end_time, will be updated with an 'EXPIRED' status.
* fulfill contracts: if a contract's start_time <= the current timestamp and is not expired, the manager service will fulfill the resources in the contracts and update the status of the contracts to 'FULFILLED'. 
* expire contracts: same as 'expire offers', ESI Leap will expire contracts based on timestamp.
* update offers: after the manager fulfills and expires contracts, it will update the relevant offers' status. The offers in a fulfilled contract should be unavailable to others. Likewise, when a contract expires, offers in the contract should be updated and be available again. 

## Reporting API
ESI Leap admin queries this API to learn about the usage of nodes given a period. The admin enters a date range to get all contracts' information within that range. The results could be like this:
```
    [
        {
        'contract_uuid':'634653c9-880d-4c2d-6d6d-f4f2a09e384',
        'project_id': '01d4e6a72f5c408813e02f664cc8c83e',
        'offer_uuid': '534653c9-880d-4c2d-6d6d-f4f2a09e384',
        'resource_uuid': '1718',
        'resource_type': 'ironic_node',
        'start_time': datetime.datetime(2016, 7, 16, 19, 20, 30),
        'end_time': datetime.datetime(2016, 7, 16, 19, 20, 30),
        'status': statuses.OPEN,
        'created_at': None,
        'updated_at': None
        },
        {
        'contract_uuid':...,
        ...
        }
    ]
```
With the contracts and nodes information, admin can inform owners about the status of the node and who leases their nodes during a date range.