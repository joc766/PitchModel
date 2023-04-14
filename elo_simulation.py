from prediction_model import EloModel
from db_utils import create_session_scope


if __name__ == "__main__":
    with create_session_scope() as session:
        model = EloModel(session)
        model.train(suppress_output=False)