# Detector de actividad sospechosa en Active Directory

Proyecto de Fundamentos de IA. Implementa los algoritmos del curso y deja la entrada de datos aislada.

> **AVISO:** el sistema se desarrolló sin conocer el formato real de los logs. La entrada es una suposición
> (eventos 4624/4625 de `Security.evtx`). No hay datos etiquetados ni entrenamiento previo. La evaluación usa
> **datos simulados**: las métricas no representan desempeño real. Una alerta es apoyo al analista, no un veredicto.

## Uso
```
pip install numpy matplotlib
python main.py                      # demo simulado + evaluación
python main.py --log eventos.xml    # log real (.xml o .csv), sin métricas
python main.py --guardar-ejemplo    # genera salida/ejemplo_eventos.csv
```

## Cómo funciona
1. `entrada.py` lee eventos 4624/4625 (XML, CSV de `Export-Csv` o CSV simple). **Es el único archivo que depende del formato.**
2. `indicadores.py` agrupa por origen (IP) y ventana de 5 min y cuenta fallos, éxitos, cuentas distintas, tasa de fallos y "éxito tras fallos".
3. `knn.py` (desde cero) aprende lo normal del propio servidor con la primera mitad del log y da un puntaje de rareza entre 0 y 1.
4. `bayes_secuencial.py` acumula evidencia ventana tras ventana por IP (actualización Bayesiana). La probabilidad puede subir y bajar.
5. Si la probabilidad supera el umbral (0.80) la entidad se marca **sospechosa** (salida binaria).
6. `evaluacion.py` compara contra una regla de umbral simple y ablaciones (sin KNN, sin escalar) usando ataques simulados.

## Temas del curso
Feature engineering y escalamiento · KNN desde cero e hiperparámetro k · regla de Bayes y actualización Bayesiana ·
clasificador Bayesiano · métricas (precisión, recall, F1, matriz de confusión) · línea base.

## Supuestos y limitaciones
- Las probabilidades de evidencia (`config.py`) las definió el equipo; no se aprendieron de datos.
- "Raro" no siempre es "malicioso": el servicio con contraseña vencida del simulador es un falso positivo intencional.
- Si el servidor ya estaba comprometido durante el periodo base, se tomará como normal.
- Escalar el KNN cambia los puntajes pero, con estos datos, no cambió las decisiones finales.
