
from sqlalchemy import create_engine
import sqlalchemy.orm
from sqlalchemy.orm import exc
import sqlalchemy as db
from flocx_provider.db import models as db_models


class Connection(object):

    _ENGINE = None
    _SESSION_MAKER = None

    def __init__(self):
        session = self.get_session()
        query = session.query(db_models.Offers)
        query.all()
        return

    def get_session(self):

        if self._ENGINE is not None:
            engine = self._ENGINE
        else:
            self._ENGINE = db.create_engine('mysql+pymysql://flocx_provider:qwerty123@127.0.0.1/flocx_provider', echo=False)
            engine = self._ENGINE

        if self._SESSION_MAKER is not None:
            maker = self._SESSION_MAKER
        else:
            self._SESSION_MAKER = sqlalchemy.orm.sessionmaker(bind=engine)
            maker = self._SESSION_MAKER

        session = maker()
        return session

    def add_offer(self, node_id, start_time, end_time, duration, price):
        offer = db_models.Offers(
                      node_id=node_id,
                      start_time=start_time,
                      end_time=end_time,
                      duration=duration,
                      price=price,
                      ironic_config='xx',
                      status=0)
        s = self.get_session()
        s.add(offer)
        s.commit()
        return offer.offer_id

    def get_ironic_config(self, node_id):
        s = self.get_session()
        return s.query(db_models.ironic_config).filter_by(node_id=node_id).first()

    def add_ironic_config(self, node_id, config):
        ic = db_models.ironic_config(
            node_id=node_id,
            config=config)
        s = self.get_session()
        s.add(ic)
        s.commit()
        return True
