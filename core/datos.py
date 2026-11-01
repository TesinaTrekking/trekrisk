"""Carga y validación de los CSV de clima, y estadística descriptiva."""

from pathlib import Path

import pandas as pd

from core.config import DIAS_ESPERADOS, FECHA_FIN, FECHA_INICIO, ZONAS

COLUMNAS_NUMERICAS: list[str] = [
    "precipitacion_mm",
    "viento_kmh",
    "racha_kmh",
    "tmax_c",
    "tmin_c",
]
COLUMNAS_BASE: list[str] = ["zona", "fecha", *COLUMNAS_NUMERICAS]

_ESTACION_POR_MES: dict[int, str] = {
    12: "verano", 1: "verano", 2: "verano",
    3: "otoño", 4: "otoño", 5: "otoño",
    6: "invierno", 7: "invierno", 8: "invierno",
    9: "primavera", 10: "primavera", 11: "primavera",
}


def cargar_clima(carpeta: str = "data", zonas: list[str] | None = None) -> pd.DataFrame:
    """Lee los CSV de las zonas pedidas (todas por defecto) y agrega anio, mes y estacion.

    Lanza FileNotFoundError, con un mensaje claro, si falta algún CSV.
    """
    slugs = zonas if zonas is not None else [z.slug for z in ZONAS]
    partes: list[pd.DataFrame] = []
    for slug in slugs:
        ruta = Path(carpeta) / f"clima_{slug}.csv"
        if not ruta.exists():
            raise FileNotFoundError(
                f"Falta el archivo {ruta}. Descargá los datos desde la pantalla Datos."
            )
        partes.append(pd.read_csv(ruta, parse_dates=["fecha"]))
    if not partes:
        return pd.DataFrame(columns=[*COLUMNAS_BASE, "anio", "mes", "estacion"])

    df = pd.concat(partes, ignore_index=True)
    df["anio"] = df["fecha"].dt.year
    df["mes"] = df["fecha"].dt.month
    df["estacion"] = df["mes"].map(_ESTACION_POR_MES)
    return df


def validar(df: pd.DataFrame) -> list[str]:
    """Revisa el clima completo y devuelve la lista de problemas (vacía si todo está bien).

    Controla columnas, nulos, fechas duplicadas y que cada zona tenga
    exactamente los días del período fijo.
    """
    faltantes = [c for c in COLUMNAS_BASE if c not in df.columns]
    if faltantes:
        return [f"Faltan columnas: {', '.join(faltantes)}."]

    problemas: list[str] = []
    for columna in COLUMNAS_BASE:
        nulos = int(df[columna].isna().sum())
        if nulos:
            problemas.append(f"La columna {columna} tiene {nulos} valores nulos.")

    esperadas = pd.date_range(FECHA_INICIO, FECHA_FIN, freq="D")
    for slug, grupo in df.groupby("zona"):
        fechas = pd.to_datetime(grupo["fecha"])
        duplicadas = int(fechas.duplicated().sum())
        if duplicadas:
            problemas.append(f"{slug}: {duplicadas} fechas duplicadas.")
        if len(grupo) != DIAS_ESPERADOS:
            problemas.append(f"{slug}: tiene {len(grupo)} filas y se esperaban {DIAS_ESPERADOS}.")
        sin_dia = len(esperadas.difference(pd.DatetimeIndex(fechas)))
        if sin_dia:
            problemas.append(f"{slug}: faltan {sin_dia} días del período.")
    return problemas


def resumen_descriptivo(df: pd.DataFrame) -> pd.DataFrame:
    """Media, mediana, desvío, mínimo, máximo y percentiles 25 y 75 por variable."""
    datos = df[COLUMNAS_NUMERICAS]
    return pd.DataFrame(
        {
            "media": datos.mean(),
            "mediana": datos.median(),
            "desvio": datos.std(),
            "minimo": datos.min(),
            "maximo": datos.max(),
            "p25": datos.quantile(0.25),
            "p75": datos.quantile(0.75),
        }
    )
