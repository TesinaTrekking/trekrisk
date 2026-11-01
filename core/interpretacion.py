"""Textos interpretativos en español (Argentina) para cada resultado."""

import math

import pandas as pd

from core.config import EPSILON_INDEPENDENCIA, MIN_CASOS, ZONAS
from core.probabilidad import Resultado, ResultadoIndependencia
from core.simulacion import ResultadoSimulacion

_MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
          "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
_NOMBRE_ZONA = {z.slug: z.nombre for z in ZONAS}
_ADVERTENCIA = f"Atención: se basa en menos de {MIN_CASOS} casos."


def _vacio(x: float | None) -> bool:
    return x is None or (isinstance(x, float) and math.isnan(x))


def pct(x: float | None) -> str:
    """Formatea una proporción como porcentaje argentino: 0.123 -> '12,3 %'."""
    if _vacio(x):
        return "sin datos"
    return f"{x * 100:.1f}".replace(".", ",") + " %"


def _puntos(x: float) -> str:
    """Diferencia de proporciones en puntos porcentuales: 0.167 -> '16,7'."""
    return f"{abs(x) * 100:.1f}".replace(".", ",")


def _entero(x: int) -> str:
    """Entero con punto como separador de miles."""
    return f"{x:,}".replace(",", ".")


def _casos(r: Resultado) -> str:
    return f"{_entero(r.favorables)} de {_entero(r.totales)}"


def texto_frecuencia(nombre_evento: str, r: Resultado, contexto: str = "") -> str:
    """Frecuencia relativa de un evento, con favorables y totales."""
    if r.valor is None:
        return f"No hay días para calcular la frecuencia de {nombre_evento}{contexto}."
    texto = (f"{nombre_evento.capitalize()} ocurrió en {pct(r.valor)} de los días{contexto} "
             f"({_casos(r)} casos).")
    return f"{texto} {_ADVERTENCIA}" if r.poca_muestra else texto


def texto_clasica(nombre_evento: str, r: Resultado, sorteo: str) -> str:
    """Probabilidad clásica: casos favorables sobre casos posibles de un sorteo equiprobable."""
    if r.valor is None:
        return f"No hay casos posibles en el sorteo de {sorteo}."
    texto = (f"Si se sortea {sorteo} con todos los casos equiprobables, la probabilidad de "
             f"{nombre_evento} es {pct(r.valor)} ({_casos(r)} casos favorables sobre posibles). "
             "Es un cálculo exacto dentro del registro.")
    return f"{texto} {_ADVERTENCIA}" if r.poca_muestra else texto


def texto_frecuencial(nombre_evento: str, r: Resultado) -> str:
    """Probabilidad frecuencial: la frecuencia observada como estimación de un día futuro."""
    if r.valor is None:
        return f"No hay días en el registro para estimar la probabilidad de {nombre_evento}."
    texto = (f"Según el historial, la probabilidad estimada de {nombre_evento} para un día "
             f"futuro es {pct(r.valor)} ({_casos(r)} casos). Es una estimación: depende de "
             "que el clima futuro se comporte como el registrado.")
    return f"{texto} {_ADVERTENCIA}" if r.poca_muestra else texto


def texto_condicional(nombre_a: str, nombre_b: str, cond: Resultado, base: Resultado) -> str:
    """P(A | B) frente a P(A); `nombre_b` va como condición, por ejemplo 'es invierno'."""
    if cond.valor is None:
        return (f"No se puede calcular: la condición «{nombre_b}» no ocurre en ningún día "
                "del registro.")
    texto = (f"Cuando {nombre_b}, la probabilidad de {nombre_a} es {pct(cond.valor)} "
             f"(n = {_entero(cond.totales)}), frente a {pct(base.valor)} en general.")
    if base.valor is not None:
        diferencia = cond.valor - base.valor
        if abs(diferencia) < EPSILON_INDEPENDENCIA:
            texto += (f" La probabilidad casi no cambia: la diferencia es de "
                      f"{_puntos(diferencia)} puntos porcentuales.")
        else:
            sentido = "más" if diferencia > 0 else "menos"
            texto += (f" Con esa condición, {nombre_a} es {sentido} probable, con "
                      f"{_puntos(diferencia)} puntos porcentuales de diferencia.")
    return f"{texto} {_ADVERTENCIA}" if cond.poca_muestra else texto


def texto_independencia(nombre_a: str, nombre_b: str, r: ResultadoIndependencia,
                        epsilon: float) -> str:
    """Veredicto de independencia con P(A ∩ B), P(A)·P(B) y la tolerancia epsilon."""
    if r.casos == 0:
        return f"No hay días en común para evaluar {nombre_a} y {nombre_b}."
    comparacion = "menor" if r.independientes else "mayor o igual"
    veredicto = "se consideran independientes" if r.independientes else "no se consideran independientes"
    texto = (f"P({nombre_a} ∩ {nombre_b}) = {pct(r.p_ab)} y "
             f"P({nombre_a})·P({nombre_b}) = {pct(r.producto)} (n = {_entero(r.casos)}). "
             f"La diferencia es de {_puntos(r.diferencia)} puntos, {comparacion} que "
             f"ε = {_puntos(epsilon)} puntos, por lo que {veredicto}.")
    if r.p_a_dado_b is not None:
        texto += (f" P({nombre_a} | {nombre_b}) = {pct(r.p_a_dado_b)} frente a "
                  f"P({nombre_a}) = {pct(r.p_a)}.")
    return f"{texto} {_ADVERTENCIA}" if r.casos < MIN_CASOS else texto


def texto_simulacion(r: ResultadoSimulacion, nombre_evento: str) -> str:
    """Compara la frecuencia del remuestreo con la probabilidad del registro."""
    if _vacio(r.frecuencia_final):
        return f"No hay días en el registro para simular {nombre_evento}."
    diferencia = r.frecuencia_final - r.probabilidad_registro
    texto = (f"Con {_entero(r.n)} sorteos con reposición de días reales, "
             f"la frecuencia de {nombre_evento} fue {pct(r.frecuencia_final)}, frente a "
             f"{pct(r.probabilidad_registro)} en el registro: {_puntos(diferencia)} puntos de "
             "diferencia. Al aumentar N, la frecuencia tiende a la del registro.")
    return f"{texto} {_ADVERTENCIA}" if r.n < MIN_CASOS else texto


def texto_poca_muestra() -> str:
    """Aviso corto para métricas que se basan en pocos casos."""
    return f"⚠️ Menos de {MIN_CASOS} casos."


def texto_leyenda_eventos(letras: dict[str, str], nombres: dict[str, str]) -> str:
    """Leyenda de letras y eventos: 'A = lluvia · B = viento fuerte'."""
    return " · ".join(f"{letra} = {nombres[evento]}" for evento, letra in letras.items())


def texto_espacio_muestral(apto: Resultado) -> str:
    """Explica las letras de los 8 resultados y la frecuencia del día apto."""
    return ("A: lluvia, B: viento fuerte, C: temperatura extrema. "
            + texto_frecuencia("un día apto", apto))


def texto_matriz_independencia(matriz: pd.DataFrame, epsilon: float = EPSILON_INDEPENDENCIA) -> str:
    """Resume cuántos pares de eventos se consideran independientes."""
    if matriz.empty:
        return "No hay pares de eventos para evaluar."
    independientes = int(matriz["independientes"].sum())
    texto = (f"{independientes} de {len(matriz)} pares de eventos se consideran independientes "
             f"(diferencia menor que ε = {_puntos(epsilon)} puntos).")
    return f"{texto} {_ADVERTENCIA}" if matriz["casos"].min() < MIN_CASOS else texto


def texto_mapa_calor(matriz: pd.DataFrame) -> str:
    """Avisa cuántas celdas zona-mes del mapa de calor tienen pocos casos."""
    if matriz.empty:
        return "No hay datos para armar el mapa de calor."
    pocas = int((matriz["totales"] < MIN_CASOS).sum())
    texto = "Cada celda es la probabilidad de un día apto en esa zona y ese mes."
    if pocas:
        texto += (f" {pocas} de {len(matriz)} celdas tienen menos de {MIN_CASOS} casos y "
                  "conviene interpretarlas con cuidado.")
    return texto


def _combinacion(fila: pd.Series) -> str:
    zona = _NOMBRE_ZONA.get(fila["zona"], str(fila["zona"]))
    mes = _MESES[int(fila["mes"]) - 1]
    return (f"{zona} en {mes} ({pct(fila['probabilidad'])}, "
            f"{_entero(int(fila['favorables']))} de {_entero(int(fila['totales']))} días)")


def texto_recomendacion(ranking: pd.DataFrame) -> str:
    """Resume la mejor y la peor combinación zona-mes del ranking (ordenado de mayor a menor)."""
    if ranking.empty:
        return "No hay datos para recomendar una zona y un mes."
    mejor, peor = ranking.iloc[0], ranking.iloc[-1]
    texto = (f"La mejor combinación es {_combinacion(mejor)}. "
             f"La peor es {_combinacion(peor)}.")
    if min(mejor["totales"], peor["totales"]) < MIN_CASOS:
        texto += f" {_ADVERTENCIA}"
    return texto
