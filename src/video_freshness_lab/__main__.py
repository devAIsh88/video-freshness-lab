"""Run synthetic experiments via ``python -m video_freshness_lab``."""

import argparse
import json
from dataclasses import replace

from .experiments import SCENARIOS
from .simulation import Simulator


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic synthetic freshness lab"
    )
    parser.add_argument("--scenario", choices=["all", *SCENARIOS], default="all")
    parser.add_argument(
        "--json", action="store_true", help="include full evidence as JSON"
    )
    for name in ("duration", "producer-interval", "consumer-duration"):
        parser.add_argument(f"--{name}-ms", type=int)
    parser.add_argument("--freshness-threshold-ms", type=int)
    parser.add_argument("--queue-capacity", type=int, help="FIFO waiting capacity only")
    parser.add_argument("--overflow", choices=["drop_newest", "drop_oldest"])
    args = parser.parse_args(argv)
    selected = (
        SCENARIOS
        if args.scenario == "all"
        else {args.scenario: SCENARIOS[args.scenario]}
    )
    results = {}
    for name, config in selected.items():
        overrides = {
            key: value
            for key, value in vars(args).items()
            if key not in ("scenario", "json") and value is not None
        }
        if config.policy == "latest":
            overrides.pop("queue_capacity", None)
        try:
            result = Simulator(replace(config, **overrides)).run()
        except ValueError as error:
            parser.error(str(error))
        results[name] = result
    if args.json:
        print(
            json.dumps(
                {name: r.to_dict() for name, r in results.items()}, sort_keys=True
            )
        )
    else:
        print(
            "Synthetic virtual-time observations only; all ages/times are milliseconds."
        )
        for name, result in results.items():
            m = result.metrics
            print(
                f"{name}: produced={m.frames_produced} consumed={m.frames_consumed} "
                f"dropped={m.frames_dropped} replaced={m.frames_replaced} "
                f"max_queue={m.max_queue_depth} max_start_age_ms={m.max_start_age_ms} "
                f"max_result_age_ms={m.max_completion_age_ms} "
                f"result_violations={m.result_freshness_violations} "
                f"finished_at_ms={m.finished_at_ms}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
