"""Parametros del sistema. Todo lo que el equipo "decide" vive aqui."""

# ---------------------------------------------------------------- general
VENTANA_MIN = 5            # tamano de la ventana de tiempo (minutos)
FRACCION_BASE = 0.5        # primera parte del log usada para aprender lo "normal"
K_VECINOS = 5              # hiperparametro k del KNN

# ------------------------------------------------- seguimiento bayesiano
PRIOR_ATAQUE = 0.01        # probabilidad inicial de que una entidad sea atacante
UMBRAL_ALERTA = 0.80       # probabilidad a partir de la cual se marca "sospechoso"
LIMITES_PROB = (0.005, 0.995)   # evita que la probabilidad se "atore" en 0 o 1
                                # (permite que baje si la actividad vuelve a la normalidad)

# ---------------------------------------- umbrales de las senales (experto)
RAREZA_ALTA = 0.95         # puntaje KNN a partir del cual una ventana es "rara"
FALLOS_ALTOS = 8           # fallos de acceso en una ventana
CUENTAS_MULTIPLES = 4      # cuentas distintas con fallo desde un mismo origen
TASA_FALLOS_ALTA = 0.80    # proporcion de fallos...
MIN_FALLOS_TASA = 3        # ...siempre que haya al menos estos fallos
FALLOS_PREVIOS_EXITO = 3   # fallos seguidos antes de un acceso exitoso

# -------------------------------------------- evidencia definida por experto
# senal -> (P(senal | ataque), P(senal | normal))
# SON SUPUESTOS DEL EQUIPO, no estan aprendidos de datos etiquetados.
EVIDENCIA_EXPERTA = {
    "rareza_alta":       (0.85, 0.05),
    "fallos_altos":      (0.50, 0.01),
    "cuentas_multiples": (0.50, 0.01),
    "tasa_fallos_alta":  (0.80, 0.05),
    "exito_tras_fallos": (0.30, 0.02),
}

# ------------------------------------------------------ linea base (regla)
REGLA_SIMPLE_FALLOS = 10   # "mas de 10 fallos en una ventana = alerta"

DISCLAIMER = """
================================================================================
  AVISO IMPORTANTE
  Este sistema se desarrollo SIN CONOCER el formato real de los logs de entrada.
  La estructura de datos es una suposicion de trabajo (eventos 4624 y 4625 de
  Security.evtx). Primero se implementaron los algoritmos del curso; despues se
  revisa que insumo necesita y se adapta unicamente el modulo de entrada.
  - No hay datos etiquetados ni entrenamiento previo: el sistema aprende lo
    "normal" del propio servidor y las probabilidades de evidencia las definio
    el equipo (conocimiento experto).
  - La evaluacion usa DATOS SIMULADOS con ataques inyectados. Las metricas NO
    representan desempeno en un entorno real.
  - Una alerta es una ayuda para el analista, no un veredicto.
================================================================================
"""
