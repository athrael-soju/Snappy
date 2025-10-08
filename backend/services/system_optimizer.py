import logging
import os
import platform
import subprocess
from typing import Any, Dict, List, Tuple

try:
    import psutil  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    psutil = None

from runtime_config import get_runtime_config

logger = logging.getLogger(__name__)


def _get_total_memory_gb() -> float | None:
    """Return total system memory in gigabytes."""
    candidates: List[float] = []

    if psutil:
        try:
            candidates.append(round(float(psutil.virtual_memory().total) / (1024**3), 1))
        except Exception as exc:  # pragma: no cover - best effort
            logger.debug("psutil failed to report memory: %s", exc)

    if hasattr(os, "sysconf"):
        try:
            page_size = os.sysconf("SC_PAGE_SIZE")  # type: ignore[arg-type]
            phys_pages = os.sysconf("SC_PHYS_PAGES")  # type: ignore[arg-type]
            if isinstance(page_size, int) and isinstance(phys_pages, int):
                candidates.append(round(page_size * phys_pages / (1024**3), 1))
        except (ValueError, OSError):  # pragma: no cover - platform dependent
            pass

    if platform.system() == "Windows":  # pragma: no cover - windows only
        try:
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            mem_status = MEMORYSTATUSEX()
            mem_status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem_status))  # type: ignore[attr-defined]
            candidates.append(round(mem_status.ullTotalPhys / (1024**3), 1))
        except Exception as exc:
            logger.debug("ctypes memory probe failed: %s", exc)

    return max(candidates) if candidates else None


def _detect_nvidia_gpus() -> Tuple[int, List[str]]:
    """Detect NVIDIA GPUs via nvidia-smi if available."""
    try:
        proc = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        if proc.returncode != 0:
            return 0, []
        names = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        return len(names), names
    except FileNotFoundError:
        return 0, []
    except Exception as exc:  # pragma: no cover - best effort
        logger.debug("nvidia-smi probe failed: %s", exc)
        return 0, []


def _get_cpu_model() -> str | None:
    """Attempt to determine the CPU model name."""
    candidates = [
        platform.processor(),
        getattr(platform.uname(), "processor", ""),
        getattr(platform.uname(), "machine", ""),
    ]
    for value in candidates:
        if value:
            return value

    if platform.system() == "Linux":
        try:
            with open("/proc/cpuinfo", "r", encoding="utf-8") as cpuinfo:
                for line in cpuinfo:
                    if "model name" in line:
                        return line.split(":", 1)[1].strip()
        except Exception as exc:  # pragma: no cover - best effort
            logger.debug("/proc/cpuinfo read failed: %s", exc)

    return None


def _get_cpu_frequency_ghz() -> float | None:
    """Return the current CPU frequency in GHz if available."""
    if psutil:
        try:
            freq = psutil.cpu_freq()
            if freq and freq.current:
                return round(freq.current / 1000.0, 2)
        except Exception as exc:  # pragma: no cover - best effort
            logger.debug("psutil failed to report cpu frequency: %s", exc)
    return None


def _choose_profile(cores: int, ram_gb: float | None, gpu_count: int) -> str:
    safe_ram = ram_gb or 0.0
    if gpu_count > 0:
        if cores >= 16 and safe_ram >= 48:
            return "gpu_high"
        return "gpu_standard"
    if cores >= 12 and safe_ram >= 32:
        return "cpu_high"
    if cores >= 6 and safe_ram >= 16:
        return "balanced"
    return "light"


def _derive_minio_workers(cores: int, profile: str) -> int:
    if profile in {"gpu_high", "cpu_high"}:
        return min(32, max(8, cores * 2))
    if profile in {"gpu_standard", "balanced"}:
        return min(24, max(6, cores * 2))
    return max(4, min(12, cores * 2))


def _derive_minio_retries(workers: int) -> int:
    if workers >= 24:
        return 5
    if workers >= 16:
        return 4
    if workers >= 8:
        return 3
    return 2


def build_recommendations() -> Dict[str, Any]:
    """Build recommended configuration values based on detected hardware."""
    cores = os.cpu_count() or 1
    ram_gb = _get_total_memory_gb()
    gpu_count, gpu_names = _detect_nvidia_gpus()
    cpu_model = _get_cpu_model()
    cpu_freq = _get_cpu_frequency_ghz()

    profile = _choose_profile(cores, ram_gb, gpu_count)

    if profile == "light":
        batch_size = 4
        pipeline_indexing = False
    elif profile == "balanced":
        batch_size = 8
        pipeline_indexing = True
    else:
        # cpu_high, gpu_standard, gpu_high
        batch_size = 12 if (ram_gb or 0) < 48 else 16
        pipeline_indexing = True

    minio_workers = _derive_minio_workers(cores, profile)
    minio_retries = _derive_minio_retries(minio_workers)

    recommendations: Dict[str, Any] = {
        "BATCH_SIZE": batch_size,
        "ENABLE_PIPELINE_INDEXING": pipeline_indexing,
        "MINIO_WORKERS": minio_workers,
        "MINIO_RETRIES": minio_retries,
        "COLPALI_MODE": "gpu" if gpu_count > 0 else "cpu",
    }

    detection = {
        "cpu_cores": cores,
        "cpu_model": cpu_model,
        "cpu_frequency_ghz": cpu_freq,
        "total_ram_gb": ram_gb,
        "nvidia_gpu_count": gpu_count,
        "nvidia_gpu_names": gpu_names,
        "profile": profile,
    }

    summary_parts: List[str] = []
    if cpu_model:
        summary_parts.append(cpu_model)
    summary_parts.append(f"{cores} core{'s' if cores != 1 else ''}")
    if cpu_freq:
        summary_parts[-1] += f" @ {cpu_freq:.2f} GHz"
    if ram_gb is not None:
        summary_parts.append(f"{ram_gb:.1f} GB RAM")
    if gpu_count > 0:
        if gpu_names:
            gpu_list = ", ".join(gpu_names[:2])
            extra = "" if gpu_count <= 2 else f" (+{gpu_count - 2} more)"
            summary_parts.append(f"{gpu_count} NVIDIA GPU{'s' if gpu_count != 1 else ''} ({gpu_list}{extra})")
        else:
            summary_parts.append(f"{gpu_count} NVIDIA GPU{'s' if gpu_count != 1 else ''}")

    summary = "; ".join(summary_parts)
    message = f"Optimised configuration for {profile.replace('_', ' ')} profile ({summary})."

    return {
        "recommendations": recommendations,
        "detection": detection,
        "message": message,
    }


def optimize_runtime_config() -> Dict[str, Any]:
    """
    Apply recommended runtime configuration values based on the host system.

    Returns:
        Dictionary containing applied keys, unchanged keys, detection details, and message.
    """
    runtime_cfg = get_runtime_config()
    info = build_recommendations()

    recommendations: Dict[str, Any] = info["recommendations"]
    applied: Dict[str, str] = {}
    unchanged: List[str] = []

    for key, value in recommendations.items():
        new_value = str(value)
        current = runtime_cfg.get(key, "")
        if current != new_value:
            runtime_cfg.set(key, new_value)
            applied[key] = new_value
        else:
            unchanged.append(key)

    return {
        "applied": applied,
        "unchanged": unchanged,
        "detection": info["detection"],
        "message": info["message"],
        "profile": info["detection"]["profile"],
    }
