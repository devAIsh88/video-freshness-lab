"""Opt-in actual localhost transport fault trials, outside ordinary pytest CI."""

import unittest

from video_freshness_lab.transport_experiment import (
    SCENARIOS,
    FaultConfig,
    run_isolated,
)


class TransportFaultIntegration(unittest.TestCase):
    def test_abort_with_retained_media_still_joins_and_releases(self):
        r = run_isolated(FaultConfig("stall"), fault="abort-held")
        self.assertEqual(r["status"], "error", r)
        self.assertEqual(r["error"], "injected abort with transport media retained")
        self.assertTrue(r["relay"]["worker_joined"])
        self.assertTrue(r["relay"]["port_refused"])
        self.assertTrue(r["relay"]["connected_sockets_closed"])
        self.assertEqual(r["cleanup"]["remaining_owned_children"], 0)
        self.assertEqual(r["cleanup"]["remaining_python_threads"], 0)
        self.assertTrue(r["cleanup"]["all_clients_null"])
        self.assertTrue(
            next(e["port_closed"] for e in r["events"] if "port_closed" in e)
        )

    def test_all_declared_transport_and_application_controls(self):
        for scenario in SCENARIOS:
            for policy in ("fifo", "leaky"):
                for filtered in (False, True):
                    with self.subTest(
                        scenario=scenario, policy=policy, filtered=filtered
                    ):
                        r = run_isolated(FaultConfig(scenario, policy, filtered))
                        self.assertEqual(r["status"], "ok", r)
                        self.assertEqual(r["timeout_count"], 0)
                        self.assertEqual(r["cleanup"]["errors"], [])
                        self.assertEqual(r["cleanup"]["remaining_owned_children"], 0)
                        self.assertEqual(r["cleanup"]["remaining_python_threads"], 0)
                        self.assertTrue(r["cleanup"]["all_clients_null"])
                        self.assertTrue(r["relay"]["worker_joined"])
                        self.assertTrue(r["relay"]["port_refused"])
                        self.assertEqual(r["relay"]["errors"], [])
                        self.assertEqual(
                            len(r["clients"]),
                            4
                            if scenario == "cycles"
                            else 2
                            if scenario in ("close", "slow-interruption")
                            else 1,
                        )
                        self.assertTrue(
                            all(
                                c["continuity"]["nonadvancing"] == 0
                                for c in r["clients"]
                            )
                        )
                        exits = [e for e in r["events"] if "server_exitcode" in e]
                        self.assertEqual(len(exits), 1)
                        self.assertEqual(exits[0]["server_exitcode"], 0)
                        self.assertTrue(exits[0]["port_closed"])
                        self.assertFalse(exits[0]["termination_fallback"])
                        for c in r["clients"]:
                            for receipt in c["receipts"]:
                                self.assertIsNone(receipt["capture_age_ns"])
                        if scenario == "delay":
                            release = next(
                                e
                                for e in r["relay"]["events"]
                                if e["kind"] == "forwarded-held"
                            )
                            self.assertGreaterEqual(
                                release["at_ns"] - release["hold_started_ns"],
                                200_000_000,
                            )
                        if scenario in ("stall", "epoch", "recovery"):
                            self.assertEqual(len(r["resumptions"]), 1)
                            self.assertGreaterEqual(
                                r["resumptions"][0]["receipt_ns"],
                                r["resumptions"][0]["release_ns"],
                            )


if __name__ == "__main__":
    unittest.main()
