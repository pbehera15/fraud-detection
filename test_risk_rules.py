from risk_rules import label_risk, score_transaction


# Minimal transaction with no risk signals — used as a base for isolation tests.
BASE_TX = {
    "device_risk_score": 0,
    "is_international": 0,
    "amount_usd": 0,
    "velocity_24h": 0,
    "failed_logins_24h": 0,
    "prior_chargebacks": 0,
}


# ---------------------------------------------------------------------------
# label_risk
# ---------------------------------------------------------------------------

def test_label_risk_thresholds():
    assert label_risk(10) == "low"
    assert label_risk(35) == "medium"
    assert label_risk(75) == "high"


def test_label_risk_exact_boundaries():
    assert label_risk(29) == "low"
    assert label_risk(30) == "medium"
    assert label_risk(59) == "medium"
    assert label_risk(60) == "high"


# ---------------------------------------------------------------------------
# score_transaction — device risk signal
# ---------------------------------------------------------------------------

def test_high_risk_device_adds_risk():
    tx = {**BASE_TX, "device_risk_score": 85}
    assert score_transaction(tx) == 25


def test_mid_risk_device_adds_risk():
    tx = {**BASE_TX, "device_risk_score": 55}
    assert score_transaction(tx) == 10


def test_low_risk_device_adds_no_risk():
    tx = {**BASE_TX, "device_risk_score": 20}
    assert score_transaction(tx) == 0


# ---------------------------------------------------------------------------
# score_transaction — international signal
# ---------------------------------------------------------------------------

def test_international_transaction_adds_risk():
    tx = {**BASE_TX, "is_international": 1}
    assert score_transaction(tx) == 15


def test_domestic_transaction_adds_no_risk():
    tx = {**BASE_TX, "is_international": 0}
    assert score_transaction(tx) == 0


# ---------------------------------------------------------------------------
# score_transaction — amount signal
# ---------------------------------------------------------------------------

def test_large_amount_adds_risk():
    tx = {
        "device_risk_score": 10,
        "is_international": 0,
        "amount_usd": 1200,
        "velocity_24h": 1,
        "failed_logins_24h": 0,
        "prior_chargebacks": 0,
    }
    assert score_transaction(tx) >= 25


def test_large_amount_adds_25():
    tx = {**BASE_TX, "amount_usd": 1200}
    assert score_transaction(tx) == 25


def test_medium_amount_adds_10():
    tx = {**BASE_TX, "amount_usd": 750}
    assert score_transaction(tx) == 10


def test_small_amount_adds_no_risk():
    tx = {**BASE_TX, "amount_usd": 100}
    assert score_transaction(tx) == 0


# ---------------------------------------------------------------------------
# score_transaction — velocity signal
# ---------------------------------------------------------------------------

def test_high_velocity_adds_risk():
    tx = {**BASE_TX, "velocity_24h": 8}
    assert score_transaction(tx) == 20


def test_mid_velocity_adds_risk():
    tx = {**BASE_TX, "velocity_24h": 4}
    assert score_transaction(tx) == 5


def test_low_velocity_adds_no_risk():
    tx = {**BASE_TX, "velocity_24h": 2}
    assert score_transaction(tx) == 0


# ---------------------------------------------------------------------------
# score_transaction — failed logins signal
# ---------------------------------------------------------------------------

def test_many_failed_logins_adds_risk():
    tx = {**BASE_TX, "failed_logins_24h": 6}
    assert score_transaction(tx) == 20


def test_some_failed_logins_adds_risk():
    tx = {**BASE_TX, "failed_logins_24h": 3}
    assert score_transaction(tx) == 10


def test_no_failed_logins_adds_no_risk():
    tx = {**BASE_TX, "failed_logins_24h": 0}
    assert score_transaction(tx) == 0


# ---------------------------------------------------------------------------
# score_transaction — prior chargeback history signal
# ---------------------------------------------------------------------------

def test_multiple_prior_chargebacks_adds_risk():
    tx = {**BASE_TX, "prior_chargebacks": 3}
    assert score_transaction(tx) == 20


def test_one_prior_chargeback_adds_risk():
    tx = {**BASE_TX, "prior_chargebacks": 1}
    assert score_transaction(tx) == 5


def test_no_prior_chargebacks_adds_no_risk():
    tx = {**BASE_TX, "prior_chargebacks": 0}
    assert score_transaction(tx) == 0


# ---------------------------------------------------------------------------
# score_transaction — score clamping
# ---------------------------------------------------------------------------

def test_score_never_negative():
    assert score_transaction(BASE_TX) == 0


def test_score_clamped_at_100():
    tx = {
        "device_risk_score": 85,
        "is_international": 1,
        "amount_usd": 1500,
        "velocity_24h": 8,
        "failed_logins_24h": 7,
        "prior_chargebacks": 3,
    }
    assert score_transaction(tx) == 100


# ---------------------------------------------------------------------------
# End-to-end label scenarios
# ---------------------------------------------------------------------------

def test_all_high_risk_signals_labeled_high():
    # Profile matching confirmed chargeback tx 50011 ($1400, Russia, device 85).
    tx = {
        "device_risk_score": 85,
        "is_international": 1,
        "amount_usd": 1400,
        "velocity_24h": 8,
        "failed_logins_24h": 7,
        "prior_chargebacks": 1,
    }
    assert label_risk(score_transaction(tx)) == "high"


def test_clean_transaction_labeled_low():
    # Profile matching low-risk tx 50001 ($45 grocery, US, device 8).
    tx = {
        "device_risk_score": 8,
        "is_international": 0,
        "amount_usd": 45,
        "velocity_24h": 1,
        "failed_logins_24h": 0,
        "prior_chargebacks": 0,
    }
    assert label_risk(score_transaction(tx)) == "low"
