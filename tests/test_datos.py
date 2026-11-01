"""Pruebas de core/datos.py."""

import pandas as pd
import pytest

from core.config import DIAS_ESPERADOS, FECHA_FIN, FECHA_INICIO, ZONAS
from core.datos import cargar_clima, resumen_descriptivo, validar


def _zona_completa(slug: str) -> pd.DataFrame:
    fechas = pd.date_range(FECHA_INICIO, FECHA_FIN, freq="D")
    return pd.DataFrame(
        {
            "zona": slug,
            "fecha": fechas,
            "precipitacion_mm": 0.0,
            "viento_kmh": 10.0,
            "racha_kmh": 20.0,
            "tmax_c": 25.0,
            "tmin_c": 10.0,
        }
    )


def test_periodo_fijo_tiene_1826_dias():
    assert len(_zona_completa("x")) == DIAS_ESPERADOS


def test_validar_sin_problemas():
    assert validar(_zona_completa("champaqui")) == []


def test_validar_detecta_nulos():
    df = _zona_completa("champaqui")
    df.loc[5, "tmax_c"] = None
    assert any("nulos" in p for p in validar(df))


def test_validar_detecta_filas_faltantes():
    df = _zona_completa("champaqui").drop(index=[10, 11])
    problemas = validar(df)
    assert any("1824 filas" in p for p in problemas)
    assert any("faltan 2 días" in p for p in problemas)


def test_validar_detecta_fechas_duplicadas():
    df = _zona_completa("champaqui")
    df.loc[3, "fecha"] = df.loc[2, "fecha"]
    assert any("duplicadas" in p for p in validar(df))


def test_validar_detecta_columnas_faltantes():
    df = _zona_completa("champaqui").drop(columns=["racha_kmh"])
    assert validar(df) == ["Faltan columnas: racha_kmh."]


def test_cargar_clima_agrega_derivadas(tmp_path):
    df = _zona_completa("champaqui")
    df.to_csv(tmp_path / "clima_champaqui.csv", index=False)
    cargado = cargar_clima(str(tmp_path), ["champaqui"])
    fila = cargado[cargado["fecha"] == "2021-07-15"].iloc[0]
    assert (fila["anio"], fila["mes"], fila["estacion"]) == (2021, 7, "invierno")
    estaciones = cargado.groupby("mes")["estacion"].first()
    assert estaciones[12] == "verano" and estaciones[3] == "otoño" and estaciones[9] == "primavera"


def test_cargar_clima_falta_csv(tmp_path):
    with pytest.raises(FileNotFoundError, match="clima_champaqui.csv"):
        cargar_clima(str(tmp_path), ["champaqui"])


def test_resumen_descriptivo_valores_a_mano():
    df = pd.DataFrame(
        {
            "precipitacion_mm": [0.0, 2.0, 4.0],
            "viento_kmh": [1.0, 2.0, 3.0],
            "racha_kmh": [1.0, 2.0, 3.0],
            "tmax_c": [10.0, 20.0, 30.0],
            "tmin_c": [0.0, 0.0, 0.0],
        }
    )
    r = resumen_descriptivo(df)
    assert r.loc["precipitacion_mm", "media"] == 2.0
    assert r.loc["tmax_c", "mediana"] == 20.0
    assert r.loc["tmax_c", "desvio"] == 10.0
    assert r.loc["tmax_c", "p25"] == 15.0


def test_csv_reales_tienen_1826_filas_sin_nulos_y_validan():
    df = cargar_clima("data")
    por_zona = df.groupby("zona").size()
    assert set(por_zona.index) == {z.slug for z in ZONAS}
    assert (por_zona == DIAS_ESPERADOS).all()
    assert len(df) == 9130
    assert not df.isna().any().any()
    assert validar(df) == []
