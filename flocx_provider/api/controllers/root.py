from pecan import expose
import json

from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client

from pecan import request
from pecan import response
from flocx_provider.db import api as db_api



class RootController(object):

    @expose()
    def _default(self):
        return "root"


    def returnoffersget(self):
        example = [
                    {
                    "Offerid": 100,
                    "Nodeid": "Node_100",
                    "Status": "enum - | Waiting | Published | InContract | Expired",
                    "TimeStamp": 2
                    }
                    ]

        return example

    def return_response_to_user(self, offer_id, message):
        return {
                    "offer_id": offer_id,
                    "status": message
        }


    def get_ironic_config_from_ironic(self, node_id):
        return 'Some Config'

    def get_ironic_config(self, node_id):
        con = db_api.Connection()
        conf = con.get_ironic_config(node_id)
        if conf is not None:
            print('In function get_ironic_conf', conf.config)
            return conf.config
        else:
            print ('Didnt find config, grab them from ironic')
            config = self.get_ironic_config_from_ironic(node_id)
            con = db_api.Connection()
            con.add_ironic_config(node_id, config)
            return config

    @expose("json")
    @expose(generic=True)
    def offers(self, **kwargs):

        resp = self.returnoffersget()
        response.status = 200
        return resp

    @expose("json")
    @offers.when(method='POST')
    def offers_POST(self, **kwargs):

        # 1. we parse POST request and get
        # node_id
        # start_time
        # end_time
        # price
        # duration
        # 2. create a provider offer_id and put the offer in DB
        # 3. we respond the user with provider offer_id and success
        # 4. Check if ironic config already exists in DB otherwise get them
        # 5. Make a post request to markete place.
        # 6. In case you receive the sucess message you should receive a marketplace offer id also update the DB.

        if 'node_id' in kwargs:
            node_id = kwargs.get('node_id')
        else:
            print("bad node_id")
            return -1

        if 'start_time' in kwargs:
            start_time = kwargs.get('start_time')
        else:
            print("bad start_time")
            return -1

        if 'end_time' in kwargs:
            end_time = kwargs.get('end_time')
        else:
            print("bad end_time")
            return -1

        if 'price' in kwargs:
            price = kwargs.get('price')
        else:
            print("bad price")
            return -1

        if 'duration' in kwargs:
            duration = kwargs.get('duration')
        else:
            print("bad duration")
            return -1

        con = db_api.Connection()
        offer_id = con.add_offer(node_id, start_time, end_time, price, duration)

        ironic_config = self.get_ironic_config(node_id)  # even if it doesn't gave in DB it
        # will find and put in the db and return.

        print('Ironic config:', ironic_config)

        auth = v3.Password(auth_url='http://localhost:5000/v3',
                           username='admin',
                           password='qwerty123',
                           project_name='admin',
                           user_domain_id='default',
                           project_domain_id='default')

        # Get a session object. You can use a session to make authenticated requests.
        sess = session.Session(auth=auth)
        ks = client.Client(session=sess, interface='public')



        """
        service_id = ks.services.list(type='marketplace')[0].id
        endpoints = ks.endpoints.list(service=service_id, interface='internal')


        auth = v3.Password(auth_url='http://localhost:5000/v3',
                           username='marketplace-user',
                           password='qwerty123',
                           project_name='marketplace-project',
                           user_domain_id='default',
                           project_domain_id='default')

        # Get a session object. You can use a session to make authenticated requests.
        sess = session.Session(auth=auth)
        print()
        print(kwargs)
        res = sess.post(endpoints[0].url+"/offerspost", data=kwargs).content
        
        #return res
        """

        response.status = 200
        return self.return_response_to_user(offer_id, 'Status is waiting')