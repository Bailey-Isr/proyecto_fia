"""Preparacion "a fuerza bruta": agrupar por (origen, ventana) y contar.
Tema del curso: Feature Engineering."""
from collections import defaultdict
import config as C

NOMBRES = ["fallos", "exitos", "cuentas_fallidas", "tasa_fallos", "exito_tras_fallos"]


def indice_ventana(t, t0, ventana_min):
    return int((t - t0).total_seconds() // (ventana_min * 60))


def construir_ventanas(eventos, t0, ventana_min):
    """Devuelve {(origen, idx_ventana): [eventos ordenados por tiempo]}."""
    ventanas = defaultdict(list)
    for e in sorted(eventos, key=lambda e: e["tiempo"]):
        ventanas[(e["origen"], indice_ventana(e["tiempo"], t0, ventana_min))].append(e)
    return ventanas


def calcular_indicadores(evs):
    fallos = sum(1 for e in evs if e["evento_id"] == 4625)
    exitos = sum(1 for e in evs if e["evento_id"] == 4624)
    cuentas = {e["cuenta"] for e in evs if e["evento_id"] == 4625}
    # correlacion de eventos: varios fallos seguidos y luego un acceso exitoso
    seguidos, exito_tras = 0, 0
    for e in evs:
        if e["evento_id"] == 4625:
            seguidos += 1
        else:
            if seguidos >= C.FALLOS_PREVIOS_EXITO:
                exito_tras = 1
            seguidos = 0
    total = fallos + exitos
    return {
        "fallos": fallos,
        "exitos": exitos,
        "cuentas_fallidas": len(cuentas),
        "tasa_fallos": fallos / total if total else 0.0,
        "exito_tras_fallos": exito_tras,
    }


def a_vector(ind):
    return [float(ind[n]) for n in NOMBRES]


def senales(ind, rareza, usar_rareza=True):
    """Convierte indicadores en senales verdadero/falso (la evidencia)."""
    s = {
        "fallos_altos": ind["fallos"] >= C.FALLOS_ALTOS,
        "cuentas_multiples": ind["cuentas_fallidas"] >= C.CUENTAS_MULTIPLES,
        "tasa_fallos_alta": (ind["fallos"] >= C.MIN_FALLOS_TASA
                             and ind["tasa_fallos"] >= C.TASA_FALLOS_ALTA),
        "exito_tras_fallos": bool(ind["exito_tras_fallos"]),
    }
    if usar_rareza:
        s["rareza_alta"] = rareza >= C.RAREZA_ALTA
    return s
