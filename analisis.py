"""Pipeline completo: ventanas -> indicadores -> rareza (KNN) -> seguimiento Bayes."""
from datetime import timedelta
import numpy as np
import config as C
from indicadores import (construir_ventanas, calcular_indicadores, a_vector,
                         senales, indice_ventana)
from knn import DetectorRareza
from bayes_secuencial import SeguimientoBayes


def ejecutar(eventos, ventana_min=C.VENTANA_MIN, fraccion_base=C.FRACCION_BASE,
             k=C.K_VECINOS, umbral=C.UMBRAL_ALERTA, escalar=True, usar_rareza=True):
    """Devuelve (ventanas_analizadas, idx_corte, t0).
    Las ventanas del periodo base solo sirven para aprender lo normal; el analisis
    (rareza, probabilidad, alertas) corre sobre el periodo posterior."""
    t0 = min(e["tiempo"] for e in eventos)
    tf = max(e["tiempo"] for e in eventos)
    idx_max = indice_ventana(tf, t0, ventana_min)
    corte = int((idx_max + 1) * fraccion_base)

    ventanas = construir_ventanas(eventos, t0, ventana_min)
    claves = sorted(ventanas, key=lambda c: (c[1], c[0]))
    inds = {c: calcular_indicadores(ventanas[c]) for c in claves}

    base = [c for c in claves if c[1] < corte]
    prueba = [c for c in claves if c[1] >= corte]
    if len(base) < k + 1:
        raise ValueError("Periodo base muy corto: hay muy pocas ventanas para aprender lo normal.")

    detector = DetectorRareza(k=k, escalar=escalar).ajustar([a_vector(inds[c]) for c in base])
    rarezas = detector.puntajes([a_vector(inds[c]) for c in prueba])

    seg = SeguimientoBayes(C.PRIOR_ATAQUE, C.EVIDENCIA_EXPERTA, C.LIMITES_PROB)
    resultado = []
    for c, r in zip(prueba, rarezas):
        s = senales(inds[c], r, usar_rareza)
        p = seg.actualizar(c[0], s)
        resultado.append({
            "origen": c[0], "idx": c[1],
            "t_inicio": t0 + timedelta(minutes=c[1] * ventana_min),
            "ind": inds[c], "rareza": float(r),
            "senales": [n for n, v in s.items() if v],
            "prob": p, "alerta": p >= umbral,
        })
    return resultado, corte, t0
