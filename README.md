# pycalc-tk — Arbitrary-Precision Tkinter Calculator

A polished desktop calculator with **arbitrary decimal precision** using Python’s `decimal` module and a safe AST evaluator. Clean architecture, typed code, tests, and CI out of the box.

## Features
- Arbitrary precision (default **1000** digits). Adjustable at runtime.
- Safe expression evaluator (no `eval`) supporting:
  - `+ - * / % **`, parentheses, unary `±`
  - Functions: `sqrt`, `ln`, `log10`, `exp`, `pow`, `abs`, `round(x, ndigits)`
  - Constants: `pi`, `e`, `tau`
  - Memory register: `MC`, `MR` (as variable `M`), `M+`, `M-`
- Keyboard support: `Enter` (=), `Backspace` (⌫), `Esc` (C)
- Cross-platform (Windows, macOS, Linux)

## Install & Run
```bash
# Python 3.11+ recommended
pip install -e .
python -m pycalc_tk
