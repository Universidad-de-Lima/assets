import pandas as pd
import json

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
    # Académico
    "Perfil del egreso de la carrera": "Académico",
    "Calidad de la enseñanza en la carrera": "Académico",
    "Plan curricular y perfil de egreso": "Académico",
    "Cursos del programa y contenidos": "Académico",
    "Evaluación del aprendizaje": "Académico",
    "Intercambio estudiantil": "Académico",

    # Administrativo y Bienestar
    "Servicio médico y su infraestructura": "Administrativo y Bienestar",
    "Material bibliográfico en la biblioteca": "Administrativo y Bienestar",
    "Talleres de actividades artísticas y culturales": "Administrativo y Bienestar",
    "Atención del personal administrativo": "Administrativo y Bienestar",
    "Actividades deportivas": "Administrativo y Bienestar",
    "Información sobre tu récord académico": "Administrativo y Bienestar",
    "Servicio de atención psicopedagógica": "Administrativo y Bienestar",
    "Ayuda financiera": "Administrativo y Bienestar",

    # Infraestructura
    "Condiciones ambientales en laboratorios": "Infraestructura",
    "Equipamiento tecnológico en laboratorios": "Infraestructura",
    "Aulas de clase": "Infraestructura",
    "Ambientes y aulas para estudio": "Infraestructura",

    # Tecnología
    "Aula virtual": "Tecnología",
    "Software especializado empleado en la carrera": "Tecnología",
    "Soporte técnico del sistema informático": "Tecnología",
    "Portal web de la Universidad": "Tecnología",
    "Conexión WiFi en el campus": "Tecnología",
}

# =========================================================
# 1. dimensiones.json (base real para filtros)
# =========================================================
rows = []

for (fac, car, cic), sub in df.groupby(["Facultad", "Carrera", "Ciclo"]):
    for dim, cat in categoria_dim.items():
        if dim not in sub.columns:
            continue

        serie = sub[dim].dropna()
        conteos = {r: int((serie == r).sum()) for r in respuestas_texto}

        rows.append({
            "facultad": fac,
            "carrera": car,
            "ciclo": cic,
            "categoria": cat,
            "dimension": dim,
            **conteos
        })

with open(f"{OUT}dimensiones.json", "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=2)

# =========================================================
# 2. NPS (global, carrera, ciclo)
# =========================================================
nps_col = "Recomiendas la Universidad de Lima"

df_nps = df[[nps_col, "Carrera", "Ciclo"]].dropna()

# --------
# NPS TOTAL
# --------
promotores = int(df_nps[df_nps[nps_col] >= 9].shape[0])
pasivos = int(df_nps[(df_nps[nps_col] >= 7) & (df_nps[nps_col] <= 8)].shape[0])
detractores = int(df_nps[df_nps[nps_col] <= 6].shape[0])

nps_total = {
    "Promotores": promotores,
    "Pasivos": pasivos,
    "Detractores": detractores
}

with open(f"{OUT}nps.json", "w", encoding="utf-8") as f:
    json.dump(nps_total, f, ensure_ascii=False, indent=2)

# ----------------
# NPS POR CARRERA
# ----------------
nps_carrera = []

for carrera, sub in df_nps.groupby("Carrera"):
    nps_carrera.append({
        "carrera": carrera,
        "Promotores": int((sub[nps_col] >= 9).sum()),
        "Pasivos": int(((sub[nps_col] >= 7) & (sub[nps_col] <= 8)).sum()),
        "Detractores": int((sub[nps_col] <= 6).sum())
    })

with open(f"{OUT}nps_carrera.json", "w", encoding="utf-8") as f:
    json.dump(nps_carrera, f, ensure_ascii=False, indent=2)

# --------------
# NPS POR CICLO
# --------------
nps_ciclo = []

for ciclo, sub in df_nps.groupby("Ciclo"):
    nps_ciclo.append({
        "ciclo": ciclo,
        "Promotores": int((sub[nps_col] >= 9).sum()),
        "Pasivos": int(((sub[nps_col] >= 7) & (sub[nps_col] <= 8)).sum()),
        "Detractores": int((sub[nps_col] <= 6).sum())
    })

with open(f"{OUT}nps_ciclo.json", "w", encoding="utf-8") as f:
    json.dump(nps_ciclo, f, ensure_ascii=False, indent=2)

# --------------------------
# NPS POR CICLO + CARRERA + FACULTAD
# --------------------------
df_nps_full = df[[nps_col, "Carrera", "Ciclo", "Facultad"]].dropna()
nps_ciclo_carrera = []

for (fac, car, cic), sub in df_nps_full.groupby(["Facultad", "Carrera", "Ciclo"]):
    nps_ciclo_carrera.append({
        "facultad": fac,
        "carrera": car,
        "ciclo": cic,
        "Promotores": int((sub[nps_col] >= 9).sum()),
        "Pasivos": int(((sub[nps_col] >= 7) & (sub[nps_col] <= 8)).sum()),
        "Detractores": int((sub[nps_col] <= 6).sum())
    })

with open(f"{OUT}nps_ciclo_carrera.json", "w", encoding="utf-8") as f:
    json.dump(nps_ciclo_carrera, f, ensure_ascii=False, indent=2)

# =========================================================
# 3. resumen.json
# =========================================================
df["Inicio"] = pd.to_datetime(df["Inicio"], dayfirst=True, errors="coerce")
df["Fin"] = pd.to_datetime(df["Fin"], dayfirst=True, errors="coerce")

inicio = df["Inicio"].min()
fin = df["Fin"].max()
anio_encuesta = df["Inicio"].dt.year.mode()[0]
fechas_unicas = df["Inicio"].dt.date.nunique()

resumen = {
    "encuestas": int(len(df)),
    "carreras": int(df["Carrera"].nunique()),
    "facultades": int(df["Facultad"].nunique()),
    "fecha_inicio": inicio.strftime("%Y-%m-%d"),
    "fecha_fin": fin.strftime("%Y-%m-%d"),
    "dias": int((fin - inicio).days + 1),
    "dias_recoleccion": fechas_unicas,
    "año": int(anio_encuesta)
}

with open(f"{OUT}resumen.json", "w", encoding="utf-8") as f:
    json.dump(resumen, f, ensure_ascii=False, indent=2)

# =========================================================
# 4. csat.json
# =========================================================
csat_col = "La Universidad de Lima"
serie = df[csat_col].dropna()
csat_conteos = {r: int((serie == r).sum()) for r in respuestas_texto}

with open(f"{OUT}csat.json", "w", encoding="utf-8") as f:
    json.dump(csat_conteos, f, ensure_ascii=False, indent=2)

# =========================================================
# 4.1 csat_carrera.json (solo conteos)
# =========================================================
csat_carrera = []

for (car, fac), sub in df.groupby(["Carrera", "Facultad"]):
    serie = sub[csat_col].dropna()

    row = {
        "carrera": car,
        "facultad": fac
    }

    for r in respuestas_texto:
        row[r] = int((serie == r).sum())

    csat_carrera.append(row)

with open(f"{OUT}csat_carrera.json", "w", encoding="utf-8") as f:
    json.dump(csat_carrera, f, ensure_ascii=False, indent=2)

# =========================================================
# 4.2 csat_ciclo.json (solo conteos)
# =========================================================
csat_ciclo = []

for cic, sub in df.groupby("Ciclo"):
    serie = sub[csat_col].dropna()

    row = {
        "ciclo": cic
    }

    for r in respuestas_texto:
        row[r] = int((serie == r).sum())

    csat_ciclo.append(row)

with open(f"{OUT}csat_ciclo.json", "w", encoding="utf-8") as f:
    json.dump(csat_ciclo, f, ensure_ascii=False, indent=2)

# =========================================================
# 4.3 csat_ciclo_carrera.json (con facultad, carrera, ciclo)
# =========================================================
csat_ciclo_carrera = []

for (fac, car, cic), sub in df.groupby(["Facultad", "Carrera", "Ciclo"]):
    serie = sub[csat_col].dropna()

    row = {
        "facultad": fac,
        "carrera": car,
        "ciclo": cic
    }

    for r in respuestas_texto:
        row[r] = int((serie == r).sum())

    csat_ciclo_carrera.append(row)

with open(f"{OUT}csat_ciclo_carrera.json", "w", encoding="utf-8") as f:
    json.dump(csat_ciclo_carrera, f, ensure_ascii=False, indent=2)

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
# 6. ids.json (IDs únicos por Facultad / Carrera / Ciclo)
# =========================================================
ids = []

for (fac, car, cic), sub in df.groupby(["Facultad", "Carrera", "Ciclo"]):
    for _id in sub.index:
        ids.append({
            "id": str(_id),
            "facultad": fac,
            "carrera": car,
            "ciclo": cic
        })

with open(f"{OUT}ids.json", "w", encoding="utf-8") as f:
    json.dump(ids, f, ensure_ascii=False, indent=2)

print("Archivos generados correctamente (solo conteos enteros).")
