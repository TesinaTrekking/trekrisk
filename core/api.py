"""Descarga del clima histórico desde Open-Meteo (Historical Weather API)."""

from pathlib import Path

import pandas as pd
import requests

from core.config import FECHA_FIN, FECHA_INICIO, ZONAS, Zona

URL_API = "https://archive-api.open-meteo.com/v1/archive"
ZONA_HORARIA = "America/Argentina/Cordoba"
TIMEOUT_SEGUNDOS = 60

# Variable de la API -> columna del CSV
VARIABLES_DIARIAS: dict[str, str] = {
    "precipitation_sum": "precipitacion_mm",
    "wind_speed_10m_max": "viento_kmh",
    "wind_gusts_10m_max": "racha_kmh",
    "temperature_2m_max": "tmax_c",
    "temperature_2m_min": "tmin_c",
}

COLUMNAS_CSV: list[str] = ["zona", "fecha", *VARIABLES_DIARIAS.values()]


class ErrorDescarga(Exception):
    """Falla al descargar o interpretar la respuesta de Open-Meteo."""


def _parametros(zona: Zona, inicio: str, fin: str) -> dict[str, str | float]:
    """Arma los parámetros de la consulta, con unidades explícitas."""
    return {
        "latitude": zona.latitud,
        "longitude": zona.longitud,
        "start_date": inicio,
        "end_date": fin,
        "daily": ",".join(VARIABLES_DIARIAS),
        "timezone": ZONA_HORARIA,
        "precipitation_unit": "mm",
        "wind_speed_unit": "kmh",
        "temperature_unit": "celsius",
    }


def _a_dataframe(datos: dict, zona: Zona) -> pd.DataFrame:
    """Convierte el JSON de la API al esquema del CSV."""
    diario = datos.get("daily")
    if not isinstance(diario, dict) or "time" not in diario:
        raise ErrorDescarga(f"Respuesta sin datos diarios para {zona.nombre}.")
    faltan = [v for v in VARIABLES_DIARIAS if v not in diario]
    if faltan:
        raise ErrorDescarga(f"Faltan variables en la respuesta: {', '.join(faltan)}.")
    try:
        df = pd.DataFrame({"fecha": diario["time"]})
        for variable, columna in VARIABLES_DIARIAS.items():
            df[columna] = diario[variable]
    except ValueError as error:
        raise ErrorDescarga(f"Listas de distinto largo en la respuesta: {error}") from error
    df.insert(0, "zona", zona.slug)
    return df[COLUMNAS_CSV]


def descargar_zona(zona: Zona, inicio: str, fin: str) -> pd.DataFrame:
    """Descarga el clima diario de una zona y lo devuelve con el esquema del CSV."""
    try:
        respuesta = requests.get(
            URL_API, params=_parametros(zona, inicio, fin), timeout=TIMEOUT_SEGUNDOS
        )
    except requests.RequestException as error:
        raise ErrorDescarga(f"No se pudo conectar con Open-Meteo: {error}") from error

    if respuesta.status_code != 200:
        try:
            motivo = respuesta.json().get("reason", respuesta.text)
        except ValueError:
            motivo = respuesta.text
        raise ErrorDescarga(f"Open-Meteo respondió {respuesta.status_code}: {motivo}")

    try:
        datos = respuesta.json()
    except ValueError as error:
        raise ErrorDescarga("La respuesta de Open-Meteo no es un JSON válido.") from error
    return _a_dataframe(datos, zona)


def guardar_csv(df: pd.DataFrame, zona: Zona, carpeta: str = "data") -> Path:
    """Guarda el DataFrame de una zona en `<carpeta>/clima_<slug>.csv`."""
    ruta = Path(carpeta) / f"clima_{zona.slug}.csv"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ruta, index=False)
    return ruta


def descargar_todas(carpeta: str = "data") -> dict[str, int]:
    """Descarga y guarda las 5 zonas del período fijo. Devuelve slug -> filas guardadas."""
    guardadas: dict[str, int] = {}
    for zona in ZONAS:
        df = descargar_zona(zona, FECHA_INICIO, FECHA_FIN)
        guardar_csv(df, zona, carpeta)
        guardadas[zona.slug] = len(df)
    return guardadas
