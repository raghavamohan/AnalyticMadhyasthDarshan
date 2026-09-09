"""Regression checks for the repository-managed Cloudflare bot policy."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parent
BASE = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import _cloudflare_performance as cf
import _test_api_catalog as api_catalog


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
        self.assertEqual(policy["crawler_protection"], "disabled")

    def test_generic_automation_and_verified_bots_are_allowed(self) -> None:
        policy = cf.super_bot_fight_mode_spec()
        self.assertEqual(policy["sbfm_definitely_automated"], "allow")
        self.assertEqual(policy["sbfm_verified_bots"], "allow")
        self.assertFalse(policy["sbfm_static_resource_protection"])
        self.assertTrue(policy["enable_js"])

    def test_rate_limit_covers_every_dynamic_api_surface(self) -> None:
        expression = cf.edge_api_rate_limit_expression()
        self.assertIn(cf.API_HOST, expression)
        self.assertIn(cf.SITE_HOST, expression)
        self.assertIn('starts_with(http.request.uri.path, "/api/")', expression)
        self.assertIn('starts_with(http.request.uri.path, "/mcp")', expression)

    def test_agent_publication_deploy_converges_edge_policy(self) -> None:
        workflow = (BASE / ".github" / "workflows" / "agent-publications.yml").read_text(
            encoding="utf-8"
        )
        for flag in (
            "--apply-security-headers",
            "--apply-portal-edge-security",
            "--apply-discussions-rate-limits",
        ):
            self.assertIn(flag, workflow)

    def test_agent_publication_verifies_only_its_api_catalog_route(self) -> None:
        workflow = (BASE / ".github" / "workflows" / "agent-publications.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "python Scripts/_test_api_catalog.py --live-catalog-only",
            workflow,
        )
        self.assertNotIn("python Scripts/_test_api_catalog.py --live; then", workflow)

    def test_catalog_only_mode_excludes_cross_owned_live_surfaces(self) -> None:
        catalog = {"linkset": []}
        with (
            mock.patch.object(api_catalog, "check_live_catalog", return_value=catalog) as worker,
            mock.patch.object(api_catalog, "check_live_openapi") as openapi,
            mock.patch.object(api_catalog, "check_live_homepage_link_headers") as homepage,
            mock.patch.object(api_catalog, "check_live_status_links") as status,
            mock.patch.object(api_catalog, "check_live_cookie_auth") as auth,
        ):
            api_catalog.run_live_checks(catalog_only=True)
        worker.assert_called_once_with()
        openapi.assert_not_called()
        homepage.assert_not_called()
        status.assert_not_called()
        auth.assert_not_called()

    def test_full_live_mode_retains_cross_surface_diagnostics(self) -> None:
        catalog = {"linkset": []}
        with (
            mock.patch.object(api_catalog, "check_live_catalog", return_value=catalog),
            mock.patch.object(api_catalog, "check_live_openapi") as openapi,
            mock.patch.object(api_catalog, "check_live_homepage_link_headers") as homepage,
            mock.patch.object(api_catalog, "check_live_status_links") as status,
            mock.patch.object(api_catalog, "check_live_cookie_auth") as auth,
        ):
            api_catalog.run_live_checks(catalog_only=False)
        openapi.assert_called_once_with()
        homepage.assert_called_once_with()
        status.assert_called_once_with(catalog)
        auth.assert_called_once_with()

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
