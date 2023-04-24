from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload, Session
from models import engine, Game, Play, Position, Pitcher, Batter

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

def get_all_games(session: Session, training: bool = True):
    games = (
        session.query(Game)
        .options(joinedload(Game.plays))
        .filter(Game.training == True)
        .order_by(Game.date)
        .all()
    )

    return games

def get_all_plays(session: Session, training: bool = True) -> list[Play]:
    games = get_all_games(session, training=training)
    plays = [play for game in games for play in game.plays]

    return plays


def get_n_plays(id: int, position: Position, session: Session):
    if position == Position.PITCHER:
        n_plays = (
            session.query(Pitcher)
            .filter(Pitcher.playerId == id)
            .first()
            .n_plays
        )
    elif position == Position.BATTER:
        n_plays = (
            session.query(Batter)
            .filter(Batter.playerId == id)
            .first()
            .n_plays
        )
    try:
        return n_plays
    except UnboundLocalError:
        raise Exception(
            f"Position must be either {Position.PITCHER} or {Position.BATTER}"
        )