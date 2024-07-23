## Offer API

The Offer API endpoint can be reached at /v1/offers.

##### GET /v1/offers/\<uuid_or_name> - Show Offer Details
* The /v1/offers/\<uuid_or_name> endpoint is used to retrieve the offer with the given uuid. The response type is 'application/json'.


##### GET /v1/offers - List Offers
* The /v1/offers endpoint is used to retrieve a list of offers. This URL supports several URL variables for retrieving offers filtered by given values. The response type is 'application/json'.
  * project_id: Returns all offers with given project_id.
  * status: Returns all offers with given status.
    * This value will default to returning offers with status 'available'.
    * This value can be set to 'any' to return offers without filtering by status.
  * resource_uuid: Returns all offers with given resource_uuid.
  * resource_type: Returns all offers with given resource_type.
    * This value will default to returning offers with resource_type 'ironic_node'.
  * resource_class: Returns all offers with given resource_class.
  * start_time and end_time: Passing in values for the start_time and end_time variables will return all offers with a start_time and end_time which completely span the given values. These two URL variables must be used together. Passing in only one will throw an error.
  * available_start_time and available_end_time: Passing in values for the available_start_time and available_end_time variables will return all offers with availabilities which completely span the given values. These two URL variables must be used together. Passing in only one will throw an error.


##### POST /v1/offers - Create Offer
* The /v1/offers endpoint supports POST requests for offer creation with values passed through the body.
  * resource_uuid: the uuid of the resource. If using with Ironic this would be the node's uuid.
    * A string.
    * This field is required.
  * resource_type:
    * A string.
    * This field is optional. Not setting it will default to 'ironic_node'.
  * name:
    * A string.
    * This field is optional.
  * lessee_id:
    * A string.
    * This field is optional.
  * resource_class:
    * A string.
    * This field is optional.
  * resource_properties:
    * A JSON object.
    * This field is optional.
  * start_time:
    * A datetime string.
    * This field is optional. Not setting it will default start_time to the time when the request was sent.
  * end_time:
    * A datetime string.
    * This field is optional. Not setting it will default end_time to datetime.max.
  * properties:
    * A JSON object.
    * This field is optional. Not setting it will default to {}.
  * 'status', 'uuid', 'availabilities', 'project_id', 'project', 'lessee', resource', and 'parent_lease_uuid' are read only.
  * The response to a POST request will be the newly created offer. The response type is 'application/json'.

  * An example curl request is shown below.
    ```
    curl -X POST -sH "X-Auth-Token: $token" http://localhost:7777/v1/offers  -H 'Content-Type: application/json' -d '{
      "resource_type": "dummy_node",
      "resource_uuid": "1718",
      "name": "o1",
      "start_time": "2020-04-07 05:45:02",
      "end_time": "2020-04-09 05:45:02",
      "properties": {
          "memory_gb": 10240,
          "cpu_arch": "x86_64",
          "cpu_physical_count": 4,
          "cpu_core_count": 16,
          "cpu_ghz": 3,
          "disks": [
            {
              "size_gb": 500,
              "model": "YOYODYNE 1234"
            },
        {
              "size_gb": 1024,
              "model": "evo840 ssd"
            }
          ]
        }
    }'
    ```


##### POST /v1/offers/\<uuid>/claim - Claim Offer
* The /v1/offers/\<uuid>/claim endpoint supports POST requests to claim the offer with the given uuid. The body of the request contains the lease information with the given values.
  * start_time:
    * A datetime string.
    * This field is optional. Not setting it will default start_time to the time when the request was sent.
  * end_time:
    * A datetime string.
    * This field is optional. Not setting it will default end_time to the end of the offer's first continuous availability range with a start greater than the given start_time.
  * name:
    * A string.
    * This field is optional.
  * The response to a POST request would be a newly updated lease. The response type is 'application/json'.

##### DELETE /v1/offers/\<uuid> - Delete Offer
* The /v1/offers/\<uuid> endpoint supports DELETE requests for offer cancellation.
* Offers will have their "status" set to 'cancelled'.
* All leases on this offer will also have their "status" set to 'cancelled'.
* Returns null on success.


## Lease API

The lease api endpoint can be reached at /v1/leases


##### GET /v1/leases/\<uuid_or_name> - Show Lease Details
* The /v1/leases/\<uuid_or_name> endpoint is used to retrieve the lease with the given uuid. The response type is 'application/json'.

##### GET /v1/leases - List Leases
* The /v1/leases endpoint is used to retrieve a list of leases. This URL supports several URL variables for retrieving offers filtered by given values. The response type is 'application/json'.
  * project_id: Returns all leases with given project_id.
    * This value will default to the project_id of the request.
  * status: Returns all offers with given status.
    * This value will default to returning leases with status 'open'.
    * This value can be set to 'any' to return leases without filtering by status.
  * start_time and end_time: Passing in values for the start_time and end_time variables will return all leases with a start_time and end_time which completely span the given values. These two URL variables must be used together. Passing in only one will throw an error.
  * owner_id: Returns all leases which are related to offers with project_id 'owner_id'.
  * view: Setting view to 'all' will return all leases in the database. This value can be used in combination with other filters.
  * offer_uuid: Returns all leases with given offer_uuid.
  * resource_type: Returns all leases with given resource_type.
    * This value will default to returning leases with resource_type 'ironic_node'.
  * resource_uuid: Returns all leases with given resource_uuid.
  * resource_class: Returns all leases with given resource_class.

##### POST /v1/leases - Create Lease
* The /v1/leases endpoint supports POST requests for lease creation with values passed through the body.
  * start_time:
    * A datetime string.
    * This field is optional. Not setting it will default start_time to the time when the request was sent.
  * end_time:
    * A datetime string.
    * This field is optional. Not setting it will default end_time to the end of the offer's first continuous availability range with a start greater than the given start_time.
  * properties:
    * a json object
    * This field is optional. Not setting it will default to {}.
  * name:
    * A string.
    * This field is optional.
  * project_id:
    * A string.
    * This field is optional.
  * resource_type:
    * A string.
    * This field is optional.
  * resource_uuid:
    * A string.
    * This field is optional.
  * resource_class:
    * A string.
    * This field is optional.
  * resource_properties:
    * A JSON object.
    * This field is optional.
  * purpose:
    * A string.
    * This field is optional.
  * 'status', 'uuid', 'project', 'owner_id', 'owner', 'resource', 'fulfill_time', 'expire_time', 'offer_uuid', and 'parent_lease_uuid'  are read only.
  * The response to a POST request will be the newly created lease. The response type is 'application/json'.

    An example curl request is shown below.
    ```
    curl -X POST -sH "X-Auth-Token: $token" http://localhost:7777/v1/leases  -H 'Content-Type: application/json' -d '{
      "start_time": "2020-04-07 05:45:02",
      "end_time": "2020-04-09 05:45:02",
      "name": "c1",
      "properties": {},
      "name": "0efa7486-b3df-4b4c-bc94-9fbbba88a6a5"
    }' | python -m json.tool

    ```

##### PATCH /v1/leases/\<uuid> - Update Lease
* The /v1/leases/\<uuid> endpoint supports PATCH requests to update the end time of the lease with the given uuid. The body takes in an object with only **one** property:
  * end_time:
    * A datetime string.
    * This field is required.
  * The response is the updated lease with the new end time. The response type is 'application/json'.

##### DELETE /v1/leases/\<uuid> - Delete Lease
* The /v1/leases/\<uuid> endpoint supports DELETE requests for lease cancellation.
* Leases will have their "status" set to 'cancelled'.
* Cancelling a lease does not affect any other leases. The related offer will have its availabilities updated to reflect the newly freed time range.
* Returns null on success.


## Node API

The node api endpoint can be reached at /v1/nodes


##### GET /v1/nodes - List Nodes
* The /v1/nodes endpoint is used to retrieve a list of nodes. This URL supports several URL variables for retrieving nodes filtered by given values. The response type is 'application/json'.
  * resource_class: Returns all nodes with given resource_class.
  * owner: Returns all nodes with given owner.
  * lessee: Returns all nodes with given lessee.


## Event API

The event api endpoint can be reached at /v1/events


##### GET /v1/events - List Events
* The /v1/events endpoint is used to retrieve a list of events. This URL supports several URL variables for retrieving events filtered by given values. The response type is 'application/json'.
  * last_event_id: Returns all events with given last_event_id.
  * lessee_or_owner_id: Returns all events with given lessee_or_owner_id.
  * last_event_time: Returns all events with given last_event_time.
  * event_type: Returns all events with given event_type.
  * resource_type: Returns all events with given resource_type.
    * This value will default to returning events with resouce_type 'ironic_node'
  * resource_uuid: Returns all events with given resource_uuid.
