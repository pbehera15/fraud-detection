import pandas as pd

from analyze_fraud import score_transactions, summarize_results


def make_transactions():
    return pd.DataFrame([
        {
            "transaction_id": 1, "account_id": 10,
            "amount_usd": 1500, "device_risk_score": 80,
            "is_international": 1, "velocity_24h": 8, "failed_logins_24h": 6,
        },
        {
            "transaction_id": 2, "account_id": 20,
            "amount_usd": 30, "device_risk_score": 5,
            "is_international": 0, "velocity_24h": 1, "failed_logins_24h": 0,
        },
    ])


def make_accounts():
    return pd.DataFrame([
        {"account_id": 10, "prior_chargebacks": 1},
        {"account_id": 20, "prior_chargebacks": 0},
    ])


# ---------------------------------------------------------------------------
# score_transactions pipeline
# ---------------------------------------------------------------------------

def test_score_transactions_produces_risk_score_column():
    scored = score_transactions(make_transactions(), make_accounts())
    assert "risk_score" in scored.columns


def test_score_transactions_produces_risk_label_column():
    scored = score_transactions(make_transactions(), make_accounts())
    assert "risk_label" in scored.columns


def test_high_risk_transaction_labeled_high():
    scored = score_transactions(make_transactions(), make_accounts())
    row = scored[scored["transaction_id"] == 1].iloc[0]
    assert row["risk_label"] == "high"


def test_clean_transaction_labeled_low():
    scored = score_transactions(make_transactions(), make_accounts())
    row = scored[scored["transaction_id"] == 2].iloc[0]
    assert row["risk_label"] == "low"


def test_all_transactions_are_scored():
    scored = score_transactions(make_transactions(), make_accounts())
    assert len(scored) == 2


# ---------------------------------------------------------------------------
# summarize_results
# ---------------------------------------------------------------------------

def _scored_with_one_chargeback():
    scored = score_transactions(make_transactions(), make_accounts())
    chargebacks = pd.DataFrame([{"transaction_id": 1}])
    return scored, chargebacks


def test_summarize_results_counts_chargebacks_in_high_bucket():
    scored, chargebacks = _scored_with_one_chargeback()
    summary = summarize_results(scored, chargebacks)
    high = summary[summary["risk_label"] == "high"].iloc[0]
    assert high["chargebacks"] == 1


def test_summarize_results_chargeback_rate_is_1_for_high_bucket():
    scored, chargebacks = _scored_with_one_chargeback()
    summary = summarize_results(scored, chargebacks)
    high = summary[summary["risk_label"] == "high"].iloc[0]
    assert high["chargeback_rate"] == 1.0


def test_summarize_results_zero_chargebacks_in_low_bucket():
    scored, chargebacks = _scored_with_one_chargeback()
    summary = summarize_results(scored, chargebacks)
    low = summary[summary["risk_label"] == "low"].iloc[0]
    assert low["chargebacks"] == 0
    assert low["chargeback_rate"] == 0.0


def test_summarize_results_transaction_counts_are_correct():
    scored, chargebacks = _scored_with_one_chargeback()
    summary = summarize_results(scored, chargebacks)
    assert summary["transactions"].sum() == 2


def test_summarize_results_no_chargebacks_produces_zero_rate():
    scored = score_transactions(make_transactions(), make_accounts())
    chargebacks = pd.DataFrame([{"transaction_id": 999}])  # no match
    summary = summarize_results(scored, chargebacks)
    assert (summary["chargebacks"] == 0).all()
    assert (summary["chargeback_rate"] == 0.0).all()
