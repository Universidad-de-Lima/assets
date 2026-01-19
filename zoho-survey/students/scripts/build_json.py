import pandas as pd
import json

INPUT = "data/_Encuesta_estudiantil_2025.txt"
OUT = "output/"

top3 = ["Totalmente satisfecho", "Muy satisfecho", "Satisfecho"]
exclude = ["No conozco", "No utilizo"]

# -----------------------
# Leer data
# -----------------------
df = pd.read_csv(INPUT, sep=None, engine="python")

# -----------------------
# Utilidades
# -----------------------
def t3b_from_counts(series):
    s = series.dropna()
    s = s[~s.isin(exclude)]
    total = len(s)
    ok = s.isin(top3).sum()
    return round(ok / total * 100, 2), ok, total

# -----------------------
# RESUMEN
# -----------------------
inicio = pd.to_datetime(df["Inicio"], dayfirst=True, errors="coerce").min()
fin = pd.to_datetime(df["Fin"], dayfirst=True, errors="coerce").max()

resumen = {
    "anio": inicio.year,
    "encuestas": int(len(df)),
    "periodo": {
        "inicio": inicio.strftime("%Y-%m-%d"),
        "fin": fin.strftime("%Y-%m-%d"),
        "dias": int((fin - inicio).days + 1)
    },
    "conteos": {
        "carreras": int(df["Carrera"].nunique()),
        "facultades": int(df["Carrera"].map({
            "Arquitectura":"Arquitectura",
            "Derecho":"Derecho",
            "Economía":"Economía",
            "Comunicación":"Comunicación",
            "Psicología":"Psicología",
            "Administración":"Ciencias Empresariales",
            "Marketing":"Ciencias Empresariales",
            "Negocios Internacionales":"Ciencias Empresariales",
            "Contabilidad y Finanzas":"Ciencias Empresariales",
            "Ingeniería Civil":"Ingeniería",
            "Ingeniería Industrial":"Ingeniería",
            "Ingeniería de Sistemas":"Ingeniería",
            "Ingeniería Ambiental":"Ingeniería",
            "Ingeniería Mecatrónica":"Ingeniería"
        }).nunique())
    }
}

with open(f"{OUT}resumen.json", "w", encoding="utf-8") as f:
    json.dump(resumen, f, ensure_ascii=False, indent=2)

# -----------------------
# BLOQUES DE DIMENSIONES
# -----------------------
bloques = {
    "academico.json": [
        "Perfil del egreso de la carrera",
        "Calidad de la enseñanza en la carrera",
        "Plan curricular y perfil de egreso",
        "Cursos del programa y contenidos",
        "Evaluación del aprendizaje",
        "Intercambio estudiantil"
    ],
    "infraestructura.json": [
        "Condiciones ambientales en laboratorios",
        "Equipamiento tecnológico en laboratorios",
        "Aulas de clase",
        "Ambientes y aulas para estudio"
    ],
    "tecnologia.json": [
        "Aula virtual",
        "Software especializado empleado en la carrera",
        "Portal web de la Universidad",
        "Conexión WiFi en el campus",
        "Soporte técnico del sistema informático"
    ],
    "administrativo_bienestar.json": [
        "Talleres de actividades artísticas y culturales",
        "Actividades deportivas",
        "Información sobre tu récord académico",
        "Servicio de atención psicopedagógica",
        "Atención del personal administrativo",
        "Material bibliográfico en la biblioteca",
        "Ayuda financiera",
        "Servicio médico y su infraestructura"
    ]
}

for filename, dims in bloques.items():
    salida = []
    for dim in dims:
        pct, ok, total = t3b_from_counts(df[dim])
        salida.append({
            "dimension": dim,
            "t3b": pct,
            "conteo_top3": int(ok),
            "total_validas": int(total)
        })
    with open(f"{OUT}{filename}", "w", encoding="utf-8") as f:
        json.dump({"dimensiones": salida}, f, ensure_ascii=False, indent=2)

# -----------------------
# NPS
# -----------------------
def calc_nps(series):
    s = series.dropna()
    total = len(s)
    prom = (s >= 9).sum()
    detr = (s <= 6).sum()
    return round(((prom - detr) / total) * 100, 2), prom, detr, total

nps, prom, detr, total = calc_nps(df["Recomiendas la Universidad de Lima"])
pasivos = total - prom - detr

nps_json = {
    "score": nps,
    "meta": 50,
    "diferencia": round(nps - 50, 2),
    "composicion": {
        "promotores": {"conteo": int(prom), "porcentaje": round(prom/total*100,2)},
        "pasivos": {"conteo": int(pasivos), "porcentaje": round(pasivos/total*100,2)},
        "detractores": {"conteo": int(detr), "porcentaje": round(detr/total*100,2)}
    }
}

with open(f"{OUT}nps.json", "w", encoding="utf-8") as f:
    json.dump(nps_json, f, ensure_ascii=False, indent=2)

# -----------------------
# CSAT
# -----------------------
csat_pct, csat_ok, csat_total = t3b_from_counts(df["La Universidad de Lima"])
dist = df["La Universidad de Lima"].value_counts()

csat_json = {
    "score": csat_pct,
    "meta": 90,
    "diferencia": round(csat_pct - 90, 2),
    "distribucion": [
        {
            "categoria": k,
            "conteo": int(v),
            "porcentaje": round(v / csat_total * 100, 2)
        }
        for k, v in d
