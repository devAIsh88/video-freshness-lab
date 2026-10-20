"""Explicit system-Python integration suite; excluded from normal pytest discovery.

PYTHONPATH=src /usr/bin/python3 -m unittest discover -s integration -v
Missing GI/GstApp is a failure, never a silent skip. No pytest dependency needed.
"""

import unittest

from video_freshness_lab.gstreamer_contract import WORKLOADS, ExperimentConfig
from video_freshness_lab.gstreamer_experiment import run_isolated


class NativeIntegration(unittest.TestCase):
    def assert_cleanup(self, result):
        self.assertTrue(result.get("cleanup_null"), result)
        self.assertEqual(result.get("extra_python_threads"), 0, result)

    def test_native_and_application_boundaries(self):
        for workload in WORKLOADS:
            for policy in ("fifo", "leaky"):
                pair = []
                for filtered in (False, True):
                    with self.subTest(
                        workload=workload, policy=policy, filtered=filtered
                    ):
                        r = run_isolated(ExperimentConfig(policy, filtered, workload))
                        self.assertEqual(r["status"], "ok", r)
                        self.assert_cleanup(r)
                        pair.append(r)
                        tokens = [item["token"] for item in r["receipts"]]
                        expected = list(range(4))
                        if workload == "shutdown":
                            expected = []
                        elif policy == "leaky" and workload in ("slow", "active-epoch"):
                            expected = [0, 2, 3]
                        elif policy == "leaky" and workload == "buffered-epoch":
                            expected = [2, 3]
                        self.assertEqual(tokens, expected)
                        obsolete = sum(d["obsolete"] for d in r["decisions"])
                        self.assertEqual(
                            r["counts"]["rejected"], obsolete if filtered else 0
                        )
                        if workload == "active-epoch":
                            self.assertEqual(obsolete, 2 if policy == "fifo" else 1)
                        for item in r["receipts"]:
                            self.assertIsNone(item["capture_age_ns"])
                            self.assertGreaterEqual(item["submission_to_receipt_ns"], 0)
                        final = r["snapshots"][-1]
                        self.assertEqual(final["appsrc"]["dropped"], 0)
                        self.assertEqual(
                            final["appsink"]["current-level-buffers"],
                            2 if workload == "shutdown" else 0,
                        )
                self.assertEqual(
                    pair[0]["counts"]["native_drops"], pair[1]["counts"]["native_drops"]
                )
                self.assertEqual(
                    [r["token"] for r in pair[0]["receipts"]],
                    [r["token"] for r in pair[1]["receipts"]],
                )

                def media(r):
                    return [
                        (s["token"], s["epoch"], s["pts"]) for s in r["submissions"]
                    ]

                self.assertEqual(media(pair[0]), media(pair[1]))

    def test_eos_wait_true_drains_pending_buffers_before_bus_eos(self):
        for policy in ("fifo", "leaky"):
            with self.subTest(policy=policy):
                r = run_isolated(
                    ExperimentConfig(policy, True, "shutdown"), fault="eos-wait"
                )
                self.assertEqual(r["status"], "ok", r)
                self.assert_cleanup(r)
                pending = next(
                    s for s in r["snapshots"] if s["label"] == "EOS-at-pad-before-drain"
                )
                self.assertEqual(pending["appsink"]["current-level-buffers"], 2)
                self.assertEqual(r["counts"]["published"], 2)

    def test_faults_report_failure_and_leave_null_pipeline(self):
        for fault in ("bus-error", "association", "processing", "abort"):
            with self.subTest(fault=fault):
                work = "buffered-epoch" if fault == "abort" else "balanced"
                r = run_isolated(ExperimentConfig("fifo", True, work), fault=fault)
                self.assertEqual(r["status"], "error", r)
                self.assert_cleanup(r)
                self.assertEqual(r["error_type"], "RuntimeError")
                if fault == "bus-error":
                    self.assertIn("gst-core-error-quark/1", r["error"])
                if fault == "abort":
                    self.assertEqual(
                        r["snapshots"][-1]["appsink"]["current-level-buffers"], 2
                    )


if __name__ == "__main__":
    unittest.main()
