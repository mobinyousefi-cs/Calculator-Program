from decimal import Decimal
import pytest

from pycalc_tk.core import CalculatorEngine, EvalSettings, set_precision


def evals(expr: str, prec: int = 100) -> Decimal:
    engine = CalculatorEngine(EvalSettings(precision=prec))
    return Decimal(engine.evaluate(expr))


@pytest.mark.parametrize(
    "expr, expected",
    [
        ("1+2*3", Decimal("7")),
        ("(1+2)*3", Decimal("9")),
        ("10/4", Decimal("2.5")),
        ("5%2", Decimal("1")),
        ("2^10", Decimal("1024")),
        ("sqrt(4)", Decimal("2")),
        ("ln(e)", Decimal("1")),
        ("log10(1000)", Decimal("3")),
        ("exp(0)", Decimal("0").exp()),  # 1
        ("abs(-12.5)", Decimal("12.5")),
        ("round(1.2345, 2)", Decimal("1.23")),
    ],
)
def test_basic(expr, expected):
    out = evals(expr)
    assert out == expected


def test_precision_high():
    set_precision(200)
    a = evals("1/7", 200)
    b = evals("1/7", 200)
    assert str(a).startswith("0.142857142857")
    assert a == b


def test_memory_variable():
    eng = CalculatorEngine()
    # store 3 in memory via evaluate/variables path
    v = Decimal(eng.evaluate("1+2"))
    eng.memory.add(v)
    # evaluate using M
    out = Decimal(eng.evaluate("M*2"))
    assert out == v * 2
