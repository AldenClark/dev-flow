#!/usr/bin/env python3
"""Deterministic interaction projections; not native capability or model execution."""

from __future__ import annotations

import unittest

from evals.run_contract_checks import evaluate_user_interaction_case


class InteractionEligibilityTests(unittest.TestCase):
    def scenario(self, **changes: object) -> dict[str, object]:
        # These fields model a fixture, never a host capability-detection API.
        case: dict[str, object] = {
            "kind": "eligibility",
            "purpose": "required-decision",
            "tool_exposed": True,
            "current_mode": "Default",
            "allowed_modes": ["Default"],
            "allowed_purposes": ["required-decision", "optional-clarification"],
            "schema_fits": True,
            "lifecycle_supported": True,
            "transport": "sync",
            "input_surface": "ordinary-question",
            "protected_input": False,
        }
        return case | changes

    def test_eligible_sync_and_async_surfaces(self) -> None:
        for transport in ("sync", "async"):
            with self.subTest(transport=transport):
                self.assertEqual(
                    evaluate_user_interaction_case(self.scenario(transport=transport)),
                    f"native-{transport}",
                )

    def test_exposed_plan_only_tool_is_ineligible_in_default(self) -> None:
        case = self.scenario(allowed_modes=["Plan"])
        self.assertEqual(evaluate_user_interaction_case(case), "conversation-required")

    def test_optional_only_tool_cannot_carry_a_required_decision(self) -> None:
        optional_only = {"allowed_purposes": ["optional-clarification"]}
        self.assertEqual(
            evaluate_user_interaction_case(self.scenario(**optional_only)),
            "conversation-required",
        )
        self.assertEqual(
            evaluate_user_interaction_case(self.scenario(purpose="optional-clarification", **optional_only)),
            "native-sync",
        )

    def test_each_capability_check_can_disqualify_an_exposed_tool(self) -> None:
        negative_controls = (
            {"tool_exposed": False},
            {"schema_fits": False},
            {"lifecycle_supported": False},
            {"allowed_purposes": []},
            {"transport": "unobserved"},
        )
        for change in negative_controls:
            with self.subTest(change=change):
                self.assertEqual(
                    evaluate_user_interaction_case(self.scenario(**change)),
                    "conversation-required",
                )

    def test_optional_fallback_remains_optional(self) -> None:
        self.assertEqual(
            evaluate_user_interaction_case(self.scenario(purpose="optional-clarification", tool_exposed=False)),
            "conversation-optional",
        )

    def test_ordinary_question_never_substitutes_for_approval(self) -> None:
        case = self.scenario(purpose="approval", allowed_purposes=["approval"])
        self.assertEqual(evaluate_user_interaction_case(case), "approval-unavailable")
        self.assertEqual(
            evaluate_user_interaction_case(case | {"input_surface": "native-approval"}),
            "native-approval",
        )
        self.assertEqual(
            evaluate_user_interaction_case(case | {"allowed_purposes": ["optional-clarification"]}),
            "approval-unavailable",
        )

    def test_secret_requires_observed_protected_input_surface(self) -> None:
        case = self.scenario(purpose="secret", allowed_purposes=["secret"])
        self.assertEqual(evaluate_user_interaction_case(case), "blocked-secret")
        secure = case | {"input_surface": "secure-input", "protected_input": True}
        self.assertEqual(evaluate_user_interaction_case(secure), "secure-input")
        for change in ({"protected_input": False}, {"schema_fits": False}, {"allowed_modes": ["Plan"]}):
            with self.subTest(change=change):
                self.assertEqual(evaluate_user_interaction_case(secure | change), "blocked-secret")


class AsyncInteractionTests(unittest.TestCase):
    def test_successful_dispatch_and_pending_do_not_supply_an_answer(self) -> None:
        for event in ("dispatch-returned", "pending"):
            with self.subTest(event=event):
                case = {"kind": "async-lifecycle", "event": event, "tool_result": "success"}
                self.assertEqual(evaluate_user_interaction_case(case), "unresolved-pending")

    def test_received_answer_keeps_response_validation(self) -> None:
        case = {
            "kind": "async-lifecycle",
            "event": "answer-received",
            "question_id": "retention",
            "expected_question_id": "retention",
            "options": ["retain", "delete"],
            "other_enabled": False,
            "answers": ["retain"],
            "requirement_revision": 2,
            "current_requirement_revision": 2,
        }
        self.assertEqual(evaluate_user_interaction_case(case), "accepted-option")
        negative_controls = (
            ({"requirement_revision": 1}, "ignored-stale-or-unknown"),
            ({"answers": []}, "unresolved-invalid"),
            ({"answers": ["retain", "delete"]}, "unresolved-invalid"),
            ({"question_id": "old-question"}, "ignored-stale-or-unknown"),
        )
        for change, expected in negative_controls:
            with self.subTest(change=change):
                self.assertEqual(evaluate_user_interaction_case(case | change), expected)


if __name__ == "__main__":
    unittest.main()
