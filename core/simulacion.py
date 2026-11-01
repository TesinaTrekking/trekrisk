"""Experimento aleatorio: remuestreo con reposición de días reales."""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ResultadoSimulacion:
    """Resultado de un remuestreo: frecuencia final, referencia del registro y curva."""

    n: int
    semilla: int
    frecuencia_final: float
    probabilidad_registro: float
    curva: pd.DataFrame  # columnas: n, frecuencia_acumulada


def simular(evento: pd.Series, n: int, semilla: int) -> ResultadoSimulacion:
    """Elige `n` días reales al azar, con reposición, y calcula la frecuencia acumulada.

    No genera datos nuevos: solo sortea filas del registro. Misma semilla, mismo
    resultado. Los valores <NA> del evento se excluyen. Si no quedan días, la
    frecuencia es NaN y la curva queda vacía.
    """
    if n < 1:
        raise ValueError("n debe ser al menos 1.")
    valores = evento[evento.notna()].astype(bool).to_numpy()
    if valores.size == 0:
        vacia = pd.DataFrame({"n": pd.Series(dtype="int64"),
                              "frecuencia_acumulada": pd.Series(dtype="float64")})
        return ResultadoSimulacion(n, semilla, float("nan"), float("nan"), vacia)

    azar = np.random.default_rng(semilla)
    muestra = valores[azar.integers(0, valores.size, size=n)]
    pasos = np.arange(1, n + 1)
    acumulada = np.cumsum(muestra) / pasos
    curva = pd.DataFrame({"n": pasos, "frecuencia_acumulada": acumulada})
    return ResultadoSimulacion(
        n=n,
        semilla=semilla,
        frecuencia_final=float(acumulada[-1]),
        probabilidad_registro=float(valores.mean()),
        curva=curva,
    )
