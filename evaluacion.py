"""Evaluacion con ataques simulados: matriz de confusion, precision, recall, F1,
comparacion contra linea base y retraso de deteccion.
Tema del curso: metricas, hiperparametros, efecto del escalamiento."""
from datetime import timedelta
import config as C
from indicadores import indice_ventana
import analisis


def etiquetas_de_ataques(ataques, t0, ventana_min):
    """Conjunto de (origen, idx) que son ataque, segun lo inyectado."""
    et = set()
    for a in ataques:
        for i in range(indice_ventana(a["ini"], t0, ventana_min),
                       indice_ventana(a["fin"], t0, ventana_min) + 1):
            et.add((a["origen"], i))
    return et


def _metricas(ventanas, alerta, etiquetas):
    vp = fp = fn = vn = 0
    for v in ventanas:
        real, pred = (v["origen"], v["idx"]) in etiquetas, alerta(v)
        if real and pred: vp += 1
        elif pred: fp += 1
        elif real: fn += 1
        else: vn += 1
    prec = vp / (vp + fp) if vp + fp else 0.0
    rec = vp / (vp + fn) if vp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return {"VP": vp, "FP": fp, "FN": fn, "VN": vn, "precision": prec, "recall": rec, "f1": f1}


def _retraso(ventanas, alerta, ataques, t0, ventana_min):
    """Cuantas ventanas pasan desde que inicia un ataque hasta la primera alerta."""
    retrasos = []
    for a in ataques:
        ini = indice_ventana(a["ini"], t0, ventana_min)
        fin = indice_ventana(a["fin"], t0, ventana_min)
        hits = [v["idx"] for v in ventanas
                if v["origen"] == a["origen"] and ini <= v["idx"] <= fin and alerta(v)]
        retrasos.append(min(hits) - ini if hits else None)
    detectados = [r for r in retrasos if r is not None]
    return len(detectados), len(retrasos), (sum(detectados) / len(detectados) if detectados else None)


def comparar(eventos, ataques, ventana_min=C.VENTANA_MIN):
    completo, corte, t0 = analisis.ejecutar(eventos, ventana_min)
    sin_escalar, _, _ = analisis.ejecutar(eventos, ventana_min, escalar=False)
    sin_rareza, _, _ = analisis.ejecutar(eventos, ventana_min, usar_rareza=False)
    et = etiquetas_de_ataques(ataques, t0, ventana_min)

    configs = [
        ("Linea base: regla de umbral", completo, lambda v: v["ind"]["fallos"] >= C.REGLA_SIMPLE_FALLOS),
        ("Solo KNN (rareza)", completo, lambda v: v["rareza"] >= C.RAREZA_ALTA),
        ("Bayes secuencial sin KNN", sin_rareza, lambda v: v["alerta"]),
        ("Bayes + KNN sin escalar", sin_escalar, lambda v: v["alerta"]),
        ("Bayes + KNN escalado (completo)", completo, lambda v: v["alerta"]),
    ]
    filas = []
    for nombre, ventanas, alerta in configs:
        m = _metricas(ventanas, alerta, et)
        det, tot, ret = _retraso(ventanas, alerta, ataques, t0, ventana_min)
        m.update(nombre=nombre, detectados=det, total_ataques=tot, retraso=ret)
        filas.append(m)
    return filas, completo, corte, t0, et
