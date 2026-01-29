"""
build_json_optimized.py
-----------------------
Genera un único JSON consolidado con todos los datos precalculados
para eliminar cálculos en el cliente y reducir fetches múltiples.

Salida: output/data.json (único archivo)
"""

import pandas as pd
import json
import os
from collections import defaultdict

INPUT = "data/_Encuesta_estudiantil_2025.txt"
OUT = "output/"

# Crear directorio de salida si no existe
os.makedirs(OUT, exist_ok=True)

respuestas_texto = [
    "Totalmente satisfecho",
    "Muy satisfecho",
    "Satisfecho",
    "Insatisfecho",
    "Totalmente insatisfecho",
    "No utilizo",
    "No conozco"
]

# Respuestas para T3B (Top 3 Box)
T3B_KEYS = ["Totalmente satisfecho", "Muy satisfecho", "Satisfecho"]
B2B_KEYS = ["Insatisfecho", "Totalmente insatisfecho"]

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
    "Portal web de la Universidad": "Tecnología",
    "Conexión WiFi en el campus": "Tecnología",
}

# -----------------------
# HELPER FUNCTIONS
# -----------------------
def calc_t3b(row):
    """Calcula T3B de un diccionario con conteos"""
    return sum(row.get(k, 0) for k in T3B_KEYS)

def calc_total_valid(row):
    """Calcula total de respuestas válidas (excluyendo No utilizo/No conozco)"""
    return calc_t3b(row) + sum(row.get(k, 0) for k in B2B_KEYS)

def calc_nps(promotores, pasivos, detractores):
    """Calcula NPS score"""
    total = promotores + pasivos + detractores
    if total == 0:
        return 0
    return round(((promotores - detractores) / total) * 100)

def calc_csat_pct(t3b, total):
    """Calcula CSAT porcentaje"""
    if total == 0:
        return 0
    return round((t3b / total) * 100, 2)

# -----------------------
# COLUMNAS NPS Y CSAT
# -----------------------
nps_col = "Recomiendas la Universidad de Lima"
csat_col = "La Universidad de Lima"

# =========================================================
# 1. RESUMEN GENERAL
# =========================================================
df["Inicio"] = pd.to_datetime(df["Inicio"], dayfirst=True, errors="coerce")
df["Fin"] = pd.to_datetime(df["Fin"], dayfirst=True, errors="coerce")

inicio = df["Inicio"].min()
fin = df["Fin"].max()
anio_encuesta = int(df["Inicio"].dt.year.mode()[0])
fechas_unicas = df["Inicio"].dt.date.nunique()

resumen = {
    "encuestas": int(len(df)),
    "carreras": int(df["Carrera"].nunique()),
    "facultades": int(df["Facultad"].nunique()),
    "fecha_inicio": inicio.strftime("%Y-%m-%d"),
    "fecha_fin": fin.strftime("%Y-%m-%d"),
    "dias": int((fin - inicio).days + 1),
    "dias_recoleccion": int(fechas_unicas),
    "anio": anio_encuesta
}

# =========================================================
# 2. NPS GLOBAL Y PRECALCULADO
# =========================================================
df_nps = df[[nps_col, "Carrera", "Ciclo", "Facultad"]].dropna(subset=[nps_col])

promotores_total = int((df_nps[nps_col] >= 9).sum())
pasivos_total = int(((df_nps[nps_col] >= 7) & (df_nps[nps_col] <= 8)).sum())
detractores_total = int((df_nps[nps_col] <= 6).sum())
nps_score = calc_nps(promotores_total, pasivos_total, detractores_total)

nps_global = {
    "Promotores": promotores_total,
    "Pasivos": int(pasivos_total),
    "Detractores": detractores_total,
    "score": nps_score,
    "total": promotores_total + int(pasivos_total) + detractores_total
}

# =========================================================
# 3. CSAT GLOBAL Y PRECALCULADO
# =========================================================
serie_csat = df[csat_col].dropna()
csat_conteos = {r: int((serie_csat == r).sum()) for r in respuestas_texto}
csat_t3b = calc_t3b(csat_conteos)
csat_total = calc_total_valid(csat_conteos)
csat_pct = calc_csat_pct(csat_t3b, csat_total)

csat_global = {
    **csat_conteos,
    "t3b": csat_t3b,
    "total": csat_total,
    "pct": csat_pct
}

# =========================================================
# 4. EVOLUCIÓN TEMPORAL
# =========================================================
df["fecha"] = df["Inicio"].dt.date
serie_temporal = df.groupby("fecha").size().reset_index(name="respuestas")

evolucion = [
    {"fecha": str(r.fecha), "respuestas": int(r.respuestas)}
    for r in serie_temporal.itertuples()
]

# Pico
pico = max(evolucion, key=lambda x: x["respuestas"])

# =========================================================
# 5. NPS POR CICLO (con etapas precalculadas)
# =========================================================
etapa_map = {
    1: 'Inicial', 2: 'Inicial',
    3: 'Intermedio', 4: 'Intermedio', 5: 'Intermedio',
    6: 'Avanzado', 7: 'Avanzado', 8: 'Avanzado',
    9: 'Final', 10: 'Final', 11: 'Final', 12: 'Final'
}

nps_ciclo = []
etapas_agg = defaultdict(lambda: {"p": 0, "pa": 0, "d": 0})

for ciclo, sub in df_nps.groupby("Ciclo"):
    prom = int((sub[nps_col] >= 9).sum())
    pas = int(((sub[nps_col] >= 7) & (sub[nps_col] <= 8)).sum())
    det = int((sub[nps_col] <= 6).sum())
    score = calc_nps(prom, pas, det)
    
    ciclo_num = int(ciclo.split("°")[0]) if "°" in str(ciclo) else 0
    etapa = etapa_map.get(ciclo_num, "Final")
    
    etapas_agg[etapa]["p"] += prom
    etapas_agg[etapa]["pa"] += pas
    etapas_agg[etapa]["d"] += det
    
    nps_ciclo.append({
        "ciclo": ciclo,
        "ciclo_num": ciclo_num,
        "Promotores": prom,
        "Pasivos": pas,
        "Detractores": det,
        "score": score,
        "etapa": etapa
    })

nps_ciclo.sort(key=lambda x: x["ciclo_num"])

# NPS por etapa precalculado
nps_etapas = {}
for etapa, v in etapas_agg.items():
    nps_etapas[etapa] = calc_nps(v["p"], v["pa"], v["d"])

# =========================================================
# 6. NPS POR CARRERA
# =========================================================
nps_carrera = []
for carrera, sub in df_nps.groupby("Carrera"):
    prom = int((sub[nps_col] >= 9).sum())
    pas = int(((sub[nps_col] >= 7) & (sub[nps_col] <= 8)).sum())
    det = int((sub[nps_col] <= 6).sum())
    
    nps_carrera.append({
        "carrera": carrera,
        "facultad": carrera_facultad.get(carrera, ""),
        "Promotores": prom,
        "Pasivos": pas,
        "Detractores": det,
        "score": calc_nps(prom, pas, det),
        "total": prom + pas + det
    })

nps_carrera.sort(key=lambda x: -x["total"])

# =========================================================
# 7. CSAT POR CARRERA (con precálculo)
# =========================================================
csat_carrera = []
fac_agg = defaultdict(lambda: {"t3b": 0, "total": 0})

for (car, fac), sub in df.groupby(["Carrera", "Facultad"]):
    serie = sub[csat_col].dropna()
    row = {r: int((serie == r).sum()) for r in respuestas_texto}
    t3b = calc_t3b(row)
    total = calc_total_valid(row)
    
    fac_agg[fac]["t3b"] += t3b
    fac_agg[fac]["total"] += total
    
    csat_carrera.append({
        "carrera": car,
        "facultad": fac,
        **row,
        "t3b": t3b,
        "total": total,
        "pct": calc_csat_pct(t3b, total)
    })

csat_carrera.sort(key=lambda x: -x["total"])

# Top 2 facultades por CSAT
top_facultades = sorted(
    [{"facultad": k, "pct": calc_csat_pct(v["t3b"], v["total"])} 
     for k, v in fac_agg.items()],
    key=lambda x: -x["pct"]
)[:2]

# =========================================================
# 8. CSAT POR CICLO
# =========================================================
csat_ciclo = []
for cic, sub in df.groupby("Ciclo"):
    serie = sub[csat_col].dropna()
    row = {r: int((serie == r).sum()) for r in respuestas_texto}
    t3b = calc_t3b(row)
    total = calc_total_valid(row)
    ciclo_num = int(cic.split("°")[0]) if "°" in str(cic) else 0
    
    csat_ciclo.append({
        "ciclo": cic,
        "ciclo_num": ciclo_num,
        **row,
        "t3b": t3b,
        "total": total,
        "pct": calc_csat_pct(t3b, total)
    })

csat_ciclo.sort(key=lambda x: x["ciclo_num"])

# =========================================================
# 9. NPS/CSAT POR CICLO-CARRERA (para filtros)
# =========================================================
nps_ciclo_carrera = []
for (fac, car, cic), sub in df_nps.groupby(["Facultad", "Carrera", "Ciclo"]):
    prom = int((sub[nps_col] >= 9).sum())
    pas = int(((sub[nps_col] >= 7) & (sub[nps_col] <= 8)).sum())
    det = int((sub[nps_col] <= 6).sum())
    
    nps_ciclo_carrera.append({
        "facultad": fac,
        "carrera": car,
        "ciclo": cic,
        "Promotores": prom,
        "Pasivos": pas,
        "Detractores": det
    })

csat_ciclo_carrera = []
for (fac, car, cic), sub in df.groupby(["Facultad", "Carrera", "Ciclo"]):
    serie = sub[csat_col].dropna()
    row = {r: int((serie == r).sum()) for r in respuestas_texto}
    
    csat_ciclo_carrera.append({
        "facultad": fac,
        "carrera": car,
        "ciclo": cic,
        **row
    })

# =========================================================
# 10. DIMENSIONES (agregado por categoría para filtros)
# =========================================================
dimensiones = []
dim_agg = defaultdict(lambda: {"t3b": 0, "total": 0})

for (fac, car, cic), sub in df.groupby(["Facultad", "Carrera", "Ciclo"]):
    for dim, cat in categoria_dim.items():
        if dim not in sub.columns:
            continue
        
        serie = sub[dim].dropna()
        conteos = {r: int((serie == r).sum()) for r in respuestas_texto}
        t3b = calc_t3b(conteos)
        total = calc_total_valid(conteos)
        
        dim_agg[dim]["t3b"] += t3b
        dim_agg[dim]["total"] += total
        
        dimensiones.append({
            "facultad": fac,
            "carrera": car,
            "ciclo": cic,
            "categoria": cat,
            "dimension": dim,
            **conteos
        })

# Top 2 dimensiones
top_dimensiones = sorted(
    [{"dimension": k, "pct": calc_csat_pct(v["t3b"], v["total"])} 
     for k, v in dim_agg.items()],
    key=lambda x: -x["pct"]
)[:2]

# =========================================================
# 11. CONTEO POR FILTROS (reemplaza ids.json)
# =========================================================
conteo_filtros = []
for (fac, car, cic), sub in df.groupby(["Facultad", "Carrera", "Ciclo"]):
    conteo_filtros.append({
        "facultad": fac,
        "carrera": car,
        "ciclo": cic,
        "count": len(sub)
    })

# Listas únicas para filtros
filtros = {
    "facultades": sorted(df["Facultad"].dropna().unique().tolist()),
    "carreras": sorted(df["Carrera"].dropna().unique().tolist()),
    "ciclos": sorted(df["Ciclo"].dropna().unique().tolist(), 
                     key=lambda x: int(x.split("°")[0]) if "°" in str(x) else 0)
}

# =========================================================
# 12. INSIGHTS PRECALCULADOS
# =========================================================
insights = {
    "csat_pct": csat_pct,
    "nps_score": nps_score,
    "nps_tipo": "Excelente" if nps_score >= 60 else "Bueno" if nps_score >= 30 else "Regular" if nps_score >= 0 else "Pésimo",
    "nps_etapas": nps_etapas,
    "nps_delta": nps_etapas.get("Inicial", 0) - nps_etapas.get("Final", 0),
    "tendencia": "disminuye" if nps_etapas.get("Inicial", 0) > nps_etapas.get("Final", 0) else "aumenta" if nps_etapas.get("Inicial", 0) < nps_etapas.get("Final", 0) else "se mantiene",
    "top_dimensiones": top_dimensiones,
    "top_facultades": top_facultades
}

# =========================================================
# GENERAR JSON CONSOLIDADO
# =========================================================
data_consolidada = {
    "resumen": resumen,
    "nps": {
        "global": nps_global,
        "carrera": nps_carrera,
        "ciclo": nps_ciclo,
        "ciclo_carrera": nps_ciclo_carrera
    },
    "csat": {
        "global": csat_global,
        "carrera": csat_carrera,
        "ciclo": csat_ciclo,
        "ciclo_carrera": csat_ciclo_carrera
    },
    "evolucion": {
        "datos": evolucion,
        "pico": pico
    },
    "dimensiones": dimensiones,
    "conteo_filtros": conteo_filtros,
    "filtros": filtros,
    "insights": insights
}

# Guardar JSON consolidado
with open(f"{OUT}data.json", "w", encoding="utf-8") as f:
    json.dump(data_consolidada, f, ensure_ascii=False, separators=(',', ':'))

print(f"✓ Generado: {OUT}data.json")
print(f"  - Encuestas: {resumen['encuestas']:,}")
print(f"  - NPS: {nps_score}")
print(f"  - CSAT: {csat_pct}%")
