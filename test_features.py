import pandas as pd
import pytest

from features import build_model_frame


def make_transactions(*rows):
    defaults = {"transaction_id": 1, "account_id": 1, "amount_usd": 100, "failed_logins_24h": 0}
    return pd.DataFrame([{**defaults, **r} for r in rows])


def make_accounts(*rows):
    defaults = {"account_id": 1, "prior_chargebacks": 0}
    data = rows if rows else [{}]
    return pd.DataFrame([{**defaults, **r} for r in data])


# ---------------------------------------------------------------------------
# Join correctness
# ---------------------------------------------------------------------------

def test_account_fields_joined_to_transactions():
    txns = make_transactions({"account_id": 1})
    accts = make_accounts({"account_id": 1, "prior_chargebacks": 3})
    result = build_model_frame(txns, accts)
    assert result.loc[0, "prior_chargebacks"] == 3


def test_left_join_keeps_all_transactions():
    # A transaction with no matching account should still appear (NaN account fields).
    txns = make_transactions({"account_id": 99})
    accts = make_accounts({"account_id": 1})
    result = build_model_frame(txns, accts)
    assert len(result) == 1


def test_multiple_transactions_same_account():
    txns = make_transactions({"transaction_id": 1, "account_id": 1}, {"transaction_id": 2, "account_id": 1})
    accts = make_accounts({"account_id": 1, "prior_chargebacks": 2})
    result = build_model_frame(txns, accts)
    assert len(result) == 2
    assert (result["prior_chargebacks"] == 2).all()


# ---------------------------------------------------------------------------
# is_large_amount flag
# ---------------------------------------------------------------------------

def test_is_large_amount_below_threshold():
    txns = make_transactions({"amount_usd": 999})
    result = build_model_frame(txns, make_accounts())
    assert result.loc[0, "is_large_amount"] == 0


def test_is_large_amount_at_threshold():
    txns = make_transactions({"amount_usd": 1000})
    result = build_model_frame(txns, make_accounts())
    assert result.loc[0, "is_large_amount"] == 1


def test_is_large_amount_above_threshold():
    txns = make_transactions({"amount_usd": 2500})
    result = build_model_frame(txns, make_accounts())
    assert result.loc[0, "is_large_amount"] == 1
