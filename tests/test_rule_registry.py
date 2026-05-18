from cgt_availability import ClaimPackage, CoherenceRulePack, FunctionRule
from cgt_availability.core.deficiency import make_deficiency


def test_function_rule_adapts_existing_check() -> None:
    rule = FunctionRule("test.required", lambda _pkg: (make_deficiency("missing_frame"),))

    result = rule.evaluate(ClaimPackage("x", "x"))

    assert result.deficiencies[0].code == "missing_frame"


def test_coherence_rule_pack_exposes_distinct_named_rules() -> None:
    rules = CoherenceRulePack.default().as_rules()

    assert len({rule.name for rule in rules}) == len(rules)
    assert "coherence.verifier_failure" in {rule.name for rule in rules}
    assert "coherence.reproduction_protocol" in {rule.name for rule in rules}
