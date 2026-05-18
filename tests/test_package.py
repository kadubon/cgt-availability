from cgt_availability import ClaimPackage, FrameSpec


def test_claim_package_json_roundtrip() -> None:
    pkg = ClaimPackage(
        claim_id="roundtrip",
        statement="Roundtrip package.",
        frame=FrameSpec(id="frame", metadata={"dimension": "finite"}),
    )
    restored = ClaimPackage.from_json(pkg.to_json())
    assert restored.claim_id == pkg.claim_id
    assert restored.frame is not None
    assert restored.frame.metadata["dimension"] == "finite"


def test_declared_component_names_include_declared_specs() -> None:
    pkg = ClaimPackage(claim_id="x", statement="x", frame=FrameSpec(id="frame"))
    assert pkg.declared_component_names() == ("frame",)
