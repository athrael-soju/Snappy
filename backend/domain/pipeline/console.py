"""Rich console utilities for pipeline visualization."""

import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

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
        self._batches: Dict[str, BatchProgress] = {}  # Key: "doc_id:batch_id"
        self._documents: List[str] = []  # List of document filenames
        self._total_pages: int = 0
        self._completed_pages: int = 0
        self._batch_counter: int = 0  # Global batch counter across all documents
        self._initialized: bool = False

    def start_job(self, filenames: List[str], total_pages: int, total_size_mb: float):
        """Initialize console for a batch processing job.

        Args:
            filenames: List of document filenames being processed
            total_pages: Total pages across all documents
            total_size_mb: Total file size in megabytes
        """
        with self._lock:
            self._documents = filenames
            self._total_pages = total_pages
            self._completed_pages = 0
            self._batches.clear()
            self._batch_counter = 0
            self._initialized = True

            # Create styled header
            header = Text()
            header.append("⚡ ", style="yellow bold")
            header.append("Processing ", style="bold")

            if len(filenames) == 1:
                header.append(filenames[0], style="cyan bold")
            else:
                header.append(f"{len(filenames)} documents", style="cyan bold")

            header.append(
                f" ({total_pages} pages, {total_size_mb:.1f} MB)", style="dim"
            )

            self.console.print()
            self.console.print(Panel(header, border_style="blue"))

    def start_document(self, filename: str, total_pages: int, file_size_mb: float):
        """Announce start of document processing.

        If start_job() was already called, this is a no-op (filename shown in batch headers).
        Otherwise, falls back to single-document mode for backwards compatibility.

        Args:
            filename: Name of the document being processed
            total_pages: Total number of pages in the document
            file_size_mb: File size in megabytes
        """
        with self._lock:
            if self._initialized:
                # Job already initialized - no-op, filename will be shown in batch headers
                pass
            else:
                # Fallback: single-document mode (no start_job called)
                self._documents = [filename]
                self._total_pages = total_pages
                self._completed_pages = 0
                self._batches.clear()
                self._batch_counter = 0

                # Create styled header
                header = Text()
                header.append("⚡ ", style="yellow bold")
                header.append("Processing ", style="bold")
                header.append(filename, style="cyan bold")
                header.append(
                    f" ({total_pages} pages, {file_size_mb:.1f} MB)", style="dim"
                )

                self.console.print()
                self.console.print(Panel(header, border_style="blue"))

    def start_batch(
        self,
        batch_id: int,
        page_start: int,
        page_end: int,
        num_pages: int,
        document_id: str = "",
        filename: str = "",
    ):
        """Announce start of a new batch.

        Args:
            batch_id: Batch identifier (0-indexed internally, per-document)
            page_start: First page number in batch
            page_end: Last page number in batch
            num_pages: Number of pages in batch
            document_id: Document identifier for composite key
            filename: Document filename for display
        """
        with self._lock:
            page_range = f"{page_start}-{page_end}"
            batch_key = f"{document_id}:{batch_id}" if document_id else str(batch_id)

            # Increment global batch counter for display
            self._batch_counter += 1
            display_batch = self._batch_counter

            self._batches[batch_key] = BatchProgress(
                batch_id=display_batch - 1,  # Store 0-indexed for internal use
                num_pages=num_pages,
                page_range=page_range,
            )

            # Print batch start with tree structure
            self.console.print()
            if filename and len(self._documents) > 1:
                # Multi-document mode: include filename in batch header
                tree = Tree(
                    f"[bold blue]📦 Batch {display_batch}[/] [cyan]{filename}[/] [dim]pp. {page_range}[/]"
                )
            else:
                # Single document mode: no need to repeat filename
                tree = Tree(
                    f"[bold blue]📦 Batch {display_batch}[/] [dim]Pages {page_range} ({num_pages} pages)[/]"
                )
            self.console.print(tree)

    def stage_started(self, batch_id: int, stage_name: str, document_id: str = ""):
        """Mark a stage as started.

        Args:
            batch_id: Batch identifier (per-document)
            stage_name: Name of the stage (storage, embedding, ocr, upsert)
            document_id: Document identifier for composite key
        """
        with self._lock:
            batch_key = f"{document_id}:{batch_id}" if document_id else str(batch_id)
            batch = self._batches.get(batch_key)
            if batch and stage_name in batch.stages:
                batch.stages[stage_name].status = StageStatus.RUNNING

    def stage_completed(
        self,
        batch_id: int,
        stage_name: str,
        duration_s: float,
        extra_info: str = "",
        document_id: str = "",
    ):
        """Mark a stage as completed and print status.

        Args:
            batch_id: Batch identifier (per-document)
            stage_name: Name of the stage
            duration_s: Duration in seconds
            extra_info: Optional additional information to display
            document_id: Document identifier for composite key
        """
        with self._lock:
            batch_key = f"{document_id}:{batch_id}" if document_id else str(batch_id)
            batch = self._batches.get(batch_key)
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
            duration_style = (
                "yellow bold" if stage.status == StageStatus.SLOW else "green"
            )

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

    def stage_failed(
        self, batch_id: int, stage_name: str, error: str, document_id: str = ""
    ):
        """Mark a stage as failed.

        Args:
            batch_id: Batch identifier (per-document)
            stage_name: Name of the stage
            error: Error message
            document_id: Document identifier for composite key
        """
        with self._lock:
            batch_key = f"{document_id}:{batch_id}" if document_id else str(batch_id)
            batch = self._batches.get(batch_key)
            if batch and stage_name in batch.stages:
                batch.stages[stage_name].status = StageStatus.FAILED

            line = Text()
            line.append("    ├── ", style="dim")
            line.append(f"✗ {stage_name}", style="red bold")
            line.append(f" FAILED: {error}", style="red")

            self.console.print(line)

    def batch_completed(
        self, batch_id: int, num_pages_in_batch: int, document_id: str = ""
    ):
        """Mark a batch as fully completed.

        Args:
            batch_id: Batch identifier (per-document)
            num_pages_in_batch: Number of pages in this batch
            document_id: Document identifier for composite key
        """
        with self._lock:
            batch_key = f"{document_id}:{batch_id}" if document_id else str(batch_id)
            batch = self._batches.get(batch_key)
            if not batch:
                return

            # Update completed pages
            self._completed_pages += num_pages_in_batch

            # Use the stored global batch number (1-indexed for display)
            display_batch = batch.batch_id + 1

            # Print completion line
            line = Text()
            line.append("    └── ", style="dim")
            line.append("✓ ", style="green bold")
            line.append(f"Batch {display_batch} complete", style="green")
            line.append(
                f" ({self._completed_pages}/{self._total_pages} pages)", style="dim"
            )

            self.console.print(line)
            self.console.print()  # Blank line between batches

    def document_completed(self, total_pages: int, total_time_s: float):
        """Announce processing completion.

        Args:
            total_pages: Total pages processed
            total_time_s: Total processing time in seconds
        """
        with self._lock:
            # Create completion panel
            summary = Table.grid(padding=(0, 2))
            summary.add_column(style="bold")
            summary.add_column()

            # Show document(s) info
            if len(self._documents) == 1:
                summary.add_row("✓ Document", self._documents[0])
            elif self._documents:
                summary.add_row("✓ Documents", str(len(self._documents)))

            summary.add_row("📄 Pages", str(total_pages))
            summary.add_row("⏱️  Time", f"{total_time_s:.1f}s")
            summary.add_row(
                "📊 Rate",
                (
                    f"{total_pages / total_time_s:.1f} pages/sec"
                    if total_time_s > 0
                    else "N/A"
                ),
            )

            self.console.print()
            self.console.print(
                Panel(
                    summary,
                    title="[green bold]Processing Complete[/]",
                    border_style="green",
                )
            )

            # Reset state for next job
            self._initialized = False

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
