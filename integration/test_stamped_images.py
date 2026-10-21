"""Opt-in real NumPy/OpenCV arrays. Missing media dependencies fail explicitly."""

import unittest
from dataclasses import FrozenInstanceError, replace

import cv2
import numpy as np

from video_freshness_lab.model import Frame
from video_freshness_lab.stamped_images import (
    ImageSimulator,
    Marker,
    generate,
    read_marker,
    repeated_content,
    run_images,
    transform,
    verify,
    workloads,
)


class StampedImages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cv2.setNumThreads(1)

    def test_source_marker_survives_actual_color_and_png_transform(self):
        for source, epoch, sequence in ((7, 0, 0), (8, 2, 17), (2**32 - 1, 3, 99)):
            with self.subTest(source=source, epoch=epoch, sequence=sequence):
                image = generate(Frame(epoch, sequence, 10), source)
                expected = Marker(source, epoch, sequence)
                self.assertEqual(read_marker(image.pixels), expected)
                decoded = transform(image.pixels)
                self.assertEqual(verify(decoded, image.evidence), expected)
                self.assertFalse(np.shares_memory(decoded, image.pixels))
                # The actual color operation changes scene pixels; identity is
                # validated through marker decoding, not whole-buffer equality.
                self.assertFalse(np.array_equal(decoded[80:], image.pixels[80:]))
                self.assertIsNone(image.evidence.capture)

    def test_image_and_sidecar_cannot_be_mutated_during_held_work(self):
        image = generate(Frame(0, 0, 0))
        with self.assertRaises(ValueError):
            image.pixels[0, 0, 0] = 0
        with self.assertRaises(ValueError):
            image.pixels.setflags(write=True)
        with self.assertRaises(FrozenInstanceError):
            image.evidence.epoch = 1

    def test_corrupt_ambiguous_cropped_or_mismatched_identity_fails_closed(self):
        original = generate(Frame(0, 0, 0))
        corrupt = original.pixels.copy()
        corrupt[:4, :4] = 240 - corrupt[:4, :4] + 16
        ambiguous = original.pixels.copy()
        ambiguous[:4, :4] = 128
        for pixels in (
            corrupt,
            ambiguous,
            original.pixels[:-1],
            original.pixels.astype(float),
        ):
            self.assertIsNone(read_marker(pixels))
            with self.assertRaisesRegex(ValueError, "UNKNOWN"):
                verify(pixels, original.evidence)
        with self.assertRaisesRegex(ValueError, "mismatch"):
            verify(original.pixels, replace(original.evidence, epoch=1))

    def test_fifo_and_latest_use_same_source_images_and_preserve_counts(self):
        configs = workloads()
        fifo, latest = (
            run_images(configs["slow-fifo"]),
            run_images(configs["slow-latest"]),
        )
        self.assertEqual(fifo["produced_markers"], latest["produced_markers"])
        self.assertEqual(
            [o["marker"]["sequence"] for o in fifo["outputs"]], list(range(10))
        )
        self.assertEqual(
            [o["marker"]["sequence"] for o in latest["outputs"]], [0, 4, 8, 9]
        )
        self.assertEqual(fifo["metrics"]["max_completion_age_ms"], 310)
        self.assertEqual(latest["metrics"]["max_completion_age_ms"], 70)
        self.assertEqual(fifo["metrics"]["frames_dropped"], 0)
        self.assertEqual(latest["metrics"]["frames_replaced"], 6)
        self.assertTrue(
            all(
                o["capture_age_ns"] is None for o in fifo["outputs"] + latest["outputs"]
            )
        )

    def test_repeated_buffers_are_not_no_data_or_static_scene_with_new_stamps(self):
        r = repeated_content()
        self.assertEqual(r["no_data_deliveries"], 0)
        self.assertEqual(len(r["repeat_observations"]), 3)
        self.assertTrue(r["new_buffer_objects"] and r["no_shared_memory"])
        self.assertTrue(r["identical_repeated_pixels"] and r["static_scene_roi_equal"])
        self.assertEqual(
            [o["repeated_identity"] for o in r["repeat_observations"]],
            [False, True, True],
        )
        self.assertTrue(
            all(o["capture_freshness"] == "unknown" for o in r["repeat_observations"])
        )
        self.assertEqual([m["sequence"] for m in r["static_scene_markers"]], [0, 1, 2])

    def test_pause_produces_no_new_images_and_restart_retains_old_image_epoch(self):
        configs = workloads()
        pause = ImageSimulator(configs["pause-fifo"])
        result = pause.run()
        self.assertEqual(
            [f.produced_at_ms for f in result.frames], [0, 10, 60, 70, 80, 90]
        )
        self.assertEqual(len(pause.images), 6)
        for policy in ("fifo", "latest"):
            naive = run_images(configs[f"restart-{policy}-False"])
            filtered = run_images(configs[f"restart-{policy}-True"])
            self.assertGreater(naive["metrics"]["obsolete_session_outputs"], 0)
            self.assertEqual(filtered["metrics"]["obsolete_session_outputs"], 0)
            rejected = [o for o in filtered["outputs"] if not o["published"]]
            self.assertEqual(
                len(rejected), 1
            )  # Active old work, separate from queued rejects.
            self.assertEqual(rejected[0]["marker"]["epoch"], 0)
            self.assertIsNone(rejected[0]["capture_age_ns"])


if __name__ == "__main__":
    unittest.main()
