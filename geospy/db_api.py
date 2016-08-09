import os

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       'location.db')

_engine = sa.create_engine('sqlite:///{}'.format(DB_FILE))
Session = sessionmaker(bind=_engine)
_metadata = sa.schema.MetaData(_engine)

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
Base = declarative_base()


class Position(Base):
    # TODO(haim): rename to Positions
    __tablename__ = 'Positions'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    # TODO: switch to foreign key
    service_name = sa.Column(sa.VARCHAR)
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
        print (('{},' * 6).format(p.id, p.service_name, p.latitude,
                                  p.longitude, p.accuracy, p.timestamp))
