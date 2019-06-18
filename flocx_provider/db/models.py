
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext import declarative
from sqlalchemy import Index


#
# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy import Column, Integer, String
# from sqlalchemy.orm import sessionmaker
# Base = declarative_base()
# engine = create_engine('mysql+pymysql://flocx_provider:qwerty123@127.0.0.1/flocx_provider')
# Session = sessionmaker(bind=engine)
# session = Session()



Base = declarative.declarative_base()

class Offers(Base):
    __tablename__ = 'provider_offers'
    offer_id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(Integer)
    start_time = Column(String(50))
    duration = Column(String(50))
    end_time = Column(String(50))
    price = Column(Integer)
    ironic_config = Column(String(2000))
    status = Column(Integer)


class ironic_config(Base):
    __tablename__ = 'ironic_config'
    node_id = Column(Integer, primary_key=True)
    config = Column(String(50))





# Base.metadata.create_all(engine)