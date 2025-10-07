#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=========================================================================================================
Project: pycalc-tk — Arbitrary-Precision Tkinter Calculator
File: core.py
Author: Mobin Yousefi (GitHub: https://github.com/mobinyousefi-cs)
Created: 2025-10-02
Updated: 2025-10-02
License: MIT License (see LICENSE file for details)
=====================================================================================================

Description:
Core calculation engine with a safe Decimal-based evaluator (AST parsing). Supports arbitrary
precision arithmetic, common operators (+, -, *, /, %, **), functions (sqrt, ln, log10, exp, abs,
round, pow), and constants (pi, e, tau). Also provides a simple memory register (M).

Usage:
python -c "from pycalc_tk.core import CalculatorEngine; print(CalculatorEngine().evaluate('sqrt(2)+pi'))"

Notes:
- Uses Python's `decimal` for high-precision, banker’s rounding (ROUND_HALF_EVEN).
- Avoids `eval` by parsing expressions via `ast`.
- Set precision at runtime via `set_precision(digits)` or GUI control.
"""


from __future__ import annotations

import ast
from dataclasses import dataclass
from decimal import Decimal, getcontext, Context, localcontext, ROUND_HALF_EVEN
from typing import Any, Dict, Mapping

# Global context: very high precision by default; adjust via set_precision()
_DEFAULT_PRECISION = 1000
getcontext().prec = _DEFAULT_PRECISION
getcontext().rounding = ROUND_HALF_EVEN
getcontext().traps[decimal.FloatOperation] = True  # type: ignore[name-defined]

import decimal  # after setting traps we can import for type hints


@dataclass
class EvalSettings:
    precision: int = _DEFAULT_PRECISION
    rounding: str = ROUND_HALF_EVEN  # see decimal module for options
    max_depth: int = 64  # safety for nested expressions


SAFE_CONSTS: Mapping[str, Decimal] = {
    "pi": Decimal("3.14159265358979323846264338327950288419716939937510"),
    "e": Decimal("2.71828182845904523536028747135266249775724709369995"),
    "tau": Decimal("6.28318530717958647692528676655900576839433879875021"),
}

def set_precision(prec: int) -> None:
    """Set global default precision (affects subsequent evaluations)."""
    if prec < 16:
        raise ValueError("Precision must be at least 16.")
    ctx = getcontext()
    ctx.prec = prec

def _to_decimal(n: Any) -> Decimal:
    if isinstance(n, Decimal):
        return n
    if isinstance(n, (int, str)):
        return Decimal(str(n))
    raise TypeError(f"Unsupported literal type: {type(n)}")

class DecimalEvaluator(ast.NodeVisitor):
    """
    Safe expression evaluator to Decimal using Python AST.
    Supports: +, -, *, /, %, **, unary +/-, parentheses.
    Functions: sqrt, ln, log10, exp, pow(x,y), abs, round(x, [ndigits]).
    Constants: pi, e, tau.
    """

    allowed_funcs = {
        "sqrt": lambda x: x.sqrt(),
        "ln": lambda x: x.ln(),
        "log10": lambda x: x.log10(),
        "exp": lambda x: x.exp(),
        "abs": lambda x: x.copy_abs(),
        "round": lambda x, n=Decimal(0): _round_decimal(x, int(n)),
        "pow": lambda x, y: x.__pow__(y),
    }

    def __init__(self, settings: EvalSettings | None = None, variables: Dict[str, Decimal] | None = None):
        super().__init__()
        self.settings = settings or EvalSettings()
        self.vars: Dict[str, Decimal] = dict(SAFE_CONSTS)
        if variables:
            # Allow user variables (e.g., memory recall) as Decimals
            self.vars.update({k: _to_decimal(v) for k, v in variables.items()})

    def eval(self, expr: str) -> Decimal:
        with localcontext(Context(prec=self.settings.precision, rounding=self.settings.rounding)):
            node = ast.parse(expr, mode="eval")
            return self._eval_node(node.body, depth=0)

    # ---- Node handlers ----
    def _eval_node(self, node: ast.AST, depth: int) -> Decimal:
        if depth > self.settings.max_depth:
            raise ValueError("Expression too deeply nested.")
        match node:
            case ast.Constant(value=v):
                return _to_decimal(v)
            case ast.Num(n=n):  # py<3.8 compatibility
                return _to_decimal(n)
            case ast.BinOp(left=l, op=op, right=r):
                a, b = self._eval_node(l, depth + 1), self._eval_node(r, depth + 1)
                return self._apply_binop(a, op, b)
            case ast.UnaryOp(op=op, operand=operand):
                val = self._eval_node(operand, depth + 1)
                return self._apply_unary(op, val)
            case ast.Name(id=name):
                if name in self.vars:
                    return self.vars[name]
                raise NameError(f"Unknown identifier: {name}")
            case ast.Call(func=f, args=args, keywords=kwargs):
                if kwargs:
                    raise ValueError("Keyword arguments are not supported.")
                fname = getattr(f, "id", None)
                if fname not in self.allowed_funcs:
                    raise NameError(f"Unsupported function: {fname}")
                dargs = [self._eval_node(a, depth + 1) for a in args]
                # Special case: pow should enforce integer exponent if exponent not finite?
                return self.allowed_funcs[fname](*dargs)  # type: ignore[misc]
            case _:
                raise SyntaxError("Unsupported syntax in expression.")

    @staticmethod
    def _apply_unary(op: ast.unaryop, val: Decimal) -> Decimal:
        if isinstance(op, ast.UAdd):
            return val
        if isinstance(op, ast.USub):
            return -val
        raise SyntaxError("Unsupported unary operator.")

    @staticmethod
    def _apply_binop(a: Decimal, op: ast.operator, b: Decimal) -> Decimal:
        if isinstance(op, ast.Add):
            return a + b
        if isinstance(op, ast.Sub):
            return a - b
        if isinstance(op, ast.Mult):
            return a * b
        if isinstance(op, ast.Div):
            if b == 0:
                raise ZeroDivisionError("Division by zero.")
            return a / b
        if isinstance(op, ast.Mod):
            if b == 0:
                raise ZeroDivisionError("Modulo by zero.")
            return a % b
        if isinstance(op, ast.Pow):
            # Decimal ** Decimal may be slow for large fractional exponents; still allowed.
            return a.__pow__(b)
        raise SyntaxError("Unsupported binary operator.")

def _round_decimal(x: Decimal, ndigits: int) -> Decimal:
    if ndigits >= 0:
        q = Decimal(1).scaleb(-ndigits)  # 10**(-ndigits)
        return x.quantize(q)
    # Negative ndigits rounds to tens, hundreds, etc.
    q = Decimal(1).scaleb(-ndigits)  # still works: e.g., ndigits=-1 => q=10
    return x.quantize(q)

# -------- Memory register --------

@dataclass
class Memory:
    value: Decimal = Decimal(0)

    def clear(self) -> None:
        self.value = Decimal(0)

    def recall(self) -> Decimal:
        return self.value

    def add(self, x: Decimal) -> None:
        self.value += x

    def sub(self, x: Decimal) -> None:
        self.value -= x

# -------- Public API --------

class CalculatorEngine:
    """
    Glue between GUI and evaluator. Manages memory and formatting.
    """

    def __init__(self, settings: EvalSettings | None = None):
        self.settings = settings or EvalSettings()
        self.memory = Memory()

    def evaluate(self, expr: str) -> str:
        expr = expr.strip()
        if not expr:
            return ""
        evaluator = DecimalEvaluator(self.settings, variables={"M": self.memory.recall()})
        result = evaluator.eval(expr)
        return self.format_decimal(result)

    @staticmethod
    def format_decimal(x: Decimal) -> str:
        # Normalize to remove trailing zeros, but keep integer if exact.
        normalized = x.normalize()
        # If it's an integer in scientific notation, convert to plain string
        s = format(normalized, "f") if normalized == normalized.to_integral() else format(normalized, "f")
        # Strip trailing zeros after decimal point
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        return s or "0"
