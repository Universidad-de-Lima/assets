import pandas as pd
import json
from datetime import datetime

INPUT = "data/_Encuesta_estudiantil_2025.txt"
OUT = "output/"

respuestas_texto = [
    "Totalmente satisfecho",
    "Muy satisfecho",
    "Satisfecho",
    "Insatisfecho",
    "Totalmente insatisfecho",
    "No utilizo",
    "No conozco"
]

# -----------------------
# Leer data
# -----------------------
df = pd.read_csv(INPUT, sep=None, engine="python")

# -----------------------
# Catálogo Carrera → Facultad
# -----------------------
carrera_facultad = {
    "Arquitectura": "Facultad de Arquitectura",
    "Administración": "Facultad de Ciencias Empresariales",
    "Contabilidad y Finanzas": "Facultad de Ciencias Empresariales",
    "Marketing": "Facultad de Ciencias Empresariales",
    "Negocios Internacionales": "Facultad de Ciencias Empresariales",
    "Comunicación": "Facultad de Comunicación",
    "Derecho": "Facultad de Derecho",
    "Economía": "Facultad de Economía",
    "Ingeniería Ambiental": "Facultad de Ingeniería",
    "Ingeniería Civil": "Facultad de Ingeniería",
    "Ingeniería de Sistemas": "Facultad de Ingeniería",
    "Ingeniería Industrial": "Facultad de Ingeniería",
    "Ingeniería Mecatrónica": "Facultad de Ingeniería",
    "Psicología": "Facultad de Psicología"
}

df["Facultad"] = df["Carrera"].map(carrera_facultad)

# -----------------------
# Catálogo dimensión → categoría
# -----------------------
categoria_dim = {
    "Perfil del egreso de la carrera": "Académico",
    "Calidad de la enseñanza en la carrera": "Académico",
    "Plan curricular y perfil de egreso": "Académico",
    "Cursos del programa y contenidos": "Académico",
    "Evaluación del aprendizaje": "Académico",
    "Intercambio estudiantil": "Académico",
    "Servicio médico y su infraestructura": "Administrativo y Bienestar",
    "Material bibliográfico en la biblioteca": "Administrativo y Bienestar",
    "Talleres de actividades artísticas y culturales": "Administrativo y Bienestar",
    "Atención del personal administrativo": "Administrativo y Bienestar",
    "Actividades deportivas": "Administrativo y Bienestar",
    "Información sobre tu récord académico": "Administrativo y Bienestar",
    "Servicio de atención psicopedagógica": "Administrativo y Bienestar",
    "Ayuda financiera": "Administrativo y Bienestar",
    "Condiciones ambientales en laboratorios": "Infraestructura",
    "Equipamiento tecnológico en laboratorios": "Infraestructura",
    "Aulas de clase": "Infraestructura",
    "Ambientes y aulas para estudio": "Infraestructura",
    "Aula virtual": "Tecnología",
    "Software especializado empleado en la carrera": "Tecnología",
    "Soporte técnico del sistema informático": "Tecnología",
    "Portal web de la Universidad (MiUlima)": "Tecnología",
    "Conexión WiFi en el campus": "Tecnología",
}

# -----------------------
# Funciones auxiliares
# -----------------------
def calc_nps(promotores, pasivos, detractores):
    """Calcula NPS score"""
    total = promotores + pasivos + detractores
    if total == 0:
        return 0.0
    return round(((promotores - detractores) / total) * 100, 2)

def calc_csat(t3b, total):
    """Calcula CSAT score (Top 3 Box %)"""
    if total == 0:
        return 0.0
    return round((t3b / total) * 100, 2)

def get_t3b(row):
    """Obtiene suma de Top 3 Box"""
    return (row.get("Totalmente satisfecho", 0) + 
            row.get("Muy satisfecho", 0) + 
            row.get("Satisfecho", 0))

def get_b2b(row):
    """Obtiene suma de Bottom 2 Box"""
    return (row.get("Insatisfecho", 0) + 
            row.get("Totalmente insatisfecho", 0))

# =========================================================
# 1. resumen.json (con métricas pre-calculadas)
# =========================================================
df["Inicio"] = pd.to_datetime(df["Inicio"], dayfirst=True, errors="coerce")
df["Fin"] = pd.to_datetime(df["Fin"], dayfirst=True, errors="coerce")

inicio = df["Inicio"].min()
fin = df["Fin"].max()
anio_encuesta = df["Inicio"].dt.year.mode()[0]
fechas_unicas = df["Inicio"].dt.date.nunique()

# Calcular NPS global
nps_col = "Recomiendas la Universidad de Lima"
df_nps = df[[nps_col, "Carrera", "Ciclo", "Facultad"]].dropna()
promotores_total = int(df_nps[df_nps[nps_col] >= 9].shape[0])
pasivos_total = int(df_nps[(df_nps[nps_col] >= 7) & (df_nps[nps_col] <= 8)].shape[0])
detractores_total = int(df_nps[df_nps[nps_col] <= 6].shape[0])
nps_score = calc_nps(promotores_total, pasivos_total, detractores_total)

# Calcular CSAT global
csat_col = "La Universidad de Lima"
serie_csat = df[csat_col].dropna()
csat_t3b = int((serie_csat.isin(["Totalmente satisfecho", "Muy satisfecho", "Satisfecho"])).sum())
csat_total = int(serie_csat.isin(respuestas_texto[:5]).sum())  # Solo respuestas válidas
csat_score = calc_csat(csat_t3b, csat_total)

resumen = {
    "encuestas": int(len(df)),
    "carreras": int(df["Carrera"].nunique()),
    "facultades": int(df["Facultad"].nunique()),
    "fecha_inicio": inicio.strftime("%Y-%m-%d"),
    "fecha_fin": fin.strftime("%Y-%m-%d"),
    "dias": int((fin - inicio).days + 1),
    "dias_recoleccion": fechas_unicas,
    "año": int(anio_encuesta),
    # Métricas pre-calculadas
    "nps": {
        "score": nps_score,
        "promotores": promotores_total,
        "pasivos": pasivos_total,
        "detractores": detractores_total,
        "total": promotores_total + pasivos_total + detractores_total
    },
    "csat": {
        "score": csat_score,
        "t3b": csat_t3b,
        "total": csat_total
    }
}

with open(f"{OUT}resumen.json", "w", encoding="utf-8") as f:
    json.dump(resumen, f, ensure_ascii=False, indent=2)

# =========================================================
# 2. NPS (global, carrera, ciclo, ciclo_carrera) - con scores
# =========================================================
nps_total = {
    "Promotores": promotores_total,
    "Pasivos": pasivos_total,
    "Detractores": detractores_total,
    "score": nps_score
}

with open(f"{OUT}nps.json", "w", encoding="utf-8") as f:
    json.dump(nps_total, f, ensure_ascii=False, indent=2)

# NPS por carrera (con score pre-calculado)
nps_carrera = []
for carrera, sub in df_nps.groupby("Carrera"):
    p = int((sub[nps_col] >= 9).sum())
    pa = int(((sub[nps_col] >= 7) & (sub[nps_col] <= 8)).sum())
    d = int((sub[nps_col] <= 6).sum())
    nps_carrera.append({
        "carrera": carrera,
        "Promotores": p,
        "Pasivos": pa,
        "Detractores": d,
        "score": calc_nps(p, pa, d)
    })

with open(f"{OUT}nps_carrera.json", "w", encoding="utf-8") as f:
    json.dump(nps_carrera, f, ensure_ascii=False, indent=2)

# NPS por ciclo (con score pre-calculado)
nps_ciclo = []
for ciclo, sub in df_nps.groupby("Ciclo"):
    p = int((sub[nps_col] >= 9).sum())
    pa = int(((sub[nps_col] >= 7) & (sub[nps_col] <= 8)).sum())
    d = int((sub[nps_col] <= 6).sum())
    nps_ciclo.append({
        "ciclo": ciclo,
        "Promotores": p,
        "Pasivos": pa,
        "Detractores": d,
        "score": calc_nps(p, pa, d)
    })

with open(f"{OUT}nps_ciclo.json", "w", encoding="utf-8") as f:
    json.dump(nps_ciclo, f, ensure_ascii=False, indent=2)

# NPS por ciclo + carrera + facultad (con score pre-calculado)
nps_ciclo_carrera = []
for (fac, car, cic), sub in df_nps.groupby(["Facultad", "Carrera", "Ciclo"]):
    p = int((sub[nps_col] >= 9).sum())
    pa = int(((sub[nps_col] >= 7) & (sub[nps_col] <= 8)).sum())
    d = int((sub[nps_col] <= 6).sum())
    nps_ciclo_carrera.append({
        "facultad": fac,
        "carrera": car,
        "ciclo": cic,
        "Promotores": p,
        "Pasivos": pa,
        "Detractores": d,
        "score": calc_nps(p, pa, d)
    })

with open(f"{OUT}nps_ciclo_carrera.json", "w", encoding="utf-8") as f:
    json.dump(nps_ciclo_carrera, f, ensure_ascii=False, indent=2)

# =========================================================
# 3. CSAT (global, carrera, ciclo, ciclo_carrera) - con scores
# =========================================================
csat_conteos = {r: int((serie_csat == r).sum()) for r in respuestas_texto}
csat_conteos["score"] = csat_score

with open(f"{OUT}csat.json", "w", encoding="utf-8") as f:
    json.dump(csat_conteos, f, ensure_ascii=False, indent=2)

# CSAT por carrera (con score pre-calculado)
csat_carrera = []
for (car, fac), sub in df.groupby(["Carrera", "Facultad"]):
    serie = sub[csat_col].dropna()
    row = {"carrera": car, "facultad": fac}
    for r in respuestas_texto:
        row[r] = int((serie == r).sum())
    t3b = row["Totalmente satisfecho"] + row["Muy satisfecho"] + row["Satisfecho"]
    total = t3b + row["Insatisfecho"] + row["Totalmente insatisfecho"]
    row["score"] = calc_csat(t3b, total)
    csat_carrera.append(row)

with open(f"{OUT}csat_carrera.json", "w", encoding="utf-8") as f:
    json.dump(csat_carrera, f, ensure_ascii=False, indent=2)

# CSAT por ciclo (con score pre-calculado)
csat_ciclo = []
for cic, sub in df.groupby("Ciclo"):
    serie = sub[csat_col].dropna()
    row = {"ciclo": cic}
    for r in respuestas_texto:
        row[r] = int((serie == r).sum())
    t3b = row["Totalmente satisfecho"] + row["Muy satisfecho"] + row["Satisfecho"]
    total = t3b + row["Insatisfecho"] + row["Totalmente insatisfecho"]
    row["score"] = calc_csat(t3b, total)
    csat_ciclo.append(row)

with open(f"{OUT}csat_ciclo.json", "w", encoding="utf-8") as f:
    json.dump(csat_ciclo, f, ensure_ascii=False, indent=2)

# CSAT por ciclo + carrera + facultad (con score pre-calculado)
csat_ciclo_carrera = []
for (fac, car, cic), sub in df.groupby(["Facultad", "Carrera", "Ciclo"]):
    serie = sub[csat_col].dropna()
    row = {"facultad": fac, "carrera": car, "ciclo": cic}
    for r in respuestas_texto:
        row[r] = int((serie == r).sum())
    t3b = row["Totalmente satisfecho"] + row["Muy satisfecho"] + row["Satisfecho"]
    total = t3b + row["Insatisfecho"] + row["Totalmente insatisfecho"]
    row["score"] = calc_csat(t3b, total)
    csat_ciclo_carrera.append(row)

with open(f"{OUT}csat_ciclo_carrera.json", "w", encoding="utf-8") as f:
    json.dump(csat_ciclo_carrera, f, ensure_ascii=False, indent=2)

# =========================================================
# 4. dimensiones.json (con T3B pre-calculado)
# =========================================================
rows = []
for (fac, car, cic), sub in df.groupby(["Facultad", "Carrera", "Ciclo"]):
    for dim, cat in categoria_dim.items():
        if dim not in sub.columns:
            continue
        serie = sub[dim].dropna()
        conteos = {r: int((serie == r).sum()) for r in respuestas_texto}
        t3b = conteos["Totalmente satisfecho"] + conteos["Muy satisfecho"] + conteos["Satisfecho"]
        b2b = conteos["Insatisfecho"] + conteos["Totalmente insatisfecho"]
        total = t3b + b2b
        
        rows.append({
            "facultad": fac,
            "carrera": car,
            "ciclo": cic,
            "categoria": cat,
            "dimension": dim,
            "t3b": t3b,
            "b2b": b2b,
            "total": total,
            "t3b_pct": calc_csat(t3b, total),
            "no_utilizo": conteos["No utilizo"],
            "no_conozco": conteos["No conozco"],
            **conteos
        })

with open(f"{OUT}dimensiones.json", "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=2)

# =========================================================
# 5. evolucion_temporal.json
# =========================================================
df["fecha"] = pd.to_datetime(df["Inicio"], dayfirst=True, errors="coerce").dt.date
serie = df.groupby("fecha").size().reset_index(name="respuestas")
evol = [
    {"fecha": str(r.fecha), "respuestas": int(r.respuestas)}
    for r in serie.itertuples()
]

with open(f"{OUT}evolucion_temporal.json", "w", encoding="utf-8") as f:
    json.dump(evol, f, ensure_ascii=False, indent=2)

# =========================================================
# 6. ids.json (simplificado - solo conteos)
# =========================================================
ids_conteo = []
for (fac, car, cic), sub in df.groupby(["Facultad", "Carrera", "Ciclo"]):
    ids_conteo.append({
        "facultad": fac,
        "carrera": car,
        "ciclo": cic,
        "count": int(len(sub))
    })

with open(f"{OUT}ids.json", "w", encoding="utf-8") as f:
    json.dump(ids_conteo, f, ensure_ascii=False, indent=2)

# =========================================================
# 7. NUEVO: dashboard_data.json (datos consolidados)
# =========================================================
# Pre-calcular hallazgos clave
etapa_map = {
    1: 'Inicial', 2: 'Inicial',
    3: 'Intermedio', 4: 'Intermedio', 5: 'Intermedio', 6: 'Intermedio',
    7: 'Avanzado', 8: 'Avanzado', 9: 'Avanzado', 10: 'Avanzado', 11: 'Avanzado', 12: 'Avanzado'
}

etapas = {}
for item in nps_ciclo:
    ciclo_num = int(''.join(filter(str.isdigit, item["ciclo"])) or 0)
    etapa = etapa_map.get(ciclo_num, 'Otro')
    if etapa not in etapas:
        etapas[etapa] = {"p": 0, "pa": 0, "d": 0}
    etapas[etapa]["p"] += item["Promotores"]
    etapas[etapa]["pa"] += item["Pasivos"]
    etapas[etapa]["d"] += item["Detractores"]

nps_etapas = {}
for etapa, vals in etapas.items():
    nps_etapas[etapa] = calc_nps(vals["p"], vals["pa"], vals["d"])

# Top dimensiones
dim_agg = {}
for r in rows:
    if r["dimension"] not in dim_agg:
        dim_agg[r["dimension"]] = {"t3b": 0, "total": 0}
    dim_agg[r["dimension"]]["t3b"] += r["t3b"]
    dim_agg[r["dimension"]]["total"] += r["total"]

top_dims = sorted(
    [{"name": k, "score": calc_csat(v["t3b"], v["total"])} 
     for k, v in dim_agg.items()],
    key=lambda x: x["score"],
    reverse=True
)[:2]

# Top facultades
fac_agg = {}
for item in csat_carrera:
    fac = item["facultad"]
    if fac not in fac_agg:
        fac_agg[fac] = {"t3b": 0, "total": 0}
    t3b = item["Totalmente satisfecho"] + item["Muy satisfecho"] + item["Satisfecho"]
    total = t3b + item["Insatisfecho"] + item["Totalmente insatisfecho"]
    fac_agg[fac]["t3b"] += t3b
    fac_agg[fac]["total"] += total

top_facs = sorted(
    [{"name": k, "score": calc_csat(v["t3b"], v["total"])} 
     for k, v in fac_agg.items()],
    key=lambda x: x["score"],
    reverse=True
)[:2]

# Conteos especiales
dashboard_data = {
    "resumen": resumen,
    "hallazgos": {
        "csat_pct": int(csat_score),
        "nps_score": int(nps_score),
        "nps_tipo": "Excelente" if nps_score >= 60 else "Bueno" if nps_score >= 30 else "Regular" if nps_score >= 0 else "Pésimo",
        "nps_etapas": nps_etapas,
        "tendencia": "disminuye" if nps_etapas.get("Inicial", 0) > nps_etapas.get("Avanzado", 0) else "aumenta" if nps_etapas.get("Inicial", 0) < nps_etapas.get("Avanzado", 0) else "se mantiene",
        "delta": abs(int(nps_etapas.get("Inicial", 0) - nps_etapas.get("Avanzado", 0))),
        "top_dimensiones": top_dims,
        "top_facultades": top_facs,
        "ciclos_12_count": ciclos_12_count,
        "derecho_count": derecho_count
    },
    "nps": nps_total,
    "csat": csat_conteos,
    "evolucion": evol
}

with open(f"{OUT}dashboard_data.json", "w", encoding="utf-8") as f:
    json.dump(dashboard_data, f, ensure_ascii=False, indent=2)

# =========================================================
# 8. NUEVO: filtros.json (listas únicas para filtros)
# =========================================================
filtros = {
    "facultades": sorted(df["Facultad"].dropna().unique().tolist()),
    "carreras": sorted(df["Carrera"].dropna().unique().tolist()),
    "ciclos": sorted(df["Ciclo"].dropna().unique().tolist(), 
                    key=lambda x: int(''.join(filter(str.isdigit, x)) or 0)),
    "facultad_carrera": {
        fac: sorted(df[df["Facultad"] == fac]["Carrera"].unique().tolist())
        for fac in df["Facultad"].dropna().unique()
    }
}

with open(f"{OUT}filtros.json", "w", encoding="utf-8") as f:
    json.dump(filtros, f, ensure_ascii=False, indent=2)

print("✅ Archivos generados correctamente (con pre-cálculos optimizados).")
print(f"   - resumen.json (con NPS/CSAT pre-calculados)")
print(f"   - nps.json, nps_carrera.json, nps_ciclo.json, nps_ciclo_carrera.json")
print(f"   - csat.json, csat_carrera.json, csat_ciclo.json, csat_ciclo_carrera.json")
print(f"   - dimensiones.json (con T3B pre-calculados)")
print(f"   - evolucion_temporal.json")
print(f"   - ids.json (simplificado)")
print(f"   - dashboard_data.json (NUEVO - datos consolidados)")
print(f"   - filtros.json (NUEVO - listas para filtros)")
