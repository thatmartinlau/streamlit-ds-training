"""Pandas code challenges with output checking against a reference solution.

A challenge is a small snippet of pandas code. We run the reference on a fresh
copy of the Titanic dataframe, run the user's code the same way, and compare
their *output* (DataFrame / Series / scalar / sequence).
"""

from __future__ import annotations

import ast
import builtins
import numbers
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

PANDAS_QUESTIONS_DIR = (
    Path(__file__).resolve().parent.parent / "pandas_questions"
)


# --------------------------------------------------------------------------- #
#  Challenge model & loading
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class PandasChallenge:
    id: str
    title: str
    difficulty: str
    prompt: str
    reference_code: str
    hint: str = ""
    ordered: bool = False


def _parse_bool(v) -> bool:
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in {"true", "1", "yes", "y", "t"}


def load_challenges(
    directory: Path = PANDAS_QUESTIONS_DIR,
) -> tuple[list[PandasChallenge], list[dict]]:
    """Load every ``*.csv`` in ``directory`` and merge into one bank."""
    challenges: list[PandasChallenge] = []
    errors: list[dict] = []
    if not directory.exists():
        return challenges, errors

    seen: set[str] = set()
    required = {"id", "title", "difficulty", "prompt", "reference_code"}

    for path in sorted(directory.glob("*.csv")):
        try:
            df = pd.read_csv(path)
        except Exception as exc:  # noqa: BLE001
            errors.append({"file": path.name, "error": str(exc)})
            continue

        missing = required - set(df.columns)
        if missing:
            errors.append(
                {"file": path.name, "error": f"missing column(s): {sorted(missing)}"}
            )
            continue

        if "hint" not in df.columns:
            df["hint"] = ""
        if "ordered" not in df.columns:
            df["ordered"] = False

        for _, row in df.iterrows():
            cid = str(row["id"]).strip()
            if not cid or cid in seen:
                errors.append({"file": path.name, "error": f"bad/duplicate id {cid!r}"})
                continue
            seen.add(cid)
            hint_val = row.get("hint", "")
            hint = "" if pd.isna(hint_val) else str(hint_val).strip()
            challenges.append(
                PandasChallenge(
                    id=cid,
                    title=str(row["title"]).strip(),
                    difficulty=str(row["difficulty"]).strip().lower(),
                    prompt=str(row["prompt"]).strip(),
                    reference_code=str(row["reference_code"]).strip(),
                    hint=hint,
                    ordered=_parse_bool(row.get("ordered", False)),
                )
            )

    return challenges, errors


# --------------------------------------------------------------------------- #
#  Safe-ish execution
# --------------------------------------------------------------------------- #
_BLOCKED_BUILTINS = {
    "__import__", "eval", "exec", "compile", "open", "input",
    "breakpoint", "exit", "quit", "globals", "locals", "vars",
}


def _safe_builtins() -> dict:
    return {k: v for k, v in vars(builtins).items() if k not in _BLOCKED_BUILTINS}


def _exec_and_get_last(code: str, namespace: dict):
    """Execute ``code``; return the value of its final expression."""
    tree = ast.parse(code.strip())
    if not tree.body:
        return None

    last = tree.body[-1]
    result_var = None
    if isinstance(last, ast.Expr):
        result_var = "__result__"
        tree.body[-1] = ast.Assign(
            targets=[ast.Name(id=result_var, ctx=ast.Store())],
            value=last.value,
        )
        ast.fix_missing_locations(tree)

    compiled = compile(tree, filename="<pandas-user>", mode="exec")
    exec(compiled, namespace)
    return namespace.get(result_var) if result_var else None


# --------------------------------------------------------------------------- #
#  Output comparison
# --------------------------------------------------------------------------- #
@dataclass
class CheckOutcome:
    ok: bool
    reason: str  # ok | syntax | error | type | columns | shape | content | order
    message: str
    user_output: object = None
    ref_output: object = None
    missing: list | None = None
    extra: list | None = None


def _norm_value(v):
    if v is None:
        return None
    if isinstance(v, (bool, str, bytes)):
        return v
    if isinstance(v, numbers.Real):
        try:
            if pd.isna(v):
                return None
        except (TypeError, ValueError):
            pass
        return round(float(v), 4)
    if isinstance(v, pd.Timestamp):
        return v.isoformat()
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    return v


def _records(df: pd.DataFrame) -> list:
    return [
        tuple(_norm_value(v) for v in row)
        for row in df.itertuples(index=False, name=None)
    ]


def _compare_dataframes(
    user: pd.DataFrame, ref: pd.DataFrame, ordered: bool
) -> CheckOutcome:
    if set(map(str, user.columns)) != set(map(str, ref.columns)):
        return CheckOutcome(
            False, "columns",
            f"Expected columns {list(ref.columns)}, got {list(user.columns)}.",
            user, ref,
        )

    user = user[list(ref.columns)]  # align column order
    if user.shape != ref.shape:
        return CheckOutcome(
            False, "shape",
            f"Expected shape {ref.shape}, got {user.shape}.", user, ref,
        )

    u_rows = _records(user)
    r_rows = _records(ref)

    if ordered:
        if u_rows == r_rows:
            return CheckOutcome(True, "ok", "Correct.", user, ref)
    else:
        if Counter(u_rows) == Counter(r_rows):
            return CheckOutcome(True, "ok", "Correct.", user, ref)

    c_u, c_r = Counter(u_rows), Counter(r_rows)
    missing = list((c_r - c_u).elements())
    extra = list((c_u - c_r).elements())
    if not missing and not extra:
        reason, msg = "order", "All the right rows, but in a different order."
    else:
        reason, msg = "content", "The output doesn't match the expected result."
    return CheckOutcome(False, reason, msg, user, ref, missing=missing, extra=extra)


def _compare_series(user: pd.Series, ref: pd.Series, ordered: bool) -> CheckOutcome:
    if len(user) != len(ref):
        return CheckOutcome(
            False, "shape",
            f"Expected length {len(ref)}, got {len(user)}.", user, ref,
        )
    u_pairs = [(str(k), _norm_value(v)) for k, v in user.items()]
    r_pairs = [(str(k), _norm_value(v)) for k, v in ref.items()]
    if ordered:
        if u_pairs == r_pairs:
            return CheckOutcome(True, "ok", "Correct.", user, ref)
    else:
        if Counter(u_pairs) == Counter(r_pairs):
            return CheckOutcome(True, "ok", "Correct.", user, ref)
    return CheckOutcome(False, "content", "Values don't match.", user, ref)


def _compare_sequence(user, ref) -> CheckOutcome:
    if isinstance(user, str):
        return CheckOutcome(False, "type", "Expected a sequence, got a string.", user, ref)
    try:
        u = list(user)
    except TypeError:
        return CheckOutcome(
            False, "type", f"Expected a sequence, got a {type(user).__name__}.", user, ref
        )
    if len(u) != len(ref):
        return CheckOutcome(
            False, "shape", f"Expected {len(ref)} items, got {len(u)}.", user, ref
        )
    for a, b in zip(u, ref):
        if _norm_value(a) != _norm_value(b):
            return CheckOutcome(False, "content", f"Expected {ref!r}, got {user!r}.", user, ref)
    return CheckOutcome(True, "ok", "Correct.", user, ref)


def _compare_scalar(user, ref) -> CheckOutcome:
    u, r = _norm_value(user), _norm_value(ref)
    if u == r:
        return CheckOutcome(True, "ok", "Correct.", user, ref)
    if isinstance(u, float) and isinstance(r, float) and abs(u - r) < 1e-4:
        return CheckOutcome(True, "ok", "Correct.", user, ref)
    return CheckOutcome(False, "content", f"Expected {ref!r}, got {user!r}.", user, ref)


def _compare_outputs(user, ref, ordered: bool) -> CheckOutcome:
    if isinstance(ref, pd.DataFrame):
        if not isinstance(user, pd.DataFrame):
            return CheckOutcome(
                False, "type", f"Expected a DataFrame, got a {type(user).__name__}.", user, ref
            )
        return _compare_dataframes(user, ref, ordered)
    if isinstance(ref, pd.Series):
        if not isinstance(user, pd.Series):
            return CheckOutcome(
                False, "type", f"Expected a Series, got a {type(user).__name__}.", user, ref
            )
        return _compare_series(user, ref, ordered)
    if isinstance(ref, (list, tuple)):
        return _compare_sequence(user, ref)
    return _compare_scalar(user, ref)


# --------------------------------------------------------------------------- #
#  Public entry point
# --------------------------------------------------------------------------- #
def evaluate(challenge: PandasChallenge, user_code: str, df: pd.DataFrame) -> CheckOutcome:
    if not user_code.strip():
        return CheckOutcome(False, "syntax", "Write some pandas code first.")

    try:
        ref_output = _exec_and_get_last(
            challenge.reference_code, {"df": df.copy(), "pd": pd}
        )
    except Exception as exc:  # noqa: BLE001
        return CheckOutcome(False, "reference", f"Reference code failed: {exc}")

    ns = {"df": df.copy(), "pd": pd, "__builtins__": _safe_builtins()}
    try:
        user_output = _exec_and_get_last(user_code, ns)
    except SyntaxError as exc:
        return CheckOutcome(
            False, "syntax",
            f"Syntax error: `{exc.msg}` (line {exc.lineno}).",
        )
    except Exception as exc:  # noqa: BLE001
        return CheckOutcome(
            False, "error", f"Your code raised `{type(exc).__name__}: {exc}`."
        )

    if user_output is None:
        return CheckOutcome(
            False, "error",
            "Your code didn't produce a value. End with an **expression** "
            "(e.g. `df.head()`, not `x = df.head()`).",
            ref_output=ref_output,
        )

    return _compare_outputs(user_output, ref_output, challenge.ordered)