from dataclasses import replace

from conftest import make_complete_package

from cgt_availability import AvailabilityAnalyzer, MarkerPolicySpec, MarkerStateSpec


def test_marker_state_can_supply_marker_provenance_and_preservation() -> None:
    pkg = replace(
        make_complete_package(),
        marker_policy=MarkerPolicySpec(id="policy", tracks_unresolved=True),
        marker_state=MarkerStateSpec(
            id="state",
            unresolved_markers=("source-conflict",),
            marker_provenance=("lab-a",),
            preserves_markers=True,
        ),
        metadata={"marker_sensitive": True},
    )

    report = AvailabilityAnalyzer.default().analyze(pkg)

    assert "missing_marker_provenance" not in {
        item.code for item in report.dependency_closed_deficiencies
    }
    assert "marker_policy_incomplete" not in {
        item.code for item in report.dependency_closed_deficiencies
    }


def test_marker_state_roundtrip_on_claim_package() -> None:
    pkg = make_complete_package(marker_state=MarkerStateSpec(id="state", unresolved_markers=("m",)))

    roundtrip = type(pkg).from_dict(pkg.to_dict())

    assert roundtrip.marker_state is not None
    assert roundtrip.marker_state.unresolved_markers == ("m",)
