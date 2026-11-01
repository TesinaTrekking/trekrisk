"""Pruebas de core/api.py con una respuesta de ejemplo, sin red."""

import json
from pathlib import Path

import pytest
import requests

from core import api
from core.api import COLUMNAS_CSV, ErrorDescarga, descargar_zona, guardar_csv
from core.config import ZONAS

EJEMPLO = json.loads((Path(__file__).parent / "respuesta_ejemplo.json").read_text())
ZONA = ZONAS[0]


class RespuestaFalsa:
    def __init__(self, datos, status_code=200):
        self._datos = datos
        self.status_code = status_code
        self.text = json.dumps(datos)

    def json(self):
        return self._datos


def test_descargar_zona_arma_el_esquema_del_csv(monkeypatch):
    llamadas = {}

    def falso_get(url, params, timeout):
        llamadas.update(url=url, params=params)
        return RespuestaFalsa(EJEMPLO)

    monkeypatch.setattr(api.requests, "get", falso_get)
    df = descargar_zona(ZONA, "2021-01-01", "2021-01-03")

    assert llamadas["url"] == "https://archive-api.open-meteo.com/v1/archive"
    assert llamadas["params"]["timezone"] == "America/Argentina/Cordoba"
    assert list(df.columns) == COLUMNAS_CSV
    assert len(df) == 3
    assert (df["zona"] == "champaqui").all()
    assert df.loc[1, "precipitacion_mm"] == 4.5
    assert df.loc[2, "tmin_c"] == 9.5


def test_error_http_lanza_error_descarga(monkeypatch):
    error = {"error": True, "reason": "parametro invalido"}
    monkeypatch.setattr(api.requests, "get", lambda *a, **k: RespuestaFalsa(error, 400))
    with pytest.raises(ErrorDescarga, match="parametro invalido"):
        descargar_zona(ZONA, "2021-01-01", "2021-01-03")


def test_sin_conexion_lanza_error_descarga(monkeypatch):
    def sin_red(*a, **k):
        raise requests.ConnectionError("sin red")

    monkeypatch.setattr(api.requests, "get", sin_red)
    with pytest.raises(ErrorDescarga, match="conectar"):
        descargar_zona(ZONA, "2021-01-01", "2021-01-03")


def test_respuesta_sin_variable_lanza_error_descarga(monkeypatch):
    incompleta = {"daily": {"time": ["2021-01-01"], "precipitation_sum": [0.0]}}
    monkeypatch.setattr(api.requests, "get", lambda *a, **k: RespuestaFalsa(incompleta))
    with pytest.raises(ErrorDescarga, match="Faltan variables"):
        descargar_zona(ZONA, "2021-01-01", "2021-01-01")


def test_guardar_csv_escribe_el_archivo(monkeypatch, tmp_path):
    monkeypatch.setattr(api.requests, "get", lambda *a, **k: RespuestaFalsa(EJEMPLO))
    df = descargar_zona(ZONA, "2021-01-01", "2021-01-03")
    ruta = guardar_csv(df, ZONA, str(tmp_path))
    assert ruta.name == "clima_champaqui.csv"
    assert len(ruta.read_text().splitlines()) == 4
