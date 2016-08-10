import os

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       'location.db')

_engine = sa.create_engine('sqlite:///{}'.format(DB_FILE))
Session = sessionmaker(bind=_engine)
_metadata = sa.schema.MetaData(_engine)

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
Base = declarative_base()


class Service(Base):
    __tablename__ = 'services'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    name = sa.Column(sa.VARCHAR)


class Position(Base):
    __tablename__ = 'positions'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    service_id = sa.Column(sa.Integer, sa.ForeignKey("services.id"))
    service = relationship("Service", foreign_keys=[service_id])

    latitude = sa.Column(sa.FLOAT)
    longitude = sa.Column(sa.FLOAT)
    accuracy = sa.Column(sa.FLOAT)

    timestamp = sa.Column(sa.DateTime(timezone=True),
                          default=sa.func.now())


Base.metadata.create_all(_engine)


# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
def purge_db():
    _metadata.reflect()
    _metadata.drop_all()


def db_to_csv(session):
    for p in session.query(Position).all():
        print (('{},' * 6).format(p.id, p.service.name, p.latitude,
                                  p.longitude, p.accuracy, p.timestamp))
