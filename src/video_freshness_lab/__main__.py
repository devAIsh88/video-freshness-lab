"""Run synthetic experiments via ``python -m video_freshness_lab``."""

import argparse
import json
from dataclasses import replace

from .experiments import SCENARIOS
from .recovery_experiments import RECOVERY_SCENARIOS
from .simulation import Simulator


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic synthetic freshness lab"
    )
    parser.add_argument(
        "--suite", choices=["buffering", "recovery", "all"], default="buffering"
    )
    parser.add_argument(
        "--scenario", choices=["all", *SCENARIOS, *RECOVERY_SCENARIOS], default="all"
    )
    parser.add_argument(
        "--json", action="store_true", help="include full evidence as JSON"
    )
    for name in ("duration", "producer-interval", "consumer-duration"):
        parser.add_argument(f"--{name}-ms", type=int)
    parser.add_argument("--freshness-threshold-ms", type=int)
    parser.add_argument("--queue-capacity", type=int, help="FIFO waiting capacity only")
    parser.add_argument("--overflow", choices=["drop_newest", "drop_oldest"])
    parser.add_argument("--policy", choices=["fifo", "latest"])
    parser.add_argument("--session-filter", action="store_true", default=None)
    parser.add_argument("--queue-on-disconnect", choices=["retain", "invalidate"])
    parser.add_argument("--no-progress-timeout-ms", type=int)
    args = parser.parse_args(argv)
    available = {**SCENARIOS, **RECOVERY_SCENARIOS}
    suites = {"buffering": SCENARIOS, "recovery": RECOVERY_SCENARIOS, "all": available}
    selected = (
        suites[args.suite]
        if args.scenario == "all"
        else {args.scenario: available[args.scenario]}
    )
    results = {}
    for name, config in selected.items():
        overrides = {
            key: value
            for key, value in vars(args).items()
            if key not in ("scenario", "suite", "json") and value is not None
        }
        if overrides.get("policy", config.policy) == "latest":
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
                f"obsolete_outputs={m.obsolete_session_outputs} "
                f"rejected={m.frames_rejected} no_progress={m.no_progress_intervals} "
                f"finished_at_ms={m.finished_at_ms}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
