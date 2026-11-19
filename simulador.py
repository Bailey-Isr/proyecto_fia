"""Generador de logs SIMULADOS (actividad normal + ataques inyectados).
Solo sirve para probar el sistema: el detector nunca ve las etiquetas."""
import random
from datetime import datetime, timedelta


def generar(semilla=7, horas=12, inicio=datetime(2026, 11, 18, 8, 0, 0)):
    rnd = random.Random(semilla)
    ev, ataques = [], []
    fin = inicio + timedelta(hours=horas)
    minutos = horas * 60

    def add(t, eid, cuenta, origen):
        ev.append({"tiempo": t, "evento_id": eid, "cuenta": cuenta, "origen": origen})

    def en(m):                                    # minuto relativo -> datetime
        return inicio + timedelta(minutes=m, seconds=rnd.randint(0, 59))

    # ---- actividad normal: 25 estaciones, un usuario por estacion
    for i in range(25):
        ip, user = f"10.0.1.{10 + i}", f"user{i:02d}"
        m = rnd.uniform(0, 30)
        while m < minutos:
            if rnd.random() < 0.06:               # error de captura
                add(en(m), 4625, user, ip)
                add(en(m + 0.3), 4624, user, ip)
            else:
                add(en(m), 4624, user, ip)
            m += rnd.uniform(15, 45)

    # ---- puerta de enlace / VPN: muchos usuarios desde una misma IP
    m = 0.0
    while m < minutos:
        user = f"vpn{rnd.randint(0, 29):02d}"
        add(en(m), 4625 if rnd.random() < 0.03 else 4624, user, "10.0.9.1")
        m += rnd.uniform(0.5, 2.0)

    # ---- olvidos de contrasena: 2 a 4 fallos y luego acceso exitoso
    for _ in range(int(horas * 1.5)):
        i = rnd.randint(0, 24)
        ip, user, m = f"10.0.1.{10 + i}", f"user{i:02d}", rnd.uniform(0, minutos - 5)
        for j in range(rnd.randint(2, 4)):
            add(en(m + j * 0.3), 4625, user, ip)
        add(en(m + 1.5), 4624, user, ip)

    # ---- (periodo de prueba) servicio con contrasena vencida: NO es ataque
    ini_srv = minutos * 0.62
    for j in range(30):
        add(en(ini_srv + j), 4625, "svc_respaldo", "10.0.5.20")

    # ---- ataques inyectados (todos en la segunda mitad)
    def ataque(tipo, origen, m_ini, m_fin):
        ataques.append({"tipo": tipo, "origen": origen,
                        "ini": inicio + timedelta(minutes=m_ini),
                        "fin": inicio + timedelta(minutes=m_fin)})

    # fuerza bruta intensa: una cuenta, muchisimos fallos
    m0 = minutos * 0.58
    for j in range(60):
        add(en(m0 + j * 0.1), 4625, "administrator", "10.0.200.7")
    add(en(m0 + 7), 4624, "administrator", "10.0.200.7")
    ataque("fuerza_bruta", "10.0.200.7", m0, m0 + 8)

    # fuerza bruta lenta: pocos fallos por ventana, sostenido
    m0 = minutos * 0.70
    for j in range(15):
        for q in range(4):
            add(en(m0 + j * 5 + q), 4625, "sqlsvc", "10.0.200.13")
    ataque("fuerza_bruta", "10.0.200.13", m0, m0 + 75)

    # password spraying rapido: muchas cuentas, un intento cada una
    m0 = minutos * 0.78
    for j in range(25):
        add(en(m0 + j * 0.1), 4625, f"user{j:02d}", "10.0.200.11")
    ataque("spraying", "10.0.200.11", m0, m0 + 3)

    # password spraying lento: pocas cuentas por ventana, sostenido (evade regla de umbral)
    m0 = minutos * 0.84
    for j in range(12):
        for q in range(6):
            add(en(m0 + j * 5 + q * 0.8), 4625, f"user{(j * 6 + q) % 25:02d}", "10.0.200.9")
    add(en(m0 + 60), 4624, "user03", "10.0.200.9")
    ataque("spraying", "10.0.200.9", m0, m0 + 61)

    return [e for e in ev if inicio <= e["tiempo"] < fin], ataques
