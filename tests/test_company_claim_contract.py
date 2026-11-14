# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

import pytest

from patchwork_os.hub_spoke_gate import (
    DEFAULT_LEASE_KEY,
    generate_lease_token,
    verify_lease_token,
)
from patchwork_os.llm_wiki import audit_itar_and_obsidian_hygiene
from patchwork_os.runtime_dispatch import (
    COMPLIANCE_REGIME_CATALOG,
    RUNTIME_HARNESS_CAPABILITIES,
    plan_inter_runtime_synthesis,
    resolve_extensible_compliance_routing,
)
from patchwork_os.setup_init import build_agnostic_setup_questionnaire


FIELDS = dict(task_id="sample", role="COMPOSER", agent_id="fixture", diff_hash="diff-a")
TEST_SECRET = b"fixture-only-explicit-secret-not-for-production"


def test_secret_is_required_for_generation_and_verification():
    with pytest.raises(TypeError):
        generate_lease_token(**FIELDS)
    with pytest.raises(TypeError):
        verify_lease_token("not-a-token", **FIELDS)


@pytest.mark.parametrize("secret", [b"", DEFAULT_LEASE_KEY])
def test_empty_and_public_default_keys_are_refused(secret):
    with pytest.raises(ValueError, match="secret required"):
        generate_lease_token(**FIELDS, secret=secret)
    with pytest.raises(ValueError, match="secret required"):
        verify_lease_token("not-a-token", **FIELDS, secret=secret)


def test_explicit_secret_positive_and_binding_negatives():
    token = generate_lease_token(**FIELDS, secret=TEST_SECRET)
    assert verify_lease_token(token, **FIELDS, secret=TEST_SECRET)
    assert not verify_lease_token(token, **FIELDS, secret=b"another-fixture-only-secret")
    changed = dict(FIELDS, diff_hash="diff-b")
    assert not verify_lease_token(token, **changed, secret=TEST_SECRET)


def test_local_trace_scan_never_claims_itar_or_airgap(tmp_path: Path):
    clean = audit_itar_and_obsidian_hygiene(tmp_path)
    assert clean["obsidian_traces_absent"] is True
    assert clean["zero_obsidian_dependency"] is True
    assert clean["deprecated_aliases"]["zero_obsidian_dependency"] == "obsidian_traces_absent"
    assert "itar_airgap_plain_markdown_ready" not in clean
    assert clean["itar_assessment"] == clean["airgap_assessment"] == "not_run"
    (tmp_path / ".obsidian").mkdir()
    dirty = audit_itar_and_obsidian_hygiene(tmp_path)
    assert dirty["obsidian_traces_absent"] is False
    assert dirty["zero_obsidian_dependency"] is False
    assert dirty["obsidian_dirs"] == [".obsidian"]
    assert dirty["itar_assessment"] == dirty["airgap_assessment"] == "not_run"


@pytest.mark.parametrize("regime", tuple(COMPLIANCE_REGIME_CATALOG))
def test_every_example_filter_keeps_unverified_status_through_projection(regime):
    source = COMPLIANCE_REGIME_CATALOG[regime]
    assert source["verification"] == "unverified_example"
    assert source["compliance_assessed"] is False
    assert all(item["verification"] == "unverified_example"
               for bucket in source["tier_models"].values() for item in bucket)
    assert all(item["verification"] == "unverified_example"
               for item in RUNTIME_HARNESS_CAPABILITIES.values())
    settings = dict(compliance_regime=regime)
    routed = resolve_extensible_compliance_routing(manual_kwargs=settings)
    assert routed["verification"] == "unverified_example"
    assert routed["compliance_assessed"] is False
    assert routed["itar_ear_restricted"] == source["itar_ear_restricted"]
    assert routed["rank_1_primary"]["verification"] == "unverified_example"
    assert routed["rank_2_counterpart"]["verification"] == "unverified_example"
    plan = plan_inter_runtime_synthesis(
        task_id="sample", goal="nonsensitive example", parent_session_id="fixture",
        manual_kwargs=settings,
    )
    assert plan["verification"] == "unverified_example"
    assert plan["compliance_assessed"] is False
    assert plan["execution_supported"] is False
    assert plan["runtime_acceptance"] == "not_run"
    assert all(leg["verification"] == "unverified_example" for leg in plan["legs"])
    assert plan["legs"][0]["model"] == routed["rank_1_primary"]["model"]
    assert plan["legs"][1]["model"] == routed["rank_2_counterpart"]["model"]


def test_questionnaire_does_not_turn_example_labels_into_approval():
    questionnaire = build_agnostic_setup_questionnaire()
    assert questionnaire["verification"] == "unverified_example"
    assert questionnaire["compliance_assessed"] is False
    question = next(q for q in questionnaire["questions"] if q["id"] == "compliance_regime")
    assert question["verification"] == "unverified_example"
    assert question["compliance_assessed"] is False
    assert len(question["options"]) == 6
