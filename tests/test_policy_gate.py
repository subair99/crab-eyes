from types import SimpleNamespace as F

from app.gate.policy import GateInput, decide

T = {"min_verified_sources": 2, "min_independent_red_flags": 2,
     "maths": {"max_plausible_annual_return": 1.0, "benchmark_multiple": 3.0}}


def red(key, official=False, entity="n/a", check="voices", verified=True):
    return F(check=check, kind="red_flag", summary=f"red {key}", official=official, independence_key=key,
             entity_match=entity, details_match=None, verified=verified)


def verdict(findings, maths=False):
    v, _ = decide(GateInput(findings=findings, maths_failed=maths, thresholds=T))
    return getattr(v, "value", v)


def test_high_risk_needs_official_confirmed_source():
    assert verdict([red("sec.gov.ng", official=True, entity="confirmed", check="regulator"), red("news.ng")]) == "high_risk"


def test_uncertain_entity_does_not_count_as_official():
    assert verdict([red("sec.gov.ng", official=True, entity="uncertain", check="regulator"), red("news.ng")]) == "check_first"


def test_maths_plus_one_red_flag_is_high_risk():
    maths = red("calculator", check="ponzi_maths")
    assert verdict([maths, red("forum.ng")], maths=True) == "high_risk"


def test_maths_alone_is_check_first():
    assert verdict([red("calculator", check="ponzi_maths")], maths=True) == "check_first"


def test_confirmed_register_match_looks_legitimate():
    reg = F(check="regulator", kind="register_match", summary="On SEC register", official=True,
            independence_key="sec.gov.ng", entity_match="confirmed", details_match=True, verified=True)
    assert verdict([reg]) == "looks_legitimate"


def test_register_match_with_wrong_details_is_not_legitimate():
    reg = F(check="regulator", kind="register_match", summary="Similar name on register", official=True,
            independence_key="sec.gov.ng", entity_match="confirmed", details_match=False, verified=True)
    assert verdict([reg]) == "not_enough_evidence"


def test_unverified_findings_are_ignored():
    assert verdict([red("a", verified=False), red("b", verified=False)]) == "not_enough_evidence"


def test_same_source_twice_is_not_independent():
    v = verdict([red("sec.gov.ng", official=True, entity="confirmed", check="regulator"),
                 red("sec.gov.ng", official=True, entity="confirmed", check="regulator")])
    assert v != "high_risk"     
    assert v == "check_first"   