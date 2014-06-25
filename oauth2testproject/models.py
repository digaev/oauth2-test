import hashlib
import random
import time
import datetime
import json

from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text,
    UnicodeText,
    String,
    DateTime
    )

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


class UserSession(Base):
    __tablename__ = 'sessions'

    id = Column(Integer, primary_key=True)

    # Cookie & OAuth2 state, random hash (for user identification)
    session_id = Column(String(32), unique=True, index=True, nullable=False)
    # Service id, such as google+, github, etc...
    service_id = Column(String(255)) 
    # OAuth2 session creation time
    oauth2_created_at = Column(DateTime)
    # OAuth2 session expired time
    oauth2_expired_in = Column(DateTime)
    # JSON, response to CODE request
    oauth2_data = Column(UnicodeText)
    # JSON
    user_info = Column(UnicodeText)
    # Record creation time
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def __init__(self):
        self.session_id = hashlib.md5(str(time.time()).encode() + str(random.random()).encode()).hexdigest()

    def oauth2_init(self, service, data):
        self.service_id = service
        self.oauth2_created_at = datetime.datetime.utcnow()
        self.oauth2_data = data
        return True

    def oauth2_clear(self):
        self.service_id = None
        self.oauth2_created_at = None
        self.oauth2_expired_in = None
        self.oauth2_data = None
        return True

    def oauth2_data_json(self):
        return json.loads(self.oauth2_data)

    def user_info_json(self):
        return json.loads(self.user_info)

    @staticmethod
    def find_by_sid(sid):
        return DBSession.query(UserSession).filter_by(session_id = sid).first()
