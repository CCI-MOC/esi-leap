## Offer API

The Offer API endpoint can be reached at /v1/offers.

##### GET
* The /v1/offers/\<uuid_or_name> endpoint is used to retrieve the offer with the given uuid. The response type is 'application/json'.
* The /v1/offers endpoint is used to retrieve a list of offers. This URL supports several URL variables for retrieving offers filtered by given values. The response type is 'application/json'.
  * project_id: Returns all offers with given project_id.
  * status: Returns all offers with given status. 
    * This value will default to returning offers with status 'available'.
    * This value can be set to 'any' to return offers without filtering by status.
  * resource_uuid: Returns all offers with given resource_uuid.
  * resource_type: Returns all offers with given resource_type
  * start_time and end_time: Passing in values for the start_time and end_time variables will return all offers with a start_time and end_time which completely span the given values. These two URL variables must be used together. Passing in only one will throw an error. 
  * available_start_time and available_end_time: Passing in values for the available_start_time and available_end_time variables will return all offers with availabilities which completely span the given values. These two URL variables must be used together. Passing in only one will throw an error.


##### POST
* The /v1/offers endpoint supports POST requests for offer creation with values passed through the body.
  * resource_type:
    * A string.
    * This field is required.
  * resource_uuid: the uuid of the resource. If using with Ironic this would be the node's uuid.
    * A string.
    * This field is required.
  * start_time:
    * A datetime string.
    * This field is optional. Not setting it will default start_time to the time when the request was sent.
  * end_time:
    * A datetime string.
    * This field is optional. Not setting it will default end_time to datetime.max.
  * properties:
    * a json object
    * This field is optional. Not setting it will default to {}.
* 'status', 'uuid', and 'availabilities' are read only. 
* The response to a POST request will be the newly created offer. The response type is 'application/json'.
    
An example curl request is shown below.
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

##### DELETE
* The /v1/offers/\<uuid> endpoint supports DELETE requests for offer cancellation.
* Offers will have their "status" set to 'cancelled'.
* All leases on this offer will also have their "status" set to 'cancelled'.
* Returns null on success.


## Lease API

The lease api endpoint can be reached at /v1/leases


##### GET
* The /v1/leases/\<uuid_or_name> endpoint is used to retrieve the lease with the given uuid. The response type is 'application/json'.
* The /v1/leases endpoint is used to retrieve a list of leases. This URL supports several URL variables for retrieving offers filtered by given values. The response type is 'application/json'.
  * project_id: Returns all leases with given project_id.
    * This value will default to the project_id of the request.
  * status: Returns all offers with given status. 
    * This value will default to returning leases with status 'open'.
    * This value can be set to 'any' to return leases without filtering by status.
  * start_time and end_time: Passing in values for the start_time and end_time variables will return all leases with a start_time and end_time which completely span the given values. These two URL variables must be used together. Passing in only one will throw an error. 
  * owner: Returns all leases which are related to offers with project_id 'owner'.
  * view: Setting view to 'all' will return all leases in the database. This value can be used in combination with other filters.

##### POST
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
  * offer_uuid_or_name:
    * A string.
    * This field is required.
* 'status' and 'uuid' are read only. 
* The response to a POST request will be the newly created lease. The response type is 'application/json'.

An example curl request is shown below.
```
curl -X POST -sH "X-Auth-Token: $token" http://localhost:7777/v1/leases  -H 'Content-Type: application/json' -d '{
  "start_time": "2020-04-07 05:45:02",
  "end_time": "2020-04-09 05:45:02",
  "name": "c1",
  "properties": {},
  "offer_uuid_or_name": "0efa7486-b3df-4b4c-bc94-9fbbba88a6a5"
}' | python -m json.tool

```

##### DELETE
* The /v1/leases/\<uuid> endpoint supports DELETE requests for lease cancellation.
* Leases will have their "status" set to 'cancelled'.
* Cancelling a lease does not affect any other leases. The related offer will have its availabilities updated to reflect the newly freed time range.
* Returns null on success.
