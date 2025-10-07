#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=========================================================================================================
Project: pycalc-tk — Arbitrary-Precision Tkinter Calculator
File: main.py
Author: Mobin Yousefi (GitHub: https://github.com/mobinyousefi-cs)
Created: 2025-10-02
Updated: 2025-10-02
License: MIT License (see LICENSE file for details)
=====================================================================================================

Description:
Application entry point. Initializes the Tkinter root window and launches the Calculator GUI.

Usage:
python -m pycalc_tk
# or (if installed as a script via `pyproject.toml`):
pycalc-tk

Notes:
- Make sure project is installed in editable mode for module resolution: `pip install -e .`
- The GUI depends only on the standard library (tkinter) and the local `core` engine.
"""

from __future__ import annotations

import tkinter as tk

from .gui import CalculatorApp


def main() -> None:
    root = tk.Tk()
    app = CalculatorApp(root)
    app.mainloop()


if __name__ == "__main__":
    main()
