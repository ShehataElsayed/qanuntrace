"""Run `qanuntrace-doctor config.json` before integration."""
import argparse
import sys

from .config import doctor, load_config


def main():
    parser = argparse.ArgumentParser(description="Read-only database mapping check")
    parser.add_argument("config", help="local JSON config; secrets are read from environment")
    args = parser.parse_args()
    try:
        checks = doctor(load_config(args.config))
        for check in checks: print(check)
        if "sample_hash_mismatch" in checks or "no_sample_row_found; verify schema manually" in checks:
            return 2
        return 0
    except (ValueError, KeyError, OSError, TypeError, ImportError) as exc:
        print(f"configuration check failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
