"""MODULO DE ENTRADA (unico punto que depende del formato del log).

Formato interno: lista de dicts
    {"tiempo": datetime, "evento_id": 4624|4625, "cuenta": str, "origen": str}

Formatos soportados (supuestos, a confirmar con el log real):
  1. XML de eventos de Security.evtx (Get-WinEvent ... | ForEach {$_.ToXml()} > eventos.xml)
  2. CSV de Export-Csv de Get-WinEvent (columnas TimeCreated, Id, Message)
  3. CSV simple: tiempo,evento_id,cuenta,origen
Si el log real llega con otro formato, solo se modifica este archivo."""
import csv
import re
import xml.etree.ElementTree as ET
from datetime import datetime

NS = {"e": "http://schemas.microsoft.com/win/2004/08/events/event"}
IDS = {4624, 4625}
SIN_ORIGEN = {"", "-", "::1", "127.0.0.1"}


def _tiempo(txt):
    txt = txt.strip().replace("Z", "")
    if "." in txt:                                   # 2026-11-18T15:04:12.1234567
        base, frac = txt.split(".", 1)
        txt = f"{base}.{frac[:6]}"
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S",
                "%d/%m/%Y %H:%M:%S", "%m/%d/%Y %H:%M:%S", "%d/%m/%Y %I:%M:%S %p",
                "%m/%d/%Y %I:%M:%S %p"):
        try:
            return datetime.strptime(txt.replace("p. m.", "PM").replace("a. m.", "AM"), fmt)
        except ValueError:
            continue
    raise ValueError(f"fecha no reconocida: {txt}")


def _registro(tiempo, eid, cuenta, origen):
    if eid not in IDS or not cuenta or cuenta.endswith("$"):   # ignora cuentas de maquina
        return None
    origen = "local" if origen.strip() in SIN_ORIGEN else origen.strip()
    return {"tiempo": tiempo, "evento_id": eid, "cuenta": cuenta, "origen": origen}


def _leer_xml(ruta):
    with open(ruta, encoding="utf-8-sig") as f:
        txt = re.sub(r"<\?xml[^>]*\?>", "", f.read())
    raiz = ET.fromstring(f"<Events>{txt}</Events>")
    salida = []
    for ev in raiz.iter(f"{{{NS['e']}}}Event"):
        eid = int(ev.findtext("e:System/e:EventID", namespaces=NS) or 0)
        t = ev.find("e:System/e:TimeCreated", NS)
        datos = {d.get("Name"): (d.text or "") for d in ev.findall("e:EventData/e:Data", NS)}
        r = _registro(_tiempo(t.get("SystemTime")), eid,
                      datos.get("TargetUserName", ""), datos.get("IpAddress", ""))
        if r:
            salida.append(r)
    return salida


def _leer_csv(ruta):
    salida = []
    with open(ruta, newline="", encoding="utf-8-sig") as f:
        filas = list(csv.DictReader(f))
    if not filas:
        return salida
    cols = {c.lower(): c for c in filas[0]}
    for fila in filas:
        try:
            if "evento_id" in cols:                                   # CSV simple
                r = _registro(_tiempo(fila[cols["tiempo"]]), int(fila[cols["evento_id"]]),
                              fila[cols["cuenta"]], fila[cols["origen"]])
            else:                                                     # Export-Csv de Windows
                msg = fila.get(cols.get("message", ""), "") or ""
                cuentas = re.findall(r"(?:Account Name|Nombre de cuenta):\s+(\S+)", msg)
                ip = re.search(r"(?:Source Network Address|Direcci.n de red de origen):\s+(\S+)", msg)
                r = _registro(_tiempo(fila[cols["timecreated"]]), int(fila[cols["id"]]),
                              cuentas[-1] if cuentas else "", ip.group(1) if ip else "")
        except (KeyError, ValueError):
            continue
        if r:
            salida.append(r)
    return salida


def cargar_eventos(ruta):
    eventos = _leer_xml(ruta) if ruta.lower().endswith(".xml") else _leer_csv(ruta)
    if not eventos:
        raise ValueError("No se encontraron eventos 4624/4625 en el archivo.")
    return eventos


def guardar_csv_simple(eventos, ruta):
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["tiempo", "evento_id", "cuenta", "origen"])
        for e in sorted(eventos, key=lambda e: e["tiempo"]):
            w.writerow([e["tiempo"].strftime("%Y-%m-%dT%H:%M:%S"), e["evento_id"],
                        e["cuenta"], e["origen"]])
