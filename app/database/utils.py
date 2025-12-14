from collections.abc import Mapping
from contextlib import contextmanager
from typing import Literal, assert_never, cast, final
from sqlalchemy.exc import IntegrityError
import psycopg
from sqlalchemy.orm import InstrumentedAttribute


def extract_constraint_name(exc: IntegrityError) -> str | None:
    orig = cast(psycopg.errors.IntegrityError, exc.orig)
    try:
        return orig.diag.constraint_name
    except Exception:
        return None


def to_constraint_name(
    column: InstrumentedAttribute[object], c: Literal["ix", "uq", "ck", "fk"], /
):
    tablename = column.class_.__tablename__
    columnname = column.key
    match c:
        case "uq" | "ck" | "fk":
            return f"{tablename}_{columnname}_{c}"
        case "ix":
            return f"{columnname}_{c}"
        case _:
            assert_never(c)


def get_exc_detail(exc: IntegrityError) -> str | None:
    orig = cast(psycopg.errors.IntegrityError, exc.orig)
    try:
        return orig.diag.message_detail or orig.diag.message_primary
    except Exception:
        return None


type ConstraintTuple = tuple[
    InstrumentedAttribute[object], Literal["ix", "uq", "ck", "fk"]
]


@final
class DatabaseErrorTranslator:
    '''
    Usage:

    translate_db_error = DatabaseErrorTranslator(
        {
            "team_players_team_id_fk": TeamNotFound,
            (TeamPlayer.player_id, "fk"): PlayerNotFound,
        }
    )

    def create_team_player(...):
        """Raises PlayerNotFound or TeamNotFound"""

        with translate_db_error():
            session.execute(insert(TeamPlayer).values(...))
    '''

    def __init__(
        self,
        constraint_errors: Mapping[str | ConstraintTuple, type[Exception]],
    ) -> None:
        self.constraint_errors: dict[str, type[Exception]] = {}

        for const, error in constraint_errors.items():
            if not isinstance(const, str):
                const = to_constraint_name(const[0], const[1])
            self.constraint_errors[const] = error

    @contextmanager
    def __call__(self):
        try:
            yield
        except IntegrityError as e:
            constraint = extract_constraint_name(e)
            if constraint and constraint in self.constraint_errors:
                detail = get_exc_detail(e)
                raise self.constraint_errors[constraint](detail) from e
            raise
