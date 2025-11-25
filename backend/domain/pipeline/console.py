"""Rich console utilities for pipeline visualization."""

import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree


class StageStatus(Enum):
    """Status of a pipeline stage."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SLOW = "slow"  # Completed but exceeded threshold


@dataclass
class StageInfo:
    """Information about a stage's execution."""

    name: str
    status: StageStatus = StageStatus.PENDING
    duration_s: float = 0.0
    icon: str = ""
    color: str = "white"

    @property
    def status_icon(self) -> str:
        """Get status indicator icon."""
        icons = {
            StageStatus.PENDING: "⏳",
            StageStatus.RUNNING: "🔄",
            StageStatus.COMPLETED: "✓",
            StageStatus.FAILED: "✗",
            StageStatus.SLOW: "⚠️",
        }
        return icons.get(self.status, "")


@dataclass
class BatchProgress:
    """Tracks progress for a single batch."""

    batch_id: int
    num_pages: int
    page_range: str
    stages: Dict[str, StageInfo] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize stage tracking."""
        if not self.stages:
            self.stages = {
                "storage": StageInfo("Storage", icon="🖼️", color="cyan"),
                "embedding": StageInfo("Embedding", icon="🧠", color="magenta"),
                "ocr": StageInfo("OCR", icon="📝", color="yellow"),
                "upsert": StageInfo("Upsert", icon="💾", color="green"),
            }


# Thresholds for marking stages as slow (seconds)
SLOW_THRESHOLDS = {
    "storage": 2.0,
    "embedding": 10.0,
    "ocr": 5.0,
    "upsert": 2.0,
}


class PipelineConsole:
    """Rich console for pipeline progress visualization.

    Thread-safe console output for multi-stage pipeline processing.
    """

    def __init__(self, console: Optional[Console] = None):
        """Initialize pipeline console.

        Args:
            console: Optional Rich console instance (creates new if not provided)
        """
        self.console = console or Console()
        self._lock = threading.Lock()
        self._batches: Dict[int, BatchProgress] = {}
        self._current_document: Optional[str] = None
        self._total_pages: int = 0
        self._completed_pages: int = 0


    def start_document(self, filename: str, total_pages: int, file_size_mb: float):
        """Announce start of document processing.

        Args:
            filename: Name of the document being processed
            total_pages: Total number of pages in the document
            file_size_mb: File size in megabytes
        """
        with self._lock:
            self._current_document = filename
            self._total_pages = total_pages
            self._completed_pages = 0
            self._batches.clear()

            # Create styled header
            header = Text()
            header.append("⚡ ", style="yellow bold")
            header.append("Processing ", style="bold")
            header.append(filename, style="cyan bold")
            header.append(f" ({total_pages} pages, {file_size_mb:.1f} MB)", style="dim")

            self.console.print()
            self.console.print(Panel(header, border_style="blue"))

    def start_batch(self, batch_id: int, page_start: int, page_end: int, num_pages: int):
        """Announce start of a new batch.

        Args:
            batch_id: Batch identifier (0-indexed internally)
            page_start: First page number in batch
            page_end: Last page number in batch
            num_pages: Number of pages in batch
        """
        with self._lock:
            page_range = f"{page_start}-{page_end}"
            self._batches[batch_id] = BatchProgress(
                batch_id=batch_id,
                num_pages=num_pages,
                page_range=page_range,
            )

            # Display batch number as 1-indexed for users
            display_batch = batch_id + 1

            # Print batch start with tree structure (extra newline for separation)
            self.console.print()
            tree = Tree(
                f"[bold blue]📦 Batch {display_batch}[/] [dim]Pages {page_range} ({num_pages} pages)[/]"
            )
            self.console.print(tree)

    def stage_started(self, batch_id: int, stage_name: str):
        """Mark a stage as started.

        Args:
            batch_id: Batch identifier
            stage_name: Name of the stage (storage, embedding, ocr, upsert)
        """
        with self._lock:
            batch = self._batches.get(batch_id)
            if batch and stage_name in batch.stages:
                batch.stages[stage_name].status = StageStatus.RUNNING

    def stage_completed(
        self, batch_id: int, stage_name: str, duration_s: float, extra_info: str = ""
    ):
        """Mark a stage as completed and print status.

        Args:
            batch_id: Batch identifier
            stage_name: Name of the stage
            duration_s: Duration in seconds
            extra_info: Optional additional information to display
        """
        with self._lock:
            batch = self._batches.get(batch_id)
            if not batch or stage_name not in batch.stages:
                return

            stage = batch.stages[stage_name]
            stage.duration_s = duration_s

            # Check if slow
            threshold = SLOW_THRESHOLDS.get(stage_name, 5.0)
            if duration_s > threshold:
                stage.status = StageStatus.SLOW
            else:
                stage.status = StageStatus.COMPLETED

            # Build status line
            status_icon = stage.status_icon
            duration_style = "yellow bold" if stage.status == StageStatus.SLOW else "green"

            line = Text()
            line.append("    ├── ", style="dim")
            line.append(f"{stage.icon} ", style=stage.color)
            line.append(f"{stage.name:<10}", style=stage.color)
            line.append(f" {duration_s:.2f}s ", style=duration_style)
            line.append(status_icon)

            if extra_info:
                line.append(f" {extra_info}", style="dim")

            if stage.status == StageStatus.SLOW:
                line.append(" (slow)", style="yellow")

            self.console.print(line)

    def stage_failed(self, batch_id: int, stage_name: str, error: str):
        """Mark a stage as failed.

        Args:
            batch_id: Batch identifier
            stage_name: Name of the stage
            error: Error message
        """
        with self._lock:
            batch = self._batches.get(batch_id)
            if batch and stage_name in batch.stages:
                batch.stages[stage_name].status = StageStatus.FAILED

            line = Text()
            line.append("    ├── ", style="dim")
            line.append(f"✗ {stage_name}", style="red bold")
            line.append(f" FAILED: {error}", style="red")

            self.console.print(line)

    def batch_completed(self, batch_id: int, total_completed_pages: int):
        """Mark a batch as fully completed.

        Args:
            batch_id: Batch identifier
            total_completed_pages: Total pages completed so far
        """
        with self._lock:
            self._completed_pages = total_completed_pages
            batch = self._batches.get(batch_id)
            if not batch:
                return

            # Display batch number as 1-indexed for users
            display_batch = batch_id + 1

            # Print completion line
            line = Text()
            line.append("    └── ", style="dim")
            line.append("✓ ", style="green bold")
            line.append(f"Batch {display_batch} complete", style="green")
            line.append(f" ({total_completed_pages}/{self._total_pages} pages)", style="dim")

            self.console.print(line)
            self.console.print()  # Blank line between batches

    def document_completed(self, total_pages: int, total_time_s: float):
        """Announce document processing completion.

        Args:
            total_pages: Total pages processed
            total_time_s: Total processing time in seconds
        """
        with self._lock:
            # Create completion panel
            summary = Table.grid(padding=(0, 2))
            summary.add_column(style="bold")
            summary.add_column()

            summary.add_row("✓ Document", self._current_document or "Unknown")
            summary.add_row("📄 Pages", str(total_pages))
            summary.add_row("⏱️  Time", f"{total_time_s:.1f}s")
            summary.add_row(
                "📊 Rate", f"{total_pages / total_time_s:.1f} pages/sec" if total_time_s > 0 else "N/A"
            )

            self.console.print()
            self.console.print(
                Panel(
                    summary,
                    title="[green bold]Processing Complete[/]",
                    border_style="green",
                )
            )

    def print_error(self, message: str, exc: Optional[Exception] = None):
        """Print an error message.

        Args:
            message: Error message
            exc: Optional exception
        """
        with self._lock:
            error_text = Text()
            error_text.append("✗ ", style="red bold")
            error_text.append(message, style="red")
            if exc:
                error_text.append(f"\n  {type(exc).__name__}: {exc}", style="red dim")

            self.console.print(Panel(error_text, border_style="red"))


# Global console instance for the pipeline
_pipeline_console: Optional[PipelineConsole] = None
_console_lock = threading.Lock()


def get_pipeline_console() -> PipelineConsole:
    """Get or create the global pipeline console instance.

    Returns:
        PipelineConsole: The global console instance
    """
    global _pipeline_console
    with _console_lock:
        if _pipeline_console is None:
            _pipeline_console = PipelineConsole()
        return _pipeline_console


def reset_pipeline_console():
    """Reset the global pipeline console (useful for testing)."""
    global _pipeline_console
    with _console_lock:
        _pipeline_console = None
