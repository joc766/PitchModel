from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload, Session
from models import engine, Game, Play

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

def get_all_games(session: Session = None, training: bool = True):
    with create_session_scope(session) as session:
        games = (
            session.query(Game)
            .options(joinedload(Game.plays))
            .filter(Game.training == True)
            .order_by(Game.date)
            .all()
        )

    return games

def get_all_plays(session: Session = None, training: bool = True):
    with create_session_scope(session) as session:
        games = get_all_games(session, training=training)
        plays = [play for game in games for play in game.plays]

    return plays