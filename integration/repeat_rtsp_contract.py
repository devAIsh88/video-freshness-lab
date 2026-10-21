"""Repeat mature 1.8 controls without changing their source or admission policy."""

import argparse
import json
import sys

from video_freshness_lab.rtsp_contract import RtspConfig
from video_freshness_lab.rtsp_experiment import run_isolated


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeat", type=int, default=100)
    args = parser.parse_args()
    if not 1 <= args.repeat <= 100:
        parser.error("repeat must be in [1, 100]")
    results = []
    for scenario in ("normal", "epoch", "reconnect"):
        for policy in ("fifo", "leaky"):
            for filtered in (False, True):
                for repetition in range(args.repeat):
                    result = run_isolated(RtspConfig(scenario, policy, filtered))
                    result["repetition"] = repetition
                    results.append(result)
                    print(
                        f"{scenario}/{policy}/{filtered}/{repetition}: {result['status']}",
                        file=sys.stderr,
                        flush=True,
                    )
        if scenario == "normal" and any(r["status"] != "ok" for r in results):
            break
    print(json.dumps({"results": results}))
    raise SystemExit(int(any(r["status"] != "ok" for r in results)))


if __name__ == "__main__":
    main()
