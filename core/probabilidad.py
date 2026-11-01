"""Frecuencia relativa, probabilidad clásica y frecuencial, condicional e independencia."""

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from itertools import combinations

import pandas as pd

from core.config import EPSILON_INDEPENDENCIA, MIN_CASOS


@dataclass(frozen=True)
class Resultado:
    """Una proporción con los casos que la respaldan."""

    valor: float | None  # None si no se puede calcular (por ejemplo P(B) = 0)
    favorables: int
    totales: int

    @property
    def poca_muestra(self) -> bool:
        """True si el resultado se apoya en menos de MIN_CASOS casos."""
        return self.totales < MIN_CASOS


@dataclass(frozen=True)
class ResultadoIndependencia:
    """Comparación entre P(A ∩ B) y P(A)·P(B)."""

    p_a: float
    p_b: float
    p_ab: float
    producto: float
    diferencia: float
    p_a_dado_b: float | None
    independientes: bool
    casos: int


def _resultado(favorables: int, totales: int) -> Resultado:
    """Arma un Resultado; el valor es None si no hay casos totales."""
    valor = favorables / totales if totales else None
    return Resultado(valor=valor, favorables=int(favorables), totales=int(totales))


def _como_bool(serie: pd.Series) -> pd.Series:
    """Convierte una serie booleana (posiblemente con <NA>) a bool, tratando <NA> como False."""
    return serie.fillna(False).astype(bool)


def frecuencia_relativa(evento: pd.Series, universo: pd.Series | None = None) -> Resultado:
    """fr(E) = casos con E / casos totales.

    `universo` es una máscara booleana opcional que restringe los casos totales.
    Los valores <NA> del evento se excluyen.
    """
    validos = evento.notna()
    if universo is not None:
        validos &= _como_bool(universo.reindex(evento.index))
    return _resultado(int(_como_bool(evento)[validos].sum()), int(validos.sum()))


def frecuencias_por_grupo(df: pd.DataFrame, evento: str, por: str | list[str]) -> pd.DataFrame:
    """Frecuencia relativa de un evento por grupo.

    Columnas: la(s) de agrupación, favorables, totales, frecuencia_relativa.
    """
    claves = [por] if isinstance(por, str) else list(por)
    datos = df[df[evento].notna()]
    tabla = (
        datos.assign(_fav=_como_bool(datos[evento]))
        .groupby(claves)
        .agg(favorables=("_fav", "sum"), totales=("_fav", "size"))
        .reset_index()
    )
    tabla["frecuencia_relativa"] = tabla["favorables"] / tabla["totales"]
    return tabla


def probabilidad_clasica_fecha(df: pd.DataFrame, evento: str) -> Resultado:
    """Se sortea un día del registro y todos son equiprobables: P = favorables / posibles."""
    return frecuencia_relativa(df[evento])


def probabilidad_clasica_uniforme(opciones: Sequence, favorables: Collection) -> Resultado:
    """Sorteo equiprobable entre `opciones` (por ejemplo zonas o meses)."""
    cantidad = sum(1 for opcion in opciones if opcion in favorables)
    return _resultado(cantidad, len(opciones))


def probabilidad_frecuencial(evento: pd.Series) -> Resultado:
    """P(E) ≈ fr(E) observada en el historial, como estimación de un día futuro."""
    return frecuencia_relativa(evento)


def convergencia(evento: pd.Series) -> pd.DataFrame:
    """Frecuencia acumulada del evento día a día, en el orden de la serie.

    Columnas: n, frecuencia_acumulada. Los valores <NA> se excluyen.
    """
    valores = _como_bool(evento[evento.notna()]).astype(float).reset_index(drop=True)
    n = pd.Series(range(1, len(valores) + 1), dtype="int64")
    return pd.DataFrame({"n": n, "frecuencia_acumulada": valores.cumsum() / n})


def probabilidad_condicional(a: pd.Series, b: pd.Series) -> Resultado:
    """P(A | B) = n(A ∩ B) / n(B). El valor es None si n(B) = 0."""
    validos = a.notna() & b.notna().reindex(a.index, fill_value=False)
    a_ok = _como_bool(a)[validos]
    b_ok = _como_bool(b.reindex(a.index))[validos]
    return _resultado(int((a_ok & b_ok).sum()), int(b_ok.sum()))


def matriz_condicional(
    df: pd.DataFrame, evento: str, filas: str = "zona", columnas: str = "mes"
) -> pd.DataFrame:
    """P(evento | fila, columna) en formato largo.

    Columnas: fila, columna, favorables, totales, probabilidad.
    """
    tabla = frecuencias_por_grupo(df, evento, [filas, columnas])
    return pd.DataFrame(
        {
            "fila": tabla[filas],
            "columna": tabla[columnas],
            "favorables": tabla["favorables"],
            "totales": tabla["totales"],
            "probabilidad": tabla["frecuencia_relativa"],
        }
    )


def independencia(
    a: pd.Series, b: pd.Series, epsilon: float = EPSILON_INDEPENDENCIA
) -> ResultadoIndependencia:
    """Compara P(A ∩ B) con P(A)·P(B): independientes si la diferencia es menor que epsilon.

    Se usan solo los días donde ambos eventos están definidos.
    """
    validos = a.notna() & b.reindex(a.index).notna()
    a_ok = _como_bool(a)[validos]
    b_ok = _como_bool(b.reindex(a.index))[validos]
    casos = int(validos.sum())
    if casos == 0:
        nan = float("nan")
        return ResultadoIndependencia(nan, nan, nan, nan, nan, None, False, 0)

    p_a = float(a_ok.mean())
    p_b = float(b_ok.mean())
    p_ab = float((a_ok & b_ok).mean())
    producto = p_a * p_b
    diferencia = abs(p_ab - producto)
    p_a_dado_b = p_ab / p_b if p_b > 0 else None
    return ResultadoIndependencia(
        p_a=p_a,
        p_b=p_b,
        p_ab=p_ab,
        producto=producto,
        diferencia=diferencia,
        p_a_dado_b=p_a_dado_b,
        independientes=diferencia < epsilon,
        casos=casos,
    )


def matriz_independencia(
    df: pd.DataFrame, eventos: list[str], epsilon: float = EPSILON_INDEPENDENCIA
) -> pd.DataFrame:
    """Evalúa todos los pares de eventos (con 4 eventos, 6 pares).

    Columnas: a, b, p_a, p_b, p_ab, producto, diferencia, p_a_dado_b, independientes, casos.
    """
    filas = []
    for nombre_a, nombre_b in combinations(eventos, 2):
        r = independencia(df[nombre_a], df[nombre_b], epsilon)
        filas.append(
            {
                "a": nombre_a,
                "b": nombre_b,
                "p_a": r.p_a,
                "p_b": r.p_b,
                "p_ab": r.p_ab,
                "producto": r.producto,
                "diferencia": r.diferencia,
                "p_a_dado_b": r.p_a_dado_b,
                "independientes": r.independientes,
                "casos": r.casos,
            }
        )
    return pd.DataFrame(filas)


def ranking_zona_mes(df: pd.DataFrame) -> pd.DataFrame:
    """P(apto | zona, mes) con sus casos, de mayor a menor probabilidad.

    Columnas: zona, mes, favorables, totales, probabilidad.
    """
    tabla = matriz_condicional(df, "apto", "zona", "mes").rename(
        columns={"fila": "zona", "columna": "mes"}
    )
    return tabla.sort_values(
        ["probabilidad", "totales", "zona", "mes"], ascending=[False, False, True, True]
    ).reset_index(drop=True)
