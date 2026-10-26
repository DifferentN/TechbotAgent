import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts" / "validate_port.py"
spec = importlib.util.spec_from_file_location("validate_port", SCRIPT)
port = importlib.util.module_from_spec(spec)
spec.loader.exec_module(port)


class MigrationGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.workspace = self.base / "coordinator"
        self.android = self.base / "android"
        self.ios = self.base / "ios"
        for root in (self.workspace, self.android, self.ios):
            root.mkdir()
        self.config = json.loads((SKILL / "assets/config.template.json").read_text())
        self.config.update(android_root=str(self.android), ios_root=str(self.ios))
        self.config["allowed_write_roots"] = [str(self.ios)]
        self.ir = json.loads((SKILL / "assets/ir.example.json").read_text())
        self.ir["source"]["root"] = str(self.android)
        self.ir["target"]["root"] = str(self.ios)
        self.design = json.loads((SKILL / "assets/design.example.json").read_text())
        self.design["source_ir_digest"] = port.document_digest(self.ir)

    def errors(self, stage="draft", design=True):
        return port.validate(
            self.config, self.workspace, self.ir,
            self.design if design else None, stage=stage,
        )

    def approve(self):
        self.ir["approval"] = {
            "status": "approved", "record": "synthetic test confirmation only",
            "digest": port.document_digest(self.ir),
        }
        self.design["source_ir_digest"] = port.document_digest(self.ir)
        self.design["approval"] = {
            "status": "approved", "record": "synthetic test confirmation only",
            "digest": port.document_digest(self.design),
        }

    def test_complete_draft_is_valid_without_approval(self):
        self.assertEqual([], self.errors())

    def test_ready_requires_user_confirmation_records(self):
        self.assertTrue(self.errors(stage="ready"))

    def test_complete_approved_android_to_ios_passes_ready(self):
        self.approve()
        self.assertEqual([], self.errors(stage="ready"))

    def test_complete_approved_ios_to_android_passes_ready(self):
        self.ir["direction"] = "ios-to-android"
        self.ir["source"], self.ir["target"] = self.ir["target"], self.ir["source"]
        self.config["allowed_write_roots"] = [str(self.android)]
        self.design["target_baseline"] = self.ir["target"]["baseline"]
        self.design["slices"][0]["files"] = ["src/ListScreen.kt"]
        self.approve()
        self.assertEqual([], self.errors(stage="ready"))

    def test_empty_root_is_rejected(self):
        self.config["android_root"] = ""
        self.assertTrue(self.errors())

    def test_missing_root_is_rejected(self):
        self.config["ios_root"] = str(self.base / "missing")
        self.assertTrue(self.errors())

    def test_same_roots_are_rejected(self):
        self.config["ios_root"] = str(self.android)
        self.assertTrue(self.errors())

    def test_nested_project_roots_are_rejected(self):
        child = self.android / "nested"
        child.mkdir()
        self.config["ios_root"] = str(child)
        self.assertTrue(self.errors())

    def test_symlink_alias_project_roots_are_rejected(self):
        link = self.base / "alias"
        link.symlink_to(self.android, target_is_directory=True)
        self.config["ios_root"] = str(link)
        self.assertTrue(self.errors())

    def test_artifacts_cannot_escape_workspace(self):
        self.config["artifact_root"] = "../outside"
        self.assertTrue(self.errors())

    def test_artifacts_cannot_overwrite_agent_configuration(self):
        self.config["artifact_root"] = ".codex/output"
        self.assertTrue(self.errors())

    def test_artifact_symlink_escape_is_rejected(self):
        (self.workspace / "porting").symlink_to(self.base, target_is_directory=True)
        self.assertTrue(self.errors())

    def test_unknown_configuration_fields_are_rejected(self):
        self.config["auto_approve"] = True
        self.assertTrue(self.errors())

    def test_ready_requires_target_write_allowlist(self):
        self.approve()
        self.config["allowed_write_roots"] = []
        self.assertTrue(self.errors(stage="ready"))

    def test_parent_directory_cannot_grant_target_write_access(self):
        self.config["allowed_write_roots"] = [str(self.base)]
        self.assertTrue(self.errors())

    def test_ir_root_must_match_direction_and_configuration(self):
        self.ir["source"]["root"] = str(self.ios)
        self.assertTrue(self.errors())

    def test_source_framework_must_match_source_platform(self):
        self.ir["source"]["ui_framework"] = "swiftui"
        self.assertTrue(self.errors())

    def test_required_behavior_field_cannot_be_omitted(self):
        del self.ir["contracts"][0]["lifecycle_rules"]
        self.assertTrue(self.errors())

    def test_unknown_schema_keywords_fail_closed(self):
        with self.assertRaises(ValueError):
            port.schema_errors({}, {"type": "object", "not": {}}, "test")

    def test_boolean_is_not_a_revision_integer(self):
        self.ir["revision"] = True
        self.assertTrue(self.errors())

    def test_duplicate_evidence_ids_are_rejected(self):
        self.ir["evidence"].append(copy.deepcopy(self.ir["evidence"][0]))
        self.assertTrue(self.errors())

    def test_missing_evidence_reference_is_rejected(self):
        self.ir["contracts"][0]["evidence_ids"] = ["E-missing"]
        self.assertTrue(self.errors())

    def test_verified_contract_requires_evidence(self):
        self.ir["contracts"][0]["evidence_ids"] = []
        self.assertTrue(self.errors())

    def test_transition_must_reference_existing_state(self):
        self.ir["contracts"][0]["transitions"][0]["to"] = "S-missing"
        self.assertTrue(self.errors())

    def test_acceptance_scenario_must_reference_existing_contract(self):
        self.ir["scenarios"][0]["contract_ids"] = ["C-missing"]
        self.assertTrue(self.errors())

    def test_every_contract_requires_acceptance_coverage(self):
        self.ir["scenarios"] = []
        self.assertTrue(self.errors())

    def test_changed_ir_invalidates_existing_approval_and_design(self):
        self.approve()
        self.ir["scope"]["included"].append("new behavior")
        self.assertTrue(self.errors(stage="ready"))

    def test_changed_design_invalidates_existing_approval(self):
        self.approve()
        self.design["ui_acceptance"].append("new visual threshold")
        self.assertTrue(self.errors(stage="ready"))

    def test_ready_rejects_empty_confirmation_record(self):
        self.approve()
        self.ir["approval"]["record"] = ""
        self.assertTrue(self.errors(stage="ready"))

    def test_ready_rejects_unresolved_high_risk_questions(self):
        self.ir["unknowns"].append({
            "id": "U-1", "contract_ids": ["C-list"], "severity": "high",
            "status": "open", "question": "SDK semantics unknown", "resolution": "",
        })
        self.approve()
        self.assertTrue(self.errors(stage="ready"))

    def test_unknown_contract_cannot_be_ready(self):
        self.ir["contracts"][0]["confidence"] = "unknown"
        self.approve()
        self.assertTrue(self.errors(stage="ready"))

    def test_design_must_cover_all_states_and_transitions(self):
        self.design["mappings"][0]["state_ids"] = []
        self.assertTrue(self.errors())

    def test_design_must_cover_all_acceptance_scenarios(self):
        self.design["mappings"][0]["scenario_ids"] = []
        self.assertTrue(self.errors())

    def test_non_strict_mapping_requires_visible_impact(self):
        self.design["mappings"][0]["equivalence"] = "native-substitute"
        self.design["mappings"][0]["user_impact"] = ""
        self.assertTrue(self.errors())

    def test_ready_rejects_partial_or_unsupported_mapping(self):
        self.design["mappings"][0]["equivalence"] = "partial"
        self.design["mappings"][0]["user_impact"] = "pagination missing"
        self.approve()
        self.assertTrue(self.errors(stage="ready"))

    def test_file_whitelist_rejects_parent_traversal(self):
        self.design["slices"][0]["files"] = ["../outside.swift"]
        self.assertTrue(self.errors())

    def test_file_whitelist_rejects_absolute_paths(self):
        self.design["slices"][0]["files"] = [str(self.base / "outside.swift")]
        self.assertTrue(self.errors())

    def test_file_whitelist_rejects_symlink_escape(self):
        (self.ios / "Sources").symlink_to(self.android, target_is_directory=True)
        self.assertTrue(self.errors())

    def test_function_slice_dependencies_cannot_cycle(self):
        self.design["slices"][0]["depends_on"] = [self.design["slices"][0]["id"]]
        self.assertTrue(self.errors())

    def test_digest_ignores_only_top_level_approval(self):
        original = port.document_digest(self.ir)
        self.ir["approval"]["record"] = "different record"
        self.assertEqual(original, port.document_digest(self.ir))
        self.ir["scope"]["included"].append("extra")
        self.assertNotEqual(original, port.document_digest(self.ir))

    def test_cli_rejects_default_empty_configuration(self):
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "--config",
             str(SKILL / "assets/config.template.json"),
             "--workspace-root", str(self.workspace)],
            capture_output=True, text=True,
        )
        self.assertEqual(1, result.returncode)
        self.assertIn("android_root", result.stdout)

    def test_cli_digest_does_not_modify_input(self):
        path = self.workspace / "ir.json"
        path.write_text(json.dumps(self.ir), encoding="utf-8")
        original = path.read_bytes()
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "--digest", str(path)],
            capture_output=True, text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(port.document_digest(self.ir), result.stdout.strip())
        self.assertEqual(original, path.read_bytes())


if __name__ == "__main__":
    unittest.main()
