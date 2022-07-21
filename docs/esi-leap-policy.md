## Policy
ESI-Leap uses [oslo.policy](https://docs.openstack.org/oslo.policy/latest/index.html) to define three rules which limit API endpoints:

### is_admin
By default, the is_admin policy is given to any OpenStack user with the role 'admin' or 'esi_leap_admin'.

##### Offer
* GET: an admin can view any offer. The admin has access to all GET filters.
* POST: an admin can post offers.
  * offers can be created with any resource_uuid.
* DELETE: an admin can cancel offers on behalf of any user.

##### Lease
* GET: an admin can view any lease with the /v1/leases/\<uuid> endpoint. The admin has access to all GET filters.
  * 'owner' can be set to any value.
  * 'project_id' can be set to any value.
  * 'view' variable to 'all'.
* POST: an admin can post leases.
* DELETE: an admin can cancel any lease with the /v1/leases/\<uuid> endpoint.

### is_owner
By default, the is_owner policy is given to any OpenStack user with the role 'owner' or 'esi_leap_owner'.


##### Offer
* GET: an owner can view any offer. The owner has access to all GET filters.
* POST: an owner can post offers with restrictions.
  * offers must be created with the user's own project_id.
  * The resource corresponding to resource_uuid must have project_owner_id = the user's project_id.
* DELETE: an owner can cancel any offer they own. IE, the offer's project_id = user's project_id and the resource's project_owner_id = user's project_id.

##### Lease
* GET: an owner can view any lease which is related to an offer owned by the owner or any lease owned by the owner. The owner has restricted access to the GET filters.
  * 'owner' must be set to the user's project_id.
    * The default behavior of GET is to retrieve leases owned. Not using this variable will return all leases owned, and because an owner may not create leases, will thus be an empty list.
  * 'project_id' can be set to any value if used with the 'owner' variable. If used without the 'owner' variable, project_id must equal user's project_id.
  * 'view' variable is not allowed to be set.
* POST: an owner cannot post leases.
* DELETE: an owner can cancel any lease tied to an offer which is owned by the user.


### is_lessee

By default, the is_lessee policy is given to any OpenStack user with the role 'lessee' or 'esi_leap_lessee'.


##### Offer
* GET: a lessee can view any offer. The lessee has access to all GET filters.
* POST: a lessee cannot create an offer.
* DELETE: a lessee cannot delete an offer.

##### Lease
* GET: a lessee can view any lease which is related to an offer owned by the lessee or any lease owned by the lessee. The lessee has restricted access to the GET filters.
  * 'owner' must be set to the user's project_id.
    * The default behavior of GET is to retrieve leases owned. Not using this variable will return all leases owned by the lessee.
  * 'project_id' can be set to any value if used with the 'owner' variable. If used without the 'owner' variable, project_id must equal user's project_id.
  * 'view' variable is not allowed to be set.
* POST: a lessee can create leases.
* DELETE: a lessee can cancel any lease they own.


The default policies are listed below.
```
default_policies = [
    policy.RuleDefault('is_admin',
                       'role:admin or role:esi_leap_admin',
                       description='Full read/write API access'),
    policy.RuleDefault('is_owner',
                       'role:owner or role:esi_leap_owner',
                       description='Owner API access'),
    policy.RuleDefault('is_lessee',
                       'role:lessee or role:esi_leap_lessee',
                       description='Lessee API access'),
]

lease_policies = [
    policy.DocumentedRuleDefault(
        'esi_leap:lease:lease_admin',
        'rule:is_admin',
        'Complete permissions over leases',
        [{'path': '/leases', 'method': 'POST'},
         {'path': '/leases', 'method': 'GET'},
         {'path': '/leases/{lease_ident}', 'method': 'GET'},
         {'path': '/leases/{lease_ident}', 'method': 'DELETE'}]),
    policy.DocumentedRuleDefault(
        'esi_leap:lease:create',
        'rule:is_admin or rule:is_owner',
        'Create lease',
        [{'path': '/leases', 'method': 'POST'}]),
    policy.DocumentedRuleDefault(
        'esi_leap:lease:get',
        'rule:is_admin or rule:is_lessee or rule:is_owner',
        'Retrieve all leases owned by project_id',
        [{'path': '/leases', 'method': 'GET'},
         {'path': '/leases/{lease_ident}', 'method': 'GET'}]),
    policy.DocumentedRuleDefault(
        'esi_leap:lease:delete',
        'rule:is_admin or rule:is_owner or rule:is_lessee',
        'Delete lease',
        [{'path': '/leases/{lease_ident}', 'method': 'DELETE'}]),
]

offer_policies = [
    policy.DocumentedRuleDefault(
        'esi_leap:offer:offer_admin',
        'rule:is_admin',
        'Complete permissions over offers',
        [{'path': '/offers', 'method': 'POST'},
         {'path': '/offers', 'method': 'GET'},
         {'path': '/offers/{offer_ident}', 'method': 'GET'},
         {'path': '/offers/{offer_ident}', 'method': 'DELETE'}]),
    policy.DocumentedRuleDefault(
        'esi_leap:offer:create',
        'rule:is_admin or rule:is_owner',
        'Create offer',
        [{'path': '/offers', 'method': 'POST'}]),
    policy.DocumentedRuleDefault(
        'esi_leap:offer:get',
        'rule:is_admin or rule:is_owner or rule:is_lessee',
        'Retrieve offer',
        [{'path': '/offers', 'method': 'GET'},
         {'path': '/offers/{offer_ident}', 'method': 'GET'}]),
    policy.DocumentedRuleDefault(
        'esi_leap:offer:delete',
        'rule:is_admin or rule:is_owner',
        'Delete offer',
        [{'path': '/offers/{offer_ident}', 'method': 'DELETE'}]),
    policy.DocumentedRuleDefault(
        'esi_leap:offer:claim',
        'rule:is_admin or rule:is_lessee',
        'Claim an offer',
        [{'path': '/offers/{offer_ident}/claim', 'method': 'POST'}]),
]

```
