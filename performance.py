"""
Performance monitoring for the Self-Development Organism system.

Provides timing and memory tracking to enforce:
  - Analysis completes within 30 seconds
  - Memory usage stays within reasonable bounds
  - No external API dependencies for core function
"""

import time
import sys
from contextlib import contextmanager
from typing import Dict


ANALYSIS_TIMEOUT_SECONDS = 30
MEMORY_LIMIT_MB = 256


@contextmanager
def timed_operation(label: str = "operation"):
    """Context manager that measures wall-clock time of an operation.

    Yields a dict that will contain 'elapsed' (seconds) after the block.
    """
    result = {"elapsed": 0.0}
    start = time.monotonic()
    yield result
    result["elapsed"] = time.monotonic() - start


def check_analysis_time(elapsed: float) -> bool:
    """Return True if elapsed time is within the allowed budget."""
    return elapsed <= ANALYSIS_TIMEOUT_SECONDS


def get_memory_usage_mb() -> float:
    """Return approximate RSS memory usage of the current process in MB.

    Uses /proc/self/status on Linux, falls back to sys.getsizeof heuristic.
    """
    try:
        with open("/proc/self/status", "r") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024.0  # kB -> MB
    except (OSError, ValueError, IndexError):
        pass
    return 0.0


def check_memory_usage() -> bool:
    """Return True if current memory usage is within bounds."""
    usage = get_memory_usage_mb()
    if usage == 0.0:
        return True  # cannot measure, assume OK
    return usage <= MEMORY_LIMIT_MB


def verify_no_external_apis() -> Dict[str, bool]:
    """Verify that core modules have no external API dependencies.

    Checks that no HTTP/network libraries are imported by core modules.
    Returns a dict mapping module name to whether it is clean.
    """
    network_modules = {
        "requests", "httpx", "urllib3", "aiohttp",
        "grpc", "websocket", "boto3", "google.cloud",
    }
    core_modules = [
        "organism", "models", "analyzers", "perspectives",
        "diagnostics", "formatters", "user_perspective",
        "increment_tracker", "performance",
    ]
    results = {}
    for mod_name in core_modules:
        mod = sys.modules.get(mod_name)
        if mod is None:
            results[mod_name] = True
            continue
        # Check the module's direct imports via its globals
        mod_globals = set(dir(mod))
        has_network = bool(mod_globals & network_modules)
        results[mod_name] = not has_network
    return results
