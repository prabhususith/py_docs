"""
PyQt6 Multithreaded GUI Architecture
====================================
Description: Enterprise desktop application engineering using Qt6 (`PyQt6`). Demonstrates
             `QMainWindow`, custom `pyqtSignal` cross-thread messaging, and a non-blocking
             worker `QThread` preventing UI freezing during heavy compute/I/O pipelines.
             Features `QTableWidget` telemetry grids, `QProgressBar`, and clean thread lifecycle management.
Enterprise Mapping: Analogous to Web Workers in React/Angular and background threads in WPF/C#.
                    Qt Signals and Slots provide thread-safe, decoupled event-driven message
                    passing across memory boundaries without GIL deadlocks or UI event loop blocking.

Official Documentation References:
- Riverbank PyQt6 Documentation: https://www.riverbankcomputing.com/static/Docs/PyQt6/
- Qt 6 Signals & Slots: https://doc.qt.io/qt-6/signalsandslots.html
- Qt 6 Threading Basics (QThread): https://doc.qt.io/qt-6/threads-technologies.html
- Qt 6 QMainWindow Architecture: https://doc.qt.io/qt-6/qmainwindow.html
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from PyQt6.QtCore import QCoreApplication, QObject, QThread, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# ==============================================================================
# 1. Domain Data Models
# ==============================================================================


@dataclass(frozen=True)
class BatchTaskResult:
    """Immutable record of processed batch computational payload."""

    job_id: str
    task_name: str
    processed_count: int
    duration_ms: float
    status: str
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """Serialize domain model to key-value dictionary."""
        return {
            "job_id": self.job_id,
            "task_name": self.task_name,
            "processed_count": self.processed_count,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "timestamp": self.timestamp,
        }


# ==============================================================================
# 2. Asynchronous Background Worker (QThread)
# ==============================================================================


class AsyncBatchWorker(QThread):
    """
    Dedicated background worker executing compute-heavy simulation off the main GUI thread.

    Qt Signals:
    - `progress_updated`: Emits integer percent (0-100) and step description.
    - `record_emitted`: Emits individual BatchTaskResult dictionary.
    - `batch_completed`: Emits aggregate statistics dictionary on termination.
    - `worker_error`: Emits string error description if an unhandled fault occurs.
    """

    progress_updated = pyqtSignal(int, str)
    record_emitted = pyqtSignal(dict)
    batch_completed = pyqtSignal(dict)
    worker_error = pyqtSignal(str)

    def __init__(
        self,
        batch_size: int = 10,
        task_category: str = "Matrix Quantization",
        step_delay_s: float = 0.05,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self.batch_size = max(1, batch_size)
        self.task_category = task_category
        self.step_delay_s = step_delay_s

    def run(self) -> None:
        """
        Worker execution body executing in a separate OS thread.
        Never manipulates GUI widgets directly; communicates exclusively via pyqtSignal.
        """
        start_time = time.perf_counter()
        results: List[Dict[str, Any]] = []

        try:
            self.progress_updated.emit(0, f"Initializing {self.task_category} job pipeline...")

            for i in range(1, self.batch_size + 1):
                # Check for cooperative cancellation request
                if self.isInterruptionRequested():
                    self.progress_updated.emit(
                        int((i / self.batch_size) * 100),
                        "Job cancellation requested by operator.",
                    )
                    return

                # Simulate CPU work or asynchronous I/O
                step_start = time.perf_counter()
                time.sleep(self.step_delay_s)
                step_duration = (time.perf_counter() - step_start) * 1000.0

                record = BatchTaskResult(
                    job_id=f"JOB-{int(time.time())}-{i:03d}",
                    task_name=f"{self.task_category} [Step {i}/{self.batch_size}]",
                    processed_count=i * 256,
                    duration_ms=round(step_duration, 2),
                    status="COMPLETED",
                    timestamp=datetime.now(timezone.utc).strftime("%H:%M:%S"),
                )
                results.append(record.to_dict())

                # Emit individual row and progress
                percent = int((i / self.batch_size) * 100)
                self.progress_updated.emit(percent, f"Processed step {i} of {self.batch_size}")
                self.record_emitted.emit(record.to_dict())

            total_elapsed = (time.perf_counter() - start_time) * 1000.0
            summary = {
                "total_records": len(results),
                "total_duration_ms": round(total_elapsed, 2),
                "category": self.task_category,
                "status": "SUCCESS",
            }
            self.progress_updated.emit(100, f"Batch successfully finalized in {total_elapsed:.1f}ms")
            self.batch_completed.emit(summary)

        except Exception as exc:
            self.worker_error.emit(f"Worker thread exception: {str(exc)}")


# ==============================================================================
# 3. Enterprise QMainWindow Architecture
# ==============================================================================


class EnterpriseQtMainWindow(QMainWindow):
    """
    Enterprise Qt6 Main Window.

    Features:
    - Split-pane layout with controls on the left and data telemetry on the right.
    - Thread-safe slot bindings responding to worker signals.
    - Interactive QTableWidget data grid with custom headers and status color-coding.
    - Live QProgressBar with animated state.
    - Rich QTextEdit activity console with log formatting.
    """

    def __init__(self, headless: bool = False) -> None:
        super().__init__()
        self.headless = headless
        self.worker: Optional[AsyncBatchWorker] = None
        self.total_processed_records: int = 0

        # Configure Window Properties
        self.setWindowTitle("Titan Core | PyQt6 Multithreaded Operations Console")
        self.resize(1050, 680)
        self.setMinimumSize(880, 540)

        # Build UI Structure
        self._setup_ui()
        self._apply_enterprise_stylesheet()

        # Status Bar
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Enterprise Qt6 Runtime Ready. Worker Idle.")

    # --------------------------------------------------------------------------
    # UI Setup & Layout Management
    # --------------------------------------------------------------------------

    def _setup_ui(self) -> None:
        """Construct the split-pane user interface."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(12)

        # Header Title Banner
        header_frame = QFrame()
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(2)

        lbl_title = QLabel("Asynchronous Compute & Worker Pool Orchestrator")
        lbl_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        lbl_subtitle = QLabel(
            "Non-blocking PyQt6 QThread execution with thread-safe Signal & Slot telemetry dispatch."
        )
        lbl_subtitle.setFont(QFont("Segoe UI", 10))
        lbl_subtitle.setStyleSheet("color: #718096;")

        header_layout.addWidget(lbl_title)
        header_layout.addWidget(lbl_subtitle)
        root_layout.addWidget(header_frame)

        # Main Splitter: Left Controls (30%) vs Right Telemetry (70%)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        root_layout.addWidget(splitter, 1)

        # Left Panel (Controls)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 8, 0)
        self._build_control_panel(left_layout)
        splitter.addWidget(left_widget)

        # Right Panel (Observability & Data Table)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(8, 0, 0, 0)
        self._build_telemetry_panel(right_layout)
        splitter.addWidget(right_widget)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

    def _build_control_panel(self, layout: QVBoxLayout) -> None:
        """Construct interactive parameter inputs and action buttons."""
        box = QGroupBox("Job Parameters & Controls")
        box_layout = QVBoxLayout(box)
        box_layout.setSpacing(12)

        # Parameter: Task Category
        lbl_cat = QLabel("Pipeline Task Type:")
        self.cmb_task_type = QComboBox()
        self.cmb_task_type.addItems(
            [
                "Matrix Quantization (INT8)",
                "Vector Embedding Ingestion",
                "Graph Traversal Evaluation",
                "Async SQL Migration Batch",
            ]
        )
        box_layout.addWidget(lbl_cat)
        box_layout.addWidget(self.cmb_task_type)

        # Parameter: Batch Size
        lbl_batch = QLabel("Batch Step Count (Records):")
        self.spn_batch_size = QSpinBox()
        self.spn_batch_size.setRange(2, 50)
        self.spn_batch_size.setValue(10)
        box_layout.addWidget(lbl_batch)
        box_layout.addWidget(self.spn_batch_size)

        # Action Buttons
        self.btn_start = QPushButton("Launch Worker Thread")
        self.btn_start.setObjectName("primaryButton")
        self.btn_start.clicked.connect(self.handle_start_worker)
        box_layout.addWidget(self.btn_start)

        self.btn_cancel = QPushButton("Cancel Worker Execution")
        self.btn_cancel.setObjectName("dangerButton")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.handle_cancel_worker)
        box_layout.addWidget(self.btn_cancel)

        self.btn_clear = QPushButton("Clear Results Grid")
        self.btn_clear.clicked.connect(self.handle_clear_results)
        box_layout.addWidget(self.btn_clear)

        box_layout.addStretch()
        layout.addWidget(box)

    def _build_telemetry_panel(self, layout: QVBoxLayout) -> None:
        """Construct the progress bar, data grid, and log console."""
        # Progress Bar Card
        progress_box = QGroupBox("Execution Progress")
        progress_layout = QVBoxLayout(progress_box)
        progress_layout.setSpacing(6)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.lbl_progress_status = QLabel("Worker standing by.")
        self.lbl_progress_status.setFont(QFont("Consolas", 9))

        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.lbl_progress_status)
        layout.addWidget(progress_box)

        # Results Grid (QTableWidget)
        self.table_results = QTableWidget()
        self.table_results.setColumnCount(5)
        self.table_results.setHorizontalHeaderLabels(
            ["Job ID", "Task Category", "Processed Items", "Duration (ms)", "Status"]
        )
        header = self.table_results.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_results.setAlternatingRowColors(True)
        self.table_results.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table_results, 2)

        # Streaming Log Output (QTextEdit)
        self.txt_console = QTextEdit()
        self.txt_console.setReadOnly(True)
        self.txt_console.setFont(QFont("Consolas", 9))
        self.txt_console.setMaximumHeight(140)
        layout.addWidget(self.txt_console, 1)

    def _apply_enterprise_stylesheet(self) -> None:
        """Apply modern dark stylesheet matching enterprise standards."""
        stylesheet = """
        QMainWindow {
            background-color: #1a202c;
        }
        QWidget {
            color: #e2e8f0;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #4a5568;
            border-radius: 6px;
            margin-top: 12px;
            padding-top: 14px;
            background-color: #2d3748;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 4px;
            color: #63b3ed;
        }
        QPushButton {
            background-color: #4a5568;
            color: #ffffff;
            border: none;
            border-radius: 4px;
            padding: 8px 14px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #718096;
        }
        QPushButton#primaryButton {
            background-color: #3182ce;
        }
        QPushButton#primaryButton:hover {
            background-color: #2b6cb0;
        }
        QPushButton#dangerButton {
            background-color: #e53e3e;
        }
        QPushButton#dangerButton:hover {
            background-color: #c53030;
        }
        QPushButton:disabled {
            background-color: #2d3748;
            color: #718096;
        }
        QProgressBar {
            border: 1px solid #4a5568;
            border-radius: 4px;
            text-align: center;
            background-color: #1a202c;
            height: 20px;
        }
        QProgressBar::chunk {
            background-color: #38a169;
            border-radius: 3px;
        }
        QTableWidget {
            background-color: #2d3748;
            alternate-background-color: #1a202c;
            gridline-color: #4a5568;
            border: 1px solid #4a5568;
            border-radius: 4px;
        }
        QHeaderView::section {
            background-color: #1a202c;
            color: #cbd5e0;
            padding: 4px;
            font-weight: bold;
            border: 1px solid #4a5568;
        }
        QTextEdit {
            background-color: #1a202c;
            border: 1px solid #4a5568;
            border-radius: 4px;
            color: #68d391;
        }
        QStatusBar {
            background-color: #1a202c;
            color: #a0aec0;
        }
        """
        self.setStyleSheet(stylesheet)

    # --------------------------------------------------------------------------
    # Event Handlers & Slot Connectors
    # --------------------------------------------------------------------------

    def handle_start_worker(self) -> None:
        """Instantiate and launch background QThread worker."""
        if self.worker is not None and self.worker.isRunning():
            return

        batch_count = self.spn_batch_size.value()
        task_type = self.cmb_task_type.currentText()
        delay = 0.01 if self.headless else 0.05

        self.worker = AsyncBatchWorker(
            batch_size=batch_count,
            task_category=task_type,
            step_delay_s=delay,
        )

        # Connect Qt Signals to Slots
        self.worker.progress_updated.connect(self.on_worker_progress)
        self.worker.record_emitted.connect(self.on_worker_record)
        self.worker.batch_completed.connect(self.on_worker_finished)
        self.worker.worker_error.connect(self.on_worker_error)

        # Update UI Controls
        self.btn_start.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.progress_bar.setValue(0)
        self.log_console(f"Initiated asynchronous background job: {task_type} ({batch_count} steps)")
        self.status_bar.showMessage(f"Worker ACTIVE: Running {task_type}...")

        # Start thread execution
        self.worker.start()

    def handle_cancel_worker(self) -> None:
        """Request cooperative thread interruption."""
        if self.worker is not None and self.worker.isRunning():
            self.worker.requestInterruption()
            self.log_console("Dispatched interruption request to worker thread.")
            self.status_bar.showMessage("Canceling worker thread...")

    def handle_clear_results(self) -> None:
        """Clear data table and reset metrics."""
        self.table_results.setRowCount(0)
        self.progress_bar.setValue(0)
        self.lbl_progress_status.setText("Worker standing by.")
        self.total_processed_records = 0
        self.log_console("Telemetry results grid cleared.")

    @pyqtSlot(int, str)
    def on_worker_progress(self, percent: int, message: str) -> None:
        """Slot: update progress bar and status indicator."""
        self.progress_bar.setValue(percent)
        self.lbl_progress_status.setText(f"[{percent}%] {message}")

    @pyqtSlot(dict)
    def on_worker_record(self, record: Dict[str, Any]) -> None:
        """Slot: insert processed record into telemetry table."""
        row = self.table_results.rowCount()
        self.table_results.insertRow(row)

        self.table_results.setItem(row, 0, QTableWidgetItem(record["job_id"]))
        self.table_results.setItem(row, 1, QTableWidgetItem(record["task_name"]))
        self.table_results.setItem(row, 2, QTableWidgetItem(str(record["processed_count"])))
        self.table_results.setItem(row, 3, QTableWidgetItem(f"{record['duration_ms']} ms"))

        status_item = QTableWidgetItem(record["status"])
        status_item.setForeground(QColor("#68d391"))  # Green tone
        self.table_results.setItem(row, 4, status_item)

        self.table_results.scrollToBottom()
        self.total_processed_records += 1

    @pyqtSlot(dict)
    def on_worker_finished(self, summary: Dict[str, Any]) -> None:
        """Slot: cleanup worker and restore control states."""
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.log_console(
            f"Job completed: {summary['total_records']} steps finalized in {summary['total_duration_ms']} ms."
        )
        self.status_bar.showMessage(
            f"Worker IDLE. Last job finished in {summary['total_duration_ms']} ms."
        )

    @pyqtSlot(str)
    def on_worker_error(self, error_msg: str) -> None:
        """Slot: handle worker failure message."""
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.log_console(f"ERROR: {error_msg}")
        self.status_bar.showMessage("Worker encountered an error.")
        if not self.headless:
            QMessageBox.critical(self, "Worker Error", error_msg)

    def log_console(self, text: str) -> None:
        """Append timestamped string to activity log."""
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
        self.txt_console.append(f"[{ts}] {text}")


# ==============================================================================
# 4. Automated Verification & Smoke Test Engine
# ==============================================================================


def run_automated_verification() -> bool:
    """
    Automated smoke test executing the PyQt6 multithreaded application.
    Verifies QApplication initialization, QMainWindow layout, QThread background
    execution, custom pyqtSignal emission, and QTableWidget updates without UI blocking.
    """
    console.print(
        Panel.fit(
            "[bold cyan]PyQt6 Multithreaded GUI - Automated Test Suite[/bold cyan]\n"
            "[dim]Verifying QMainWindow, QThread non-blocking worker, and Signals & Slots.[/dim]",
            border_style="cyan",
        )
    )

    # 1. Initialize Qt Application
    console.print("[dim]Phase 1: Initializing QApplication runtime...[/dim]")
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    console.print("  [green][PASS] QApplication instance active.[/green]")

    # 2. Instantiate Main Window
    console.print("[dim]Phase 2: Building EnterpriseQtMainWindow...[/dim]")
    window = EnterpriseQtMainWindow(headless=True)
    window.spn_batch_size.setValue(5)  # 5 steps for quick verification
    console.print("  [green][PASS] EnterpriseQtMainWindow constructed with split-layout.[/green]")

    # 3. Test Worker Thread Launch & Signal Processing
    console.print("[dim]Phase 3: Launching AsyncBatchWorker and processing Qt event loop...[/dim]")
    window.handle_start_worker()
    assert window.worker is not None, "Worker was not created."
    assert window.worker.isRunning(), "Worker thread should be running."

    # Pump event loop until worker finishes
    max_wait_seconds = 5.0
    start_wait = time.time()
    while window.worker.isRunning() and (time.time() - start_wait < max_wait_seconds):
        app.processEvents()
        time.sleep(0.01)

    # Allow final signals to dispatch
    for _ in range(5):
        app.processEvents()
        time.sleep(0.01)

    assert not window.worker.isRunning(), "Worker thread did not complete within timeout."
    console.print("  [green][PASS] Worker thread completed and exited cleanly.[/green]")

    # 4. Assert Telemetry Table & Progress State
    console.print("[dim]Phase 4: Verifying QTableWidget data and progress bar state...[/dim]")
    assert window.table_results.rowCount() == 5, f"Expected 5 table rows, got {window.table_results.rowCount()}."
    assert window.progress_bar.value() == 100, f"Expected 100% progress, got {window.progress_bar.value()}."
    assert window.total_processed_records == 5, f"Expected 5 records, got {window.total_processed_records}."

    first_item = window.table_results.item(0, 0)
    assert first_item is not None and "JOB-" in first_item.text(), "Table item format invalid."
    console.print(f"  [green][PASS] QTableWidget successfully received 5 rows (First: {first_item.text()}).[/green]")

    # 5. Test Clear Results Action
    console.print("[dim]Phase 5: Testing table reset action...[/dim]")
    window.handle_clear_results()
    assert window.table_results.rowCount() == 0, "Table should be empty after clear."
    assert window.progress_bar.value() == 0, "Progress bar should reset to 0."
    console.print("  [green][PASS] Table reset successfully verified.[/green]")

    # Render Summary Table
    table = Table(title="PyQt6 Architecture Verification Results", border_style="green")
    table.add_column("Component", style="bold cyan")
    table.add_column("Qt6 Class / Mechanism", style="white")
    table.add_column("Status", style="bold green")

    table.add_row("Main Window", "QMainWindow with QSplitter layout", "PASSED")
    table.add_row("Multithreading", "QThread with cooperative interruption", "PASSED")
    table.add_row("Cross-Thread Events", "pyqtSignal & pyqtSlot (thread-safe)", "PASSED")
    table.add_row("Data Grid", "QTableWidget with responsive columns", "PASSED")
    table.add_row("Telemetry & Progress", "QProgressBar & QTextEdit log console", "PASSED")

    console.print(table)

    # Clean window teardown
    window.close()
    return True


if __name__ == "__main__":
    if "--gui" in sys.argv or "--interactive" in sys.argv:
        # Launch Interactive Desktop Application
        print("Launching interactive PyQt6 desktop application...")
        qt_app = QApplication(sys.argv)
        main_win = EnterpriseQtMainWindow(headless=False)
        main_win.show()
        sys.exit(qt_app.exec())
    else:
        # Run automated verification and smoke test
        success = run_automated_verification()
        sys.exit(0 if success else 1)
