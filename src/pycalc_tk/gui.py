#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=========================================================================================================
Project: pycalc-tk — Arbitrary-Precision Tkinter Calculator
File: gui.py
Author: Mobin Yousefi (GitHub: https://github.com/mobinyousefi-cs)
Created: 2025-10-02
Updated: 2025-10-02
License: MIT License (see LICENSE file for details)
=====================================================================================================

Description:
Tkinter GUI for the calculator. Provides a clean keypad, expression entry, live result display,
memory controls (MC/MR/M+/M-), and a precision spinbox to adjust decimal digits at runtime.

Usage:
python -c "import tkinter as tk; from pycalc_tk.gui import CalculatorApp; root=tk.Tk(); CalculatorApp(root).mainloop()"

Notes:
- Keyboard shortcuts: Enter (=), Backspace (⌫), Esc (clear).
- Symbol helpers map to engine syntax (e.g., ÷ → "/", × → "*", π → pi, √ → sqrt()).
- Designed to be cross-platform (Windows/macOS/Linux) with ttk styling.
"""


from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable

from .core import CalculatorEngine, EvalSettings, set_precision

KEYS = [
    ["MC", "MR", "M+", "M-", "C", "⌫"],
    ["(", ")", "%", "÷", "√", "^"],
    ["7", "8", "9", "×", "ln", "log"],
    ["4", "5", "6", "-", "e", "π"],
    ["1", "2", "3", "+", "τ", "abs"],
    ["0", ".", "±", "=", "exp", "round"],
]

SYMBOL_MAP = {
    "÷": "/",
    "×": "*",
    "π": "pi",
    "τ": "tau",
    "√": "sqrt(",
    "ln": "ln(",
    "log": "log10(",
    "exp": "exp(",
    "abs": "abs(",
    "^": "**",
}

class CalculatorApp(ttk.Frame):
    def __init__(self, master: tk.Misc | None = None):
        super().__init__(master)
        self.engine = CalculatorEngine(EvalSettings())
        self._build_ui(master if master else self)

    def _build_ui(self, master: tk.Misc):
        master.title("pycalc-tk — Arbitrary Precision Calculator")
        master.geometry("420x520")
        master.minsize(380, 480)

        # Use a dark-ish theme if available
        style = ttk.Style(master)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        self.pack(fill="both", expand=True)
        container = ttk.Frame(self, padding=10)
        container.pack(fill="both", expand=True)

        # Display
        self.display_var = tk.StringVar(value="")
        self.entry = ttk.Entry(
            container, textvariable=self.display_var, font=("Consolas", 18), justify="right"
        )
        self.entry.pack(fill="x", pady=(0, 8))
        self.entry.focus_set()

        # Result label
        self.result_var = tk.StringVar(value="")
        result = ttk.Label(container, textvariable=self.result_var, anchor="e", font=("Consolas", 14))
        result.pack(fill="x", pady=(0, 8))

        # Buttons grid
        grid = ttk.Frame(container)
        grid.pack(fill="both", expand=True)

        for r, row in enumerate(KEYS):
            for c, key in enumerate(row):
                btn = ttk.Button(grid, text=key, command=lambda k=key: self.on_key(k))
                btn.grid(row=r, column=c, sticky="nsew", padx=3, pady=3)
        for i in range(len(KEYS)):
            grid.rowconfigure(i, weight=1)
        for j in range(len(KEYS[0])):
            grid.columnconfigure(j, weight=1)

        # Precision control
        precision_frame = ttk.Frame(container)
        precision_frame.pack(fill="x", pady=(8, 0))
        ttk.Label(precision_frame, text="Precision (digits):").pack(side="left")
        self.prec_var = tk.IntVar(value=1000)
        prec_spin = ttk.Spinbox(precision_frame, from_=16, to=100000, textvariable=self.prec_var, width=8)
        prec_spin.pack(side="left", padx=6)
        ttk.Button(precision_frame, text="Apply", command=self.apply_precision).pack(side="left")

        # Keyboard bindings
        master.bind("<Return>", lambda e: self.on_key("="))
        master.bind("<KP_Enter>", lambda e: self.on_key("="))
        master.bind("<BackSpace>", lambda e: self.on_key("⌫"))
        master.bind("<Escape>", lambda e: self.on_key("C"))
        master.bind("<Key>", self._on_text_key)

    def _insert(self, s: str) -> None:
        pos = self.entry.index(tk.INSERT)
        self.entry.insert(pos, s)

    def on_key(self, key: str) -> None:
        if key in SYMBOL_MAP:
            self._insert(SYMBOL_MAP[key])
        elif key == "=":
            expr = self.display_var.get()
            try:
                out = self.engine.evaluate(expr)
                self.result_var.set(out)
            except Exception as ex:
                messagebox.showerror("Error", str(ex))
        elif key == "C":
            self.display_var.set("")
            self.result_var.set("")
        elif key == "⌫":
            current = self.display_var.get()
            if current:
                self.display_var.set(current[:-1])
        elif key == "±":
            # Toggle sign of last number segment
            self._toggle_sign()
        elif key in {"MC", "MR", "M+", "M-"}:
            self._handle_memory(key)
        else:
            self._insert(key)

    def _toggle_sign(self) -> None:
        text = self.display_var.get()
        if not text:
            self.display_var.set("-")
            return
        # Find last number (simple heuristic)
        i = len(text) - 1
        while i >= 0 and (text[i].isdigit() or text[i] == "."):
            i -= 1
        segment = text[i + 1 :]
        if not segment:
            self._insert("-")
            return
        if segment.startswith("-"):
            new = text[: i + 1] + segment[1:]
        else:
            new = text[: i + 1] + "-" + segment
        self.display_var.set(new)

    def _handle_memory(self, key: str) -> None:
        from .core import Decimal

        if key == "MC":
            self.engine.memory.clear()
            self.result_var.set("0")
        elif key == "MR":
            # Inserts 'M' variable which engine binds to memory value
            self._insert("M")
        elif key == "M+":
            val = self._current_or_result_decimal()
            self.engine.memory.add(val)
        elif key == "M-":
            val = self._current_or_result_decimal()
            self.engine.memory.sub(val)

    def _current_or_result_decimal(self):
        from .core import Decimal, DecimalEvaluator, EvalSettings

        # Prefer evaluated result if present; else try to evaluate current input
        if self.result_var.get():
            from decimal import Decimal as _D
            return _D(self.result_var.get())
        expr = self.display_var.get() or "0"
        evaluator = DecimalEvaluator(EvalSettings(), {})
        return evaluator.eval(expr)

    def apply_precision(self) -> None:
        try:
            p = int(self.prec_var.get())
            set_precision(p)
            self.result_var.set(f"Precision set to {p}")
        except Exception as ex:
            messagebox.showerror("Precision Error", str(ex))

    def _on_text_key(self, event: tk.Event) -> None:
        # Allow digits, operators, parentheses, dot; prevent invalid chars
        allowed = "0123456789.+-*/()%^ "
        if event.char and event.char not in allowed:
            # map some common keys
            if event.char.lower() == "p":
                self._insert("pi")
            elif event.char.lower() == "e":
                self._insert("e")
            else:
                return  # ignore others
