"""Detector de actividad sospechosa en Active Directory (Fundamentos de IA).

  python main.py                       -> demo con datos SIMULADOS + evaluacion
  python main.py --log eventos.xml     -> analiza un log real (sin evaluacion: no hay etiquetas)
  python main.py --guardar-ejemplo     -> escribe salida/ejemplo_eventos.csv (formato de entrada)
"""
import argparse
import os
import config as C
import analisis, entrada, evaluacion, reporte, simulador


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", help="archivo .xml o .csv con eventos 4624/4625")
    ap.add_argument("--ventana", type=int, default=C.VENTANA_MIN, help="minutos por ventana")
    ap.add_argument("--semilla", type=int, default=7, help="semilla del simulador")
    ap.add_argument("--guardar-ejemplo", action="store_true")
    a = ap.parse_args()

    print(C.DISCLAIMER)
    os.makedirs("salida", exist_ok=True)

    if a.log:
        eventos = entrada.cargar_eventos(a.log)
        ventanas, corte, t0 = analisis.ejecutar(eventos, a.ventana)
        print(f"{len(eventos)} eventos leidos. Periodo base (aprendizaje): primeras {corte} ventanas.")
        reporte.imprimir_alertas(ventanas)
        reporte.guardar_alertas_csv(ventanas, "salida/alertas.csv")
        top = [(e["origen"], f"Prob. max {e['prob_max']:.0%}")
               for e in reporte.resumen_entidades(ventanas)[:3]]
        reporte.graficar_evolucion(ventanas, top, "salida/evolucion.png")
        print("\nSin etiquetas no se calculan metricas. Archivos: salida/alertas.csv, salida/evolucion.png")
        return

    eventos, ataques = simulador.generar(a.semilla)
    if a.guardar_ejemplo:
        entrada.guardar_csv_simple(eventos, "salida/ejemplo_eventos.csv")
        print("Guardado salida/ejemplo_eventos.csv")
    print(f"[SIMULADO] {len(eventos)} eventos, {len(ataques)} ataques inyectados.")

    filas, ventanas, corte, t0, et = evaluacion.comparar(eventos, ataques, a.ventana)
    print(f"Periodo base (aprendizaje): primeras {corte} ventanas. "
          f"Evaluacion sobre {len(ventanas)} ventanas posteriores.")
    reporte.imprimir_metricas(filas)
    reporte.imprimir_alertas(ventanas, ataques=ataques)
    reporte.guardar_alertas_csv(ventanas, "salida/alertas.csv")

    elegidas = [(ataques[0]["origen"], "Fuerza bruta intensa"),
                (ataques[3]["origen"], "Password spraying lento"),
                ("10.0.5.20", "Servicio con contrasena vencida (NO es ataque)")]
    reporte.graficar_evolucion(ventanas, elegidas, "salida/evolucion.png")
    print("\nArchivos: salida/alertas.csv, salida/evolucion.png")


if __name__ == "__main__":
    main()
