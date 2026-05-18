from conftest import make_complete_package

from cgt_availability import (
    EffectProfileRecord,
    FactorizationWitness,
    direct_selector_witness,
    find_factorization_witness,
)


def test_finite_factorization_witness_detects_same_report_different_history() -> None:
    witness = find_factorization_witness(
        (
            EffectProfileRecord("structured", "z", "structured", {"history": "structured"}),
            EffectProfileRecord("direct", "z", "direct", {"history": "direct"}),
        ),
        dimension="history",
        diagnostic_name="history_sensitive_degeneracy",
    )

    assert isinstance(witness, FactorizationWitness)
    assert witness.left_id == "direct" or witness.right_id == "direct"
    assert witness.report == "z"


def test_finite_factorization_witness_returns_none_when_fibers_agree() -> None:
    witness = find_factorization_witness(
        (
            EffectProfileRecord("a", "z", "same"),
            EffectProfileRecord("b", "z", "same"),
        ),
        dimension="marker",
        diagnostic_name="marker_status",
    )

    assert witness is None


def test_direct_selector_witness_requires_absent_controls() -> None:
    witness = direct_selector_witness(
        make_complete_package(metadata={"direct_selector_regime": True})
    )

    assert witness is not None
    assert "selector_language" in witness.missing_controls
