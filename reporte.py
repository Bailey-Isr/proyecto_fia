"""Salidas: tabla de metricas, tabla de alertas y grafica de evolucion."""
import csv
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import config as C


def imprimir_metricas(filas):
    print(f"\n{'Configuracion':<34}{'VP':>5}{'FP':>5}{'FN':>5}{'VN':>6}"
          f"{'Prec.':>8}{'Recall':>8}{'F1':>7}{'Detect.':>9}{'Retraso':>9}")
    print("-" * 100)
    for f in filas:
        ret = "-" if f["retraso"] is None else f"{f['retraso']:.1f}"
        print(f"{f['nombre']:<34}{f['VP']:>5}{f['FP']:>5}{f['FN']:>5}{f['VN']:>6}"
              f"{f['precision']:>8.2f}{f['recall']:>8.2f}{f['f1']:>7.2f}"
              f"{str(f['detectados']) + '/' + str(f['total_ataques']):>9}{ret:>9}")
    print("(Retraso = ventanas promedio entre el inicio del ataque y la primera alerta)")


def resumen_entidades(ventanas):
    ent = {}
    for v in ventanas:
        e = ent.setdefault(v["origen"], {"origen": v["origen"], "prob_max": 0.0,
                                         "ventanas_alerta": 0, "primera_alerta": None,
                                         "senales": []})
        if v["prob"] > e["prob_max"]:
            e["prob_max"], e["senales"] = v["prob"], v["senales"]
        if v["alerta"]:
            e["ventanas_alerta"] += 1
            e["primera_alerta"] = e["primera_alerta"] or v["t_inicio"]
    return sorted(ent.values(), key=lambda e: -e["prob_max"])


def imprimir_alertas(ventanas, top=10, ataques=None):
    ent = resumen_entidades(ventanas)
    reales = {a["origen"]: a["tipo"] for a in (ataques or [])}
    print(f"\nTop {top} entidades por probabilidad maxima de ataque (umbral {C.UMBRAL_ALERTA:.0%})")
    print(f"{'Origen':<14}{'P.max':>7}{'Alerta':>8}{'Primera alerta':>18}  Senales que la motivaron")
    print("-" * 100)
    for e in ent[:top]:
        marca = " <- ataque simulado: " + reales[e["origen"]] if e["origen"] in reales else ""
        pa = e["primera_alerta"].strftime("%H:%M") if e["primera_alerta"] else "-"
        print(f"{e['origen']:<14}{e['prob_max']:>7.0%}{('SI' if e['primera_alerta'] else 'no'):>8}"
              f"{pa:>18}  {', '.join(e['senales']) or '-'}{marca}")


def guardar_alertas_csv(ventanas, ruta):
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["inicio_ventana", "origen", "probabilidad", "rareza_knn", "fallos",
                    "cuentas_fallidas", "senales"])
        for v in ventanas:
            if v["alerta"]:
                w.writerow([v["t_inicio"].strftime("%Y-%m-%d %H:%M"), v["origen"],
                            f"{v['prob']:.3f}", f"{v['rareza']:.3f}", v["ind"]["fallos"],
                            v["ind"]["cuentas_fallidas"], "|".join(v["senales"])])


def graficar_evolucion(ventanas, entidades, ruta):
    """entidades: lista de (origen, titulo). Muestra como cambia la probabilidad."""
    fig, ejes = plt.subplots(len(entidades), 1, figsize=(9, 2.6 * len(entidades)), sharex=True)
    if len(entidades) == 1:
        ejes = [ejes]
    for ax, (origen, titulo) in zip(ejes, entidades):
        pts = [(v["t_inicio"], v["prob"]) for v in ventanas if v["origen"] == origen]
        if not pts:
            continue
        ax.plot([p[0] for p in pts], [p[1] for p in pts], marker="o", ms=3, lw=1.5)
        ax.axhline(C.UMBRAL_ALERTA, color="red", ls="--", lw=1, label="umbral de alerta")
        ax.set_ylim(-0.02, 1.02)
        ax.set_ylabel("P(ataque)")
        ax.set_title(f"{titulo} ({origen})", fontsize=10, loc="left")
        ax.grid(alpha=0.3)
    ejes[0].legend(loc="center left", fontsize=8)
    ejes[-1].set_xlabel("Tiempo (inicio de cada ventana)")
    fig.suptitle("Evolucion de la probabilidad de ataque por entidad", fontsize=12)
    fig.text(0.5, 0.005, "DATOS SIMULADOS / parametros definidos por el equipo - no representa desempeno real",
             ha="center", fontsize=8, color="gray")
    fig.tight_layout(rect=(0, 0.02, 1, 0.97))
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
