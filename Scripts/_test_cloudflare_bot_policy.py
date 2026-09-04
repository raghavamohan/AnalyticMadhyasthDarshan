"""Regression checks for the repository-managed Cloudflare bot policy."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import _cloudflare_performance as cf


class CloudflareBotPolicyTests(unittest.TestCase):
    def test_granular_policy_allows_discovery_and_blocks_training(self) -> None:
        policy = cf.super_bot_fight_mode_spec()
        self.assertEqual(policy["ai_search"], "disabled")
        self.assertEqual(policy["ai_user"], "disabled")
        self.assertEqual(policy["ai_training"], "block")
        self.assertEqual(policy["ai_bots_protection"], "disabled")
        self.assertTrue(policy["bot_preference_sync_enabled"])
        self.assertTrue(policy["is_robots_txt_managed"])
        self.assertEqual(policy["content_bots_protection"], "disabled")
        self.assertEqual(policy["crawler_protection"], "enabled")

    def test_unknown_automation_is_challenged_and_verified_bots_allowed(self) -> None:
        policy = cf.super_bot_fight_mode_spec()
        self.assertEqual(policy["sbfm_definitely_automated"], "managed_challenge")
        self.assertEqual(policy["sbfm_verified_bots"], "allow")
        self.assertFalse(policy["sbfm_static_resource_protection"])
        self.assertTrue(policy["enable_js"])

    def test_public_content_does_not_bypass_training_policy(self) -> None:
        rules = cf.waf_custom_security_rules_spec()
        refs = {rule["ref"] for rule in rules}
        self.assertNotIn(cf.RETIRED_WEBMCP_SKIP_REF, refs)
        skips = [rule for rule in rules if rule.get("action") == "skip"]
        self.assertEqual([rule["ref"] for rule in skips], [cf.NOTIFY_SKIP_REF])
        self.assertEqual(skips[0]["expression"], cf.NOTIFY_SKIP_EXPRESSION)

    def test_policy_drift_is_reported(self) -> None:
        current = dict(cf.super_bot_fight_mode_spec())
        current["ai_training"] = "disabled"
        ok, issues = cf._bot_management_matches(
            current, cf.super_bot_fight_mode_spec()
        )
        self.assertFalse(ok)
        self.assertTrue(any("ai_training" in issue for issue in issues))

    def test_apply_removes_retired_path_wide_skip(self) -> None:
        ruleset = {
            "id": "ruleset",
            "rules": [
                cf.probe_block_rule_body(),
                cf.notify_skip_rule_body(),
                {
                    "ref": cf.RETIRED_WEBMCP_SKIP_REF,
                    "expression": '(http.host eq "example.com")',
                    "action": "skip",
                    "enabled": True,
                    "action_parameters": {"phases": ["http_request_sbfm"]},
                },
            ],
        }
        with (
            mock.patch.object(cf, "resolve_zone_id", return_value="zone"),
            mock.patch.object(cf, "get_waf_custom_entrypoint_ruleset", return_value=ruleset),
            mock.patch.object(cf, "_api_request", return_value={}) as request,
        ):
            cf.apply_waf_custom_security_rules("token", None)
        payload = request.call_args.args[3]
        refs = {rule["ref"] for rule in payload["rules"]}
        self.assertNotIn(cf.RETIRED_WEBMCP_SKIP_REF, refs)

    def test_apply_omits_legacy_fight_mode_on_sbfm_zone(self) -> None:
        current = dict(cf.super_bot_fight_mode_spec())
        current["ai_training"] = "disabled"
        with (
            mock.patch.object(cf, "resolve_zone_id", return_value="zone"),
            mock.patch.object(cf, "get_bot_management_config", return_value=current),
            mock.patch.object(cf, "_api_request", return_value={}) as request,
        ):
            cf.apply_super_bot_fight_mode("token", None)
        payload = request.call_args.args[3]
        self.assertNotIn("fight_mode", payload)

    def test_apply_disables_legacy_fight_mode_when_present(self) -> None:
        current = dict(cf.super_bot_fight_mode_spec())
        current["ai_training"] = "disabled"
        current["fight_mode"] = True
        with (
            mock.patch.object(cf, "resolve_zone_id", return_value="zone"),
            mock.patch.object(cf, "get_bot_management_config", return_value=current),
            mock.patch.object(cf, "_api_request", return_value={}) as request,
        ):
            cf.apply_super_bot_fight_mode("token", None)
        payload = request.call_args.args[3]
        self.assertFalse(payload["fight_mode"])


if __name__ == "__main__":
    unittest.main()
