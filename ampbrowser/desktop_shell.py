from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import replace
from pathlib import Path
import sys

from .config import AppConfig
from .launch import OpenPlan, prepare_open
from .open_runner import launch_open_plan


PromptDriver = Callable[[OpenPlan], bool]


@dataclass(frozen=True)
class DesktopShellResult:
    open_plan: OpenPlan
    prompt_shown: bool
    prompt_approved: bool


def launch_desktop_shell(
    raw_url: str,
    *,
    config: AppConfig,
    root: Path,
    auto_approve: bool = False,
    prompt_driver: PromptDriver | None = None,
) -> DesktopShellResult:
    open_plan = prepare_open(raw_url, consent=False, dry_run=False, config=config, platform="desktop")
    prompt_shown = False
    prompt_approved = False

    if open_plan.status == "consent-required":
        if auto_approve:
            prompt_approved = True
        else:
            prompt_shown = True
            prompt_approved = (prompt_driver or prompt_for_setup)(open_plan)
        if not prompt_approved:
            return DesktopShellResult(
                replace(open_plan, dry_run=False, status="cancelled", message="first-use setup cancelled"),
                prompt_shown,
                False,
            )
        open_plan = prepare_open(raw_url, consent=True, dry_run=False, config=config, platform="desktop")

    return DesktopShellResult(
        launch_open_plan(open_plan, config=config, root=root),
        prompt_shown,
        prompt_approved,
    )


def prompt_for_setup(open_plan: OpenPlan) -> bool:
    try:
        return _tk_prompt(open_plan)
    except Exception:  # noqa: BLE001
        return _terminal_prompt(open_plan)


def _tk_prompt(open_plan: OpenPlan) -> bool:
    import tkinter as tk
    from tkinter import ttk

    result = {"approved": False}
    window = tk.Tk()
    window.title(open_plan.setup_prompt_title)
    window.geometry("520x260")
    window.minsize(420, 220)
    window.resizable(False, False)

    frame = ttk.Frame(window, padding=20)
    frame.pack(fill="both", expand=True)

    title = ttk.Label(frame, text=open_plan.setup_prompt_title, font=("TkDefaultFont", 15, "bold"))
    title.pack(anchor="w")

    body = ttk.Label(frame, text=open_plan.setup_prompt_body, wraplength=460, justify="left")
    body.pack(anchor="w", fill="x", pady=(12, 18))

    button_row = ttk.Frame(frame)
    button_row.pack(anchor="e", fill="x")

    def approve() -> None:
        result["approved"] = True
        window.quit()

    def cancel() -> None:
        result["approved"] = False
        window.quit()

    cancel_button = ttk.Button(button_row, text="Cancel", command=cancel)
    cancel_button.pack(side="right")
    approve_button = ttk.Button(button_row, text=open_plan.setup_prompt_approve_label, command=approve)
    approve_button.pack(side="right", padx=(0, 8))
    approve_button.focus_set()
    window.bind("<Return>", lambda event: approve())
    window.bind("<Escape>", lambda event: cancel())
    window.protocol("WM_DELETE_WINDOW", cancel)
    window.attributes("-topmost", True)
    window.after(250, lambda: window.attributes("-topmost", False))
    window.mainloop()
    window.destroy()
    return result["approved"]


def _terminal_prompt(open_plan: OpenPlan) -> bool:
    print(open_plan.setup_prompt_title, file=sys.stderr)
    print(open_plan.setup_prompt_body, file=sys.stderr)
    if not sys.stdin.isatty():
        return False
    answer = input(f"{open_plan.setup_prompt_approve_label}? [y/N] ")
    return answer.strip().lower() in {"y", "yes"}
