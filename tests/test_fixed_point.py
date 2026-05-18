from cgt_availability import least_fixed_point


def test_least_fixed_point_converges_to_expected_closure() -> None:
    dependencies = {
        "missing_projection": ("missing_observation",),
        "missing_observation": ("missing_description",),
    }

    def operator(profile: frozenset[str]) -> tuple[str, ...]:
        return tuple(target for code in profile for target in dependencies.get(code, ()))

    result = least_fixed_point(("missing_projection",), operator)

    assert result.converged
    assert result.fixed_point == (
        "missing_description",
        "missing_observation",
        "missing_projection",
    )
    assert result.stabilization_step == 2


def test_least_fixed_point_is_extensive_and_idempotent() -> None:
    def operator(profile: frozenset[str]) -> frozenset[str]:
        if "a" in profile:
            return frozenset({"b"})
        return frozenset()

    once = least_fixed_point(("a",), operator)
    twice = least_fixed_point(once.fixed_point, operator)

    assert set(("a",)) <= set(once.fixed_point)
    assert once.fixed_point == twice.fixed_point


def test_least_fixed_point_can_stop_before_convergence() -> None:
    def operator(profile: frozenset[str]) -> tuple[str, ...]:
        if "a" in profile and "b" not in profile:
            return ("b",)
        if "b" in profile and "c" not in profile:
            return ("c",)
        return ()

    result = least_fixed_point(("a",), operator, max_steps=1)

    assert not result.converged
    assert result.fixed_point == ("a", "b")
    assert result.stabilization_step is None


def test_empty_initial_profile_stabilizes_deterministically() -> None:
    result = least_fixed_point((), lambda _profile: ())

    assert result.converged
    assert result.fixed_point == ()
    assert result.iterations == ((),)
    assert result.added_by_step == ((),)
