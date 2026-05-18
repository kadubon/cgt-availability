from conftest import make_complete_package

from cgt_availability import (
    AvailabilityAnalyzer,
    ClaimPackage,
    Deficiency,
    DependencyClosure,
    FrameSpec,
    availability_preorder,
)


def test_dependency_closure_is_idempotent() -> None:
    closure = DependencyClosure()
    deficiencies = (
        Deficiency(
            code="missing_projection",
            component="projection",
            severity="blocking",
            message="missing",
        ),
    )

    once = closure.close_ordered(deficiencies)
    twice = closure.close_ordered(once)

    assert once == twice


def test_dependency_closure_is_monotone_for_added_deficiencies() -> None:
    closure = DependencyClosure()
    smaller = (
        Deficiency(
            code="missing_projection",
            component="projection",
            severity="blocking",
            message="missing",
        ),
    )
    larger = (
        *smaller,
        Deficiency(
            code="missing_expected_report",
            component="expected_report",
            severity="blocking",
            message="missing",
        ),
    )

    smaller_codes = {item.code for item in closure.close_ordered(smaller)}
    larger_codes = {item.code for item in closure.close_ordered(larger)}

    assert smaller_codes <= larger_codes


def test_availability_preorder_is_reflexive_and_transitive_on_examples() -> None:
    bare = ClaimPackage("bare", "Bare claim.")
    framed = ClaimPackage("framed", "Framed claim.", frame=FrameSpec(id="frame"))
    complete = make_complete_package()
    analyzer = AvailabilityAnalyzer.default()

    assert availability_preorder(bare, bare, analyzer=analyzer)
    assert availability_preorder(complete, complete, analyzer=analyzer)
    assert availability_preorder(bare, framed, analyzer=analyzer)
    assert availability_preorder(framed, complete, analyzer=analyzer)
    assert availability_preorder(bare, complete, analyzer=analyzer)
