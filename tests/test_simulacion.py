"""Pruebas de core/simulacion.py."""

import numpy as np
import pandas as pd
import pytest

from core.simulacion import simular

REGISTRO = pd.Series([True] * 350 + [False] * 650)  # P = 0,35


def test_misma_semilla_misma_curva():
    a = simular(REGISTRO, 500, 42)
    b = simular(REGISTRO, 500, 42)
    assert a.curva.equals(b.curva)
    assert a.frecuencia_final == b.frecuencia_final


def test_distinta_semilla_distinta_curva():
    assert not simular(REGISTRO, 500, 1).curva.equals(simular(REGISTRO, 500, 2).curva)


def test_con_n_grande_se_acerca_al_registro():
    r = simular(REGISTRO, 100_000, 42)
    assert r.probabilidad_registro == pytest.approx(0.35)
    assert abs(r.frecuencia_final - 0.35) < 0.01
    assert len(r.curva) == 100_000
    assert r.curva["n"].iloc[-1] == 100_000
    assert r.curva["frecuencia_acumulada"].iloc[-1] == r.frecuencia_final


def test_solo_sortea_dias_reales_y_excluye_na():
    ev = pd.Series([True, pd.NA, True], dtype="boolean")
    r = simular(ev, 50, 7)
    assert r.probabilidad_registro == 1.0 and r.frecuencia_final == 1.0


def test_registro_vacio_y_n_invalido():
    r = simular(pd.Series([], dtype=bool), 10, 1)
    assert np.isnan(r.frecuencia_final) and r.curva.empty
    with pytest.raises(ValueError):
        simular(REGISTRO, 0, 1)
