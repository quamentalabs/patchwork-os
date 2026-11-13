# SPDX-License-Identifier: MIT
from __future__ import annotations

import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from patchwork_os.deploy_cli import plan_inter_cli_dispatch


class DeployPlanContractTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.task = self.root / "task.md"
        self.task.write_bytes(b"local nonsensitive sample\n")
        self.arguments = dict(
            owner_session="local-test",
            run_id="sample",
            target_runtime="codex",
            task_path=self.task,
            workspace_root=self.root,
        )

    def plan(self, **overrides):
        arguments = dict(self.arguments, **overrides)
        models = {"codex": {"selected_models": ["example-model"]}}
        with patch(
            "patchwork_os.deploy_cli.resolve_canonical_three_tier_models",
            return_value=models,
        ):
            return plan_inter_cli_dispatch(**arguments)

    def test_default_is_a_nonexecuting_plan(self):
        plan = self.plan()
        self.assertEqual(plan["kind"], "deploy2-cli-plan")
        self.assertIs(plan["dry_run"], True)
        self.assertIs(plan["execution_supported"], False)
        self.assertEqual(plan["runtime_acceptance"], "not_run")
        self.assertIn("--dry-run", plan["launch_argv"])
        self.assertFalse(Path(plan["run_dir"]).exists())
        self.assertFalse(Path(plan["result_dir"]).exists())
        self.assertFalse((self.root / ".scratch").exists())

    def test_missing_task_is_rejected_before_model_resolution(self):
        arguments = dict(self.arguments, task_path=self.root / "missing.md")
        with patch(
            "patchwork_os.deploy_cli.resolve_canonical_three_tier_models"
            , return_value={"codex": {"selected_models": ["example-model"]}}
        ) as resolve:
            with self.assertRaisesRegex(FileNotFoundError, "task_path does not exist"):
                plan_inter_cli_dispatch(**arguments)
            resolve.assert_not_called()

    def test_directory_task_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "task_path must be a regular file"):
            self.plan(task_path=self.root)

    def test_live_request_is_rejected_before_reading_task_or_models(self):
        with patch(
            "patchwork_os.deploy_cli.resolve_canonical_three_tier_models"
            , return_value={"codex": {"selected_models": ["example-model"]}}
        ) as resolve, patch.object(Path, "read_bytes", return_value=b"sample") as read_bytes:
            with self.assertRaisesRegex(NotImplementedError, "live execution is not implemented"):
                plan_inter_cli_dispatch(**dict(self.arguments, dry_run=False))
            resolve.assert_not_called()
            read_bytes.assert_not_called()

    def test_hash_preserves_binary_bytes_and_valid_empty_files(self):
        for payload in (b"\x00task\r\n\xff", b""):
            with self.subTest(payload=payload):
                self.task.write_bytes(payload)
                self.assertEqual(
                    self.plan()["task"]["sha256"],
                    hashlib.sha256(payload).hexdigest(),
                )
