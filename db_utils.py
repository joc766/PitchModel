from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import engine

@contextmanager
def create_session_scope(existing_session=None):
    if existing_session:
        yield existing_session
    else:
        session = sessionmaker(bind=engine)()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()