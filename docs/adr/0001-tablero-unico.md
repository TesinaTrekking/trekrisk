# Tablero único en lugar de ocho pantallas

La interfaz pasa de 8 pantallas, una por tema de la materia, a un único tablero con una fila de métricas y una grilla de tarjetas, inspirado en la demo de Seattle Weather de Streamlit. Se priorizan las métricas bien presentadas; la explicación teórica (fórmulas, probabilidad clásica contra frecuencial) se desarrolla en la presentación y no en la app. Se mantienen las 5 zonas, con selección múltiple, porque la comparación entre zonas es la pregunta central del proyecto.

## Consecuencias

- La app no descarga datos: los CSV versionados son datos de archivo. `core/api.py` queda solo como registro de procedencia, sin conexión a la interfaz.
- La semilla del experimento es una constante en `core/config.py` y no aparece en la interfaz.
- La probabilidad clásica y el sorteo equiprobable quedan en `core/` sin pantalla en la app.
