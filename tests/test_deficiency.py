from cgt_availability import DEFICIENCY_CODE_INFO, STABLE_DEFICIENCY_CODES
from cgt_availability.core.deficiency import Deficiency, make_deficiency


def test_deficiency_json_roundtrip() -> None:
    deficiency = make_deficiency("missing_projection", metadata={"reason": "test"})
    restored = Deficiency.from_json(deficiency.to_json())
    assert restored == deficiency


def test_deficiency_is_hashable() -> None:
    deficiency = make_deficiency("missing_verifier")
    assert deficiency in {deficiency}


def test_deficiency_code_registry_has_group_and_rationale() -> None:
    assert tuple(DEFICIENCY_CODE_INFO) == STABLE_DEFICIENCY_CODES
    assert all(item.group for item in DEFICIENCY_CODE_INFO.values())
    assert all(item.rationale for item in DEFICIENCY_CODE_INFO.values())
