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
# 2. nps_base.json
# =========================================================
nps_col = "Recomiendas la Universidad de Lima"

def build_nps(group_col, label):
    salida = []
    for val, sub in df.groupby(group_col):
        serie = sub[nps_col].dropna()
        conteos = {str(i): int((serie == i).sum()) for i in range(11)}

        salida.append({
            "nivel": label,
            "valor": val,
            **conteos
        })
    return salida

nps_rows = []
nps_rows += build_nps("Carrera", "carrera")
nps_rows += build_nps("Ciclo", "ciclo")

with open(f"{OUT}nps_base.json", "w", encoding="utf-8") as f:
    json.dump(nps_rows, f, ensure_ascii=False, indent=2)

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

print("Archivos generados correctamente (solo conteos enteros).")
