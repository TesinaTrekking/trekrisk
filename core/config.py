"""Configuración del proyecto: zonas, período, umbrales y constantes."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Zona:
    """Punto de trekking con su ubicación."""

    slug: str
    nombre: str
    latitud: float
    longitud: float


ZONAS: tuple[Zona, ...] = (
    Zona("champaqui", "Cerro Champaquí", -31.97, -64.93),
    Zona("uritorco", "Cerro Uritorco", -30.84, -64.46),
    Zona("condorito", "Quebrada del Condorito", -31.65, -64.64),
    Zona("pan_de_azucar", "Pan de Azúcar", -31.24, -64.46),
    Zona("los_gigantes", "Los Gigantes", -31.57, -64.80),
)

FECHA_INICIO = "2021-01-01"
FECHA_FIN = "2025-12-31"
DIAS_ESPERADOS = 1826

EPSILON_INDEPENDENCIA = 0.02
MIN_CASOS = 30
SEMILLA = 42


@dataclass(frozen=True)
class Umbrales:
    """Umbrales que definen los eventos climáticos (editables en la interfaz)."""

    lluvia_mm: float = 1.0
    viento_kmh: float = 30.0
    calor_c: float = 32.0
    helada_c: float = 0.0
