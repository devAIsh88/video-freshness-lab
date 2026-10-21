"""Opt-in localhost integration; missing native bindings fail, never skip.

PYTHONPATH=src /usr/bin/python3 -m unittest discover -s integration -p 'test_rtsp_transport.py' -v
"""

import unittest

from video_freshness_lab.rtsp_contract import SCENARIOS, RtspConfig
from video_freshness_lab.rtsp_experiment import run_isolated


class RtspIntegration(unittest.TestCase):
    def assert_cleanup(self, result, expected_errors=None):
        cleanup = result["cleanup"]
        self.assertEqual(cleanup["errors"], expected_errors or [], result)
        self.assertEqual(cleanup["owned_children_remaining"], 0, result)
        self.assertEqual(cleanup["extra_python_threads"], 0, result)
        self.assertTrue(cleanup["all_clients_null"], result)
        exits = [e for e in result["events"] if "server_exitcode" in e]
        self.assertTrue(exits)
        for event in exits:
            self.assertEqual(event["server_exitcode"], 0)
            self.assertTrue(event["port_closed"])
            self.assertFalse(event["termination_fallback"])
            self.assertEqual(event["accepted_loopback"], [True])
            cleanup = event["library_cleanup"]
            self.assertTrue(cleanup["pool_drained"])
            self.assertTrue(cleanup["media_null"])
            self.assertTrue(all(cleanup["media_null"]))

    def test_transport_and_application_output_controls(self):
        for scenario in SCENARIOS:
            for policy in ("fifo", "leaky"):
                for filtered in (False, True):
                    with self.subTest(
                        scenario=scenario, policy=policy, filtered=filtered
                    ):
                        result = run_isolated(RtspConfig(scenario, policy, filtered))
                        self.assertEqual(result["status"], "ok", result)
                        self.assert_cleanup(result)
                        self.assertEqual(
                            len(result["clients"]), 2 if scenario == "reconnect" else 1
                        )
                        for client in result["clients"]:
                            self.assertTrue(client["rtp_packets"])
                            self.assertTrue(client["receipts"])
                            for receipt in client["receipts"]:
                                self.assertIsNone(receipt["capture_age_ns"])
                                self.assertGreaterEqual(receipt["pad_to_receipt_ns"], 0)
                                self.assertIn("video/x-raw", receipt["caps"])
                            snapshot = client["pre_null_snapshot"]
                            self.assertEqual(snapshot["rtp_caps"]["clock-rate"], 90000)
                            self.assertEqual(
                                set(snapshot["rtp_caps"]),
                                {"media", "payload", "clock-rate", "encoding-name"},
                            )
                        if scenario in ("epoch", "reconnect"):
                            old = [d for d in result["decisions"] if d["obsolete"]]
                            self.assertEqual(len(old), 1)
                            self.assertIs(old[0]["published"], not filtered)
                            self.assertTrue(
                                any(
                                    d["epoch"] == 1 and d["published"]
                                    for d in result["decisions"]
                                )
                            )
                        if scenario == "blocked-read":
                            read = result["blocked_read"]
                            null = result["clients"][0]["cleanup"]
                            self.assertLess(
                                read["read_enter_ns"], null["null_request_ns"]
                            )
                            self.assertGreaterEqual(
                                read["read_return_ns"], null["null_request_ns"]
                            )
                            self.assertFalse(read["returned_sample"])

    def test_processing_failure_still_releases_pipeline_and_server(self):
        result = run_isolated(RtspConfig("normal"), fault="processing")
        self.assertEqual(result["status"], "error", result)
        self.assertIn("injected processing failure", result["error"])
        self.assert_cleanup(result)
        self.assertEqual(result["decisions"], [])

    def test_snapshot_failure_cannot_prevent_null_cleanup(self):
        result = run_isolated(RtspConfig("normal"), fault="snapshot")
        self.assertEqual(result["status"], "error", result)
        self.assertEqual(result["error"], "injected snapshot failure")
        self.assert_cleanup(result, ["injected snapshot failure"])


if __name__ == "__main__":
    unittest.main()
