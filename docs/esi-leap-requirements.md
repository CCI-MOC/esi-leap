# ESI Leap Requirements

## Overview
ESI Leap is a leasing service for bare metal. Ironic nodes owners can offer up their nodes to other users, while lesees can view offers and create a contract for available nodes.

## Definitions

### Offer
Ironic owners can bring up their nodes to ESI Leap with an offer. An offer consists of the resource uuid, leasing period, and the status, etc. An offer can be created, destroyed, saved, retrieved, and expired by ESI Leap. Here is an example offer schema:
```
    {
        'id': 27,
        'uuid': '534653c9-880d-4c2d-6d6d-f4f2a09e384',
        'project_id': '01d4e6a72f5c408813e02f664cc8c83e',
        'resource_type': 'ironic_node',
        'resource_uuid': '1718',
        'start_date': datetime.datetime(2016, 7, 16, 19, 20, 30),
        'end_date': datetime.datetime(2016, 8, 16, 19, 20, 30),
        'status': statuses.AVAILABLE,
        'properties': {},
        'created_at': None,
        'updated_at': None
    }
```

### Contract
Users can choose available nodes offered up and make contracts to lease nodes. A contract example is shown below:
```
    {
        'id': 27,
        'uuid': '534653c9-880d-4c2d-6d6d-f4f2a09e384',
        'project_id': '01d4e6a72f5c408813e02f664cc8c83e',
        'start_date': datetime.datetime(2016, 7, 16, 19, 20, 30),
        'end_date': datetime.datetime(2016, 7, 16, 19, 20, 30),
        'status': statuses.OPEN,
        'properties': {},
        'offer_uuid': '534653c9-880d-4c2d-6d6d-f4f2a09e384',
        'created_at': None,
        'updated_at': None
    }
```

### Manager Service
An ESI Lesp manager has periodic jobs to manage offers and contracts. 
* expire offers: out-of-date offers, i.e, the current timestamp > offer's end_date, will be updated with an 'EXPIRED' status.
* fulfill contracts: if a contract's start_date <= the current timestamp and is not expired, the manager service will fulfill the resources in the contracts and update the status of the contracts to 'FULFILLED'.
* expire contracts: same as 'expire offers', ESI Leap will expire contracts based on timestamp.
