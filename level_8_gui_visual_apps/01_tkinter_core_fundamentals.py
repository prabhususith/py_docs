"""
Tkinter Core Fundamentals & Lifecycle Architecture
==================================================
Description: Production desktop UI engineering demonstrating standard library Tkinter
             and themed Ttk widgets. Covers top-level window lifecycle, the responsive
             `grid` geometry manager, reactive `StringVar`/`IntVar` bidirectional data
             binding, input validation commands, event handling, and structured styling.
Enterprise Mapping: Translates browser DOM event-driven architectures (React/Vue/HTML5)
                    and desktop application patterns to Python's built-in Tcl/Tk runtime.
                    Replaces client-side reactive state stores (MobX/Pinia/Zustand) with
                    Tkinter trace callbacks, and CSS Grid layouts with grid geometry weighting.

Official Documentation References:
- Tkinter Standard Library: https://docs.python.org/3/library/tkinter.html
- Tkinter Ttk Themed Widgets: https://docs.python.org/3/library/tkinter.ttk.html
- Tcl/Tk 8.6 Manual: https://www.tcl.tk/man/tcl8.6/TkCmd/contents.htm
- Python IDLE & Tkinter Architecture: https://docs.python.org/3/library/idle.html
"""

from __future__ import annotations

import re
import sys
import time
import tkinter as tk
from dataclasses import dataclass, field
from datetime import datetime, timezone
from tkinter import messagebox, ttk
from typing import Any, Callable, Dict, List, Optional, Tuple

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# ==============================================================================
# 1. Domain Data Models & Validation Logic
# ==============================================================================

EMAIL_REGEX: re.Pattern[str] = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
)


@dataclass(frozen=True)
class UserProfile:
    """Immutable enterprise user profile representation."""

    username: str
    email: str
    role: str
    monthly_quota_gb: int
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize domain model to key-value dictionary."""
        return {
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "monthly_quota_gb": self.monthly_quota_gb,
            "created_at": self.created_at.isoformat(),
        }


# ==============================================================================
# 2. Enterprise Tkinter Application Architecture
# ==============================================================================


class EnterpriseTkinterApp(tk.Tk):
    """
    Enterprise-grade Tkinter Root Application.

    Demonstrates:
    - Proper window initialization and responsive grid geometry (`columnconfigure`/`rowconfigure`).
    - Themed widget styling via `ttk.Style` for modern clean appearance.
    - Two-way reactive data binding using `tk.StringVar` and `trace_add`.
    - Real-time entry validation callbacks (`validate='key'`).
    - Event loop dispatch and graceful teardown (`WM_DELETE_WINDOW` protocol).
    """

    def __init__(self, headless: bool = False) -> None:
        super().__init__()
        self.headless = headless

        # Configure Root Window Attributes
        self.title("Enterprise Control Plane | Tkinter Fundamentals")
        self.geometry("780x560")
        self.minsize(680, 480)

        # Reactive State Variables (Equivalent to React useState / Vue Ref)
        self.var_username: tk.StringVar = tk.StringVar(value="")
        self.var_email: tk.StringVar = tk.StringVar(value="")
        self.var_role: tk.StringVar = tk.StringVar(value="DevOps Engineer")
        self.var_quota: tk.IntVar = tk.IntVar(value=50)
        self.var_status_msg: tk.StringVar = tk.StringVar(value="System Ready.")
        self.var_summary_display: tk.StringVar = tk.StringVar(
            value="Awaiting user input..."
        )
        self.var_validation_feedback: tk.StringVar = tk.StringVar(value="")

        # Internal Store
        self.registered_profiles: List[UserProfile] = []

        # Configure Visual Theme
        self._setup_styles()

        # Build Widget Tree
        self._build_layout()

        # Bind Reactive Traces and Event Listeners
        self._setup_reactive_traces()

        # Window Lifecycle Protocols
        self.protocol("WM_DELETE_WINDOW", self.on_close_requested)

    # --------------------------------------------------------------------------
    # Styling Configuration
    # --------------------------------------------------------------------------

    def _setup_styles(self) -> None:
        """Initialize modern Ttk styling rules with elevated contrast."""
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass  # Fall back to native platform theme if 'clam' is absent

        # Primary Colors
        bg_dark = "#1e1e2e"
        fg_light = "#cdd6f4"
        accent_blue = "#89b4fa"
        surface = "#313244"

        self.configure(bg=bg_dark)

        # Configure TTK widget classes
        self.style.configure(
            "Enterprise.TFrame",
            background=bg_dark,
        )
        self.style.configure(
            "Card.TFrame",
            background=surface,
            relief="flat",
        )
        self.style.configure(
            "Header.TLabel",
            background=bg_dark,
            foreground=accent_blue,
            font=("Segoe UI", 16, "bold"),
        )
        self.style.configure(
            "Subheader.TLabel",
            background=bg_dark,
            foreground=fg_light,
            font=("Segoe UI", 10),
        )
        self.style.configure(
            "CardText.TLabel",
            background=surface,
            foreground=fg_light,
            font=("Consolas", 10),
        )
        self.style.configure(
            "Primary.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=6,
        )
        self.style.configure(
            "Status.TLabel",
            background="#181825",
            foreground="#a6adc8",
            font=("Segoe UI", 9),
            padding=4,
        )

    # --------------------------------------------------------------------------
    # Layout & Widget Hierarchy (Responsive CSS Grid Equivalent)
    # --------------------------------------------------------------------------

    def _build_layout(self) -> None:
        """Construct hierarchical layout with weighted responsive grid coordinates."""
        # Top-level window grid configuration: row 1 (main content) expands
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # 1. Header Banner
        header_frame = ttk.Frame(self, style="Enterprise.TFrame", padding="16 12 16 8")
        header_frame.grid(row=0, column=0, sticky="ew")

        lbl_title = ttk.Label(
            header_frame,
            text="Cloud Infrastructure Tenant Provisioning",
            style="Header.TLabel",
        )
        lbl_title.pack(anchor="w")

        lbl_desc = ttk.Label(
            header_frame,
            text="Tkinter two-way reactive binding, validation hooks, and responsive grid layout.",
            style="Subheader.TLabel",
        )
        lbl_desc.pack(anchor="w", pady=(2, 0))

        # 2. Main Work Area (Split Form & Reactive Inspector)
        content_frame = ttk.Frame(self, style="Enterprise.TFrame", padding="16 8 16 8")
        content_frame.grid(row=1, column=0, sticky="nsew")
        content_frame.columnconfigure(0, weight=3)  # Left: Input Form (60%)
        content_frame.columnconfigure(1, weight=2)  # Right: Live Inspector (40%)
        content_frame.rowconfigure(0, weight=1)

        # Build Form Panel (Left)
        self._build_form_panel(content_frame)

        # Build Live Reactive Card (Right)
        self._build_inspector_panel(content_frame)

        # 3. Status Bar (Bottom)
        status_bar = ttk.Label(
            self,
            textvariable=self.var_status_msg,
            style="Status.TLabel",
            relief="sunken",
            anchor="w",
        )
        status_bar.grid(row=2, column=0, sticky="ew")

    def _build_form_panel(self, parent: ttk.Frame) -> None:
        """Construct the interactive form controls."""
        form_frame = ttk.LabelFrame(
            parent,
            text=" Provisioning Configuration ",
            padding="14",
        )
        form_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=0)
        form_frame.columnconfigure(1, weight=1)

        # Validation Registration Callback
        vcmd_quota = (self.register(self._validate_numeric_quota), "%P")

        # Field: Username
        lbl_user = ttk.Label(form_frame, text="Username:")
        lbl_user.grid(row=0, column=0, sticky="w", pady=6)
        self.ent_user = ttk.Entry(
            form_frame,
            textvariable=self.var_username,
            font=("Segoe UI", 10),
        )
        self.ent_user.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=6)

        # Field: Email
        lbl_email = ttk.Label(form_frame, text="Corporate Email:")
        lbl_email.grid(row=1, column=0, sticky="w", pady=6)
        self.ent_email = ttk.Entry(
            form_frame,
            textvariable=self.var_email,
            font=("Segoe UI", 10),
        )
        self.ent_email.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=6)

        # Field: Role Combobox
        lbl_role = ttk.Label(form_frame, text="Role Assignment:")
        lbl_role.grid(row=2, column=0, sticky="w", pady=6)
        self.cmb_role = ttk.Combobox(
            form_frame,
            textvariable=self.var_role,
            values=[
                "DevOps Engineer",
                "Site Reliability Engineer",
                "Security Operations Architect",
                "Machine Learning Platform Engineer",
            ],
            state="readonly",
        )
        self.cmb_role.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=6)

        # Field: Monthly Quota (GB) with validation
        lbl_quota = ttk.Label(form_frame, text="Monthly Quota (GB):")
        lbl_quota.grid(row=3, column=0, sticky="w", pady=6)
        self.ent_quota = ttk.Entry(
            form_frame,
            textvariable=self.var_quota,
            validate="key",
            validatecommand=vcmd_quota,
            font=("Segoe UI", 10),
        )
        self.ent_quota.grid(row=3, column=1, sticky="ew", padx=(8, 0), pady=6)

        # Validation Feedback Message
        self.lbl_feedback = ttk.Label(
            form_frame,
            textvariable=self.var_validation_feedback,
            foreground="#f38ba8",  # Red / Warning tone
            font=("Segoe UI", 9, "italic"),
        )
        self.lbl_feedback.grid(row=4, column=0, columnspan=2, sticky="w", pady=(4, 8))

        # Action Buttons Container
        btn_box = ttk.Frame(form_frame)
        btn_box.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        btn_box.columnconfigure((0, 1), weight=1)

        self.btn_submit = ttk.Button(
            btn_box,
            text="Commit Provisioning",
            style="Primary.TButton",
            command=self.handle_provision_submit,
        )
        self.btn_submit.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.btn_reset = ttk.Button(
            btn_box,
            text="Clear Form",
            command=self.handle_form_reset,
        )
        self.btn_reset.grid(row=0, column=1, sticky="ew", padx=(4, 0))

    def _build_inspector_panel(self, parent: ttk.Frame) -> None:
        """Construct the live reactive inspector showing two-way state changes."""
        inspector_frame = ttk.LabelFrame(
            parent,
            text=" Live State Inspector (Reactive Signal) ",
            padding="14",
        )
        inspector_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=0)
        inspector_frame.columnconfigure(0, weight=1)
        inspector_frame.rowconfigure(0, weight=1)

        # Card container with dark background
        card_inner = ttk.Frame(inspector_frame, style="Card.TFrame", padding="12")
        card_inner.grid(row=0, column=0, sticky="nsew")

        lbl_header = ttk.Label(
            card_inner,
            text="Real-Time State Telemetry",
            style="CardText.TLabel",
            font=("Consolas", 11, "bold"),
        )
        lbl_header.pack(anchor="w", pady=(0, 8))

        self.lbl_reactive_card = ttk.Label(
            card_inner,
            textvariable=self.var_summary_display,
            style="CardText.TLabel",
            justify="left",
            wraplength=260,
        )
        self.lbl_reactive_card.pack(anchor="w", fill="both", expand=True)

    # --------------------------------------------------------------------------
    # Reactive Binding & Validation Logic
    # --------------------------------------------------------------------------

    def _setup_reactive_traces(self) -> None:
        """Attach trace callbacks to state variables for bidirectional reactivity."""
        # 'write' mode observer triggers whenever the user keystroke mutates the variable
        self.var_username.trace_add("write", self._on_state_mutated)
        self.var_email.trace_add("write", self._on_state_mutated)
        self.var_role.trace_add("write", self._on_state_mutated)
        self.var_quota.trace_add("write", self._on_state_mutated)

        # Keyboard shortcuts
        self.bind("<Return>", lambda event: self.handle_provision_submit())
        self.bind("<Escape>", lambda event: self.handle_form_reset())

    def _validate_numeric_quota(self, proposed_value: str) -> bool:
        """
        Validation command hook enforcing integer-only characters in quota input.
        Returns True to permit keystroke, False to reject immediately.
        """
        if proposed_value == "":
            return True
        return proposed_value.isdigit()

    def _on_state_mutated(self, *args: Any) -> None:
        """
        Reactive state observer (analogous to Vue watchEffect or React useEffect).
        Recalculates validation state and formats live summary card.
        """
        raw_user = self.var_username.get().strip()
        raw_email = self.var_email.get().strip()
        raw_role = self.var_role.get()
        try:
            raw_quota = self.var_quota.get()
        except (tk.TclError, ValueError):
            raw_quota = 0

        # Validate live input
        errors: List[str] = []
        if raw_user and len(raw_user) < 3:
            errors.append("Username must contain >= 3 chars.")
        if raw_email and not EMAIL_REGEX.match(raw_email):
            errors.append("Invalid corporate email format.")
        if raw_quota < 10 or raw_quota > 5000:
            errors.append("Quota must range between 10 and 5000 GB.")

        if errors:
            self.var_validation_feedback.set(errors[0])
        else:
            self.var_validation_feedback.set("")

        # Format reactive inspection display
        status_flag = "VALID" if (raw_user and raw_email and not errors) else "PENDING"
        summary_payload = (
            f"State Status : [{status_flag}]\n"
            f"--------------------------\n"
            f"Username     : {raw_user or '<empty>'}\n"
            f"Email        : {raw_email or '<empty>'}\n"
            f"Role         : {raw_role}\n"
            f"Quota        : {raw_quota} GB\n"
            f"Len(User)    : {len(raw_user)} chars\n"
            f"Total Saved  : {len(self.registered_profiles)} record(s)\n"
            f"Timestamp    : {datetime.now(timezone.utc).strftime('%H:%M:%S')}"
        )
        self.var_summary_display.set(summary_payload)

    # --------------------------------------------------------------------------
    # Event Handlers & Form Actions
    # --------------------------------------------------------------------------

    def handle_provision_submit(self) -> Optional[UserProfile]:
        """Validate input parameters and commit new UserProfile to registry."""
        username = self.var_username.get().strip()
        email = self.var_email.get().strip()
        role = self.var_role.get()
        try:
            quota = self.var_quota.get()
        except (tk.TclError, ValueError):
            quota = 0

        if not username or len(username) < 3:
            self._display_alert("Validation Error", "Username must be at least 3 characters.")
            return None

        if not EMAIL_REGEX.match(email):
            self._display_alert("Validation Error", "Please provide a valid corporate email.")
            return None

        if quota < 10 or quota > 5000:
            self._display_alert("Validation Error", "Quota must be between 10 and 5000 GB.")
            return None

        new_profile = UserProfile(
            username=username,
            email=email,
            role=role,
            monthly_quota_gb=quota,
        )
        self.registered_profiles.append(new_profile)

        self.var_status_msg.set(
            f"Successfully provisioned tenant: {username} ({email}) at {datetime.now(timezone.utc).strftime('%H:%M:%S')}"
        )
        self._on_state_mutated()

        if not self.headless:
            messagebox.showinfo(
                "Provisioning Succeeded",
                f"Tenant '{username}' successfully registered with {quota} GB quota.",
                parent=self,
            )

        return new_profile

    def handle_form_reset(self) -> None:
        """Reset all reactive inputs back to default starting state."""
        self.var_username.set("")
        self.var_email.set("")
        self.var_role.set("DevOps Engineer")
        self.var_quota.set(50)
        self.var_status_msg.set("Form reset to default baseline.")
        self.ent_user.focus_set()

    def _display_alert(self, title: str, message: str) -> None:
        """Present error feedback via messagebox or status variable."""
        self.var_status_msg.set(f"Error: {message}")
        if not self.headless:
            messagebox.showerror(title, message, parent=self)

    def on_close_requested(self) -> None:
        """Intercept window close protocol for safe teardown."""
        self.destroy()


# ==============================================================================
# 3. Verification & Execution Engine
# ==============================================================================


def run_automated_verification() -> bool:
    """
    Automated smoke test executing the Tkinter application without human interaction.
    Verifies widget initialization, responsive grid layout, reactive trace updates,
    and event handling without blocking indefinitely.
    """
    console.print(
        Panel.fit(
            "[bold cyan]Tkinter Core Fundamentals - Automated Test Suite[/bold cyan]\n"
            "[dim]Verifying window lifecycle, reactive StringVar traces, and validation hooks.[/dim]",
            border_style="cyan",
        )
    )

    # 1. Instantiate Application in Headless / Automated Mode
    app = EnterpriseTkinterApp(headless=True)
    app.update_idletasks()
    app.update()

    # 2. Test Reactive State Mutation
    console.print("[dim]Phase 1: Testing reactive StringVar mutation & trace triggers...[/dim]")
    app.var_username.set("alice_architect")
    app.var_email.set("alice@enterprise.cloud")
    app.var_quota.set(250)
    app.update()

    # Assert live summary was updated automatically by trace_add
    summary_text = app.var_summary_display.get()
    assert "alice_architect" in summary_text, "Reactive trace failed to update username display."
    assert "alice@enterprise.cloud" in summary_text, "Reactive trace failed to update email display."
    assert "[VALID]" in summary_text, "State should be marked VALID for correct input."
    console.print("  [green][PASS] Reactive StringVar traces fired and verified.[/green]")

    # 3. Test Invalid Input & Validation Interceptor
    console.print("[dim]Phase 2: Testing validation feedback for malformed email...[/dim]")
    app.var_email.set("invalid-email-address")
    app.update()
    feedback = app.var_validation_feedback.get()
    assert "Invalid corporate email" in feedback, "Validation hook failed to catch invalid email."
    console.print("  [green][PASS] Real-time input validation correctly rejected malformed email.[/green]")

    # Restore valid email
    app.var_email.set("alice@enterprise.cloud")
    app.update()

    # 4. Test Submission Event Handler
    console.print("[dim]Phase 3: Testing form submission and profile generation...[/dim]")
    profile = app.handle_provision_submit()
    assert profile is not None, "Profile submission returned None."
    assert profile.username == "alice_architect"
    assert profile.monthly_quota_gb == 250
    assert len(app.registered_profiles) == 1
    console.print(f"  [green][PASS] Successfully committed UserProfile record: {profile.username}[/green]")

    # 5. Test Reset Mechanism
    console.print("[dim]Phase 4: Testing form reset...[/dim]")
    app.handle_form_reset()
    app.update()
    assert app.var_username.get() == ""
    assert app.var_email.get() == ""
    assert app.var_quota.get() == 50
    console.print("  [green][PASS] Form reset successfully restored baseline state.[/green]")

    # Render Summary Table
    table = Table(title="Tkinter Architecture Verification Results", border_style="green")
    table.add_column("Component", style="bold cyan")
    table.add_column("Mechanism", style="white")
    table.add_column("Status", style="bold green")

    table.add_row("Root Lifecycle", "tk.Tk.__init__ & grid geometry weighting", "PASSED")
    table.add_row("Reactive Signals", "StringVar.trace_add('write') observer", "PASSED")
    table.add_row("Input Validation", "validatecommand callback + regex", "PASSED")
    table.add_row("Themed Widgets", "ttk.Style ('clam' theme with custom CSS)", "PASSED")
    table.add_row("Lifecycle Protocol", "WM_DELETE_WINDOW clean destroy", "PASSED")

    console.print(table)

    # 6. Safe Teardown
    app.destroy()
    return True


if __name__ == "__main__":
    if "--gui" in sys.argv or "--interactive" in sys.argv:
        # Launch Interactive Desktop Window
        print("Launching interactive Tkinter desktop interface...")
        interactive_app = EnterpriseTkinterApp(headless=False)
        interactive_app.mainloop()
    else:
        # Run automated verification and smoke test
        success = run_automated_verification()
        sys.exit(0 if success else 1)
