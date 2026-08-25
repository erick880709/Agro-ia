"""Analiza los datasets descargados y evalúa su relevancia para agricultura colombiana."""
import pandas as pd

BASE = r"C:\Users\ELITEBOOK\OneDrive\Documentos\Repositorio\Trabajo\Agro-ia\datasets"

# ── Cultivos clave en Colombia (fuente: DANE, UPRA, FAO) ──
CULTIVOS_COLOMBIA = {
    "cafe", "café", "coffee",
    "maiz", "maíz", "corn", "maize",
    "arroz", "rice", "paddy",
    "platano", "plátano", "banana", "banano", "plantain",
    "yuca", "cassava",
    "papa", "potato",
    "frijol", "fríjol", "bean", "beans", "kidneybeans", "mungbean", "blackgram", "lentil", "pigeonpeas", "chickpea",
    "palma", "oil palm",
    "cacao", "cocoa", "cocoa",
    "caña", "sugarcane",
    "aguacate", "avocado",
    "citricos", "cítricos", "naranja", "orange", "limon", "lemon", "mandarina",
    "mango",
    "piña", "pineapple",
    "tomate", "tomato",
    "cebolla", "onion",
    "algodon", "cotton",
    "soya", "soybean",
    "sorgo", "sorghum",
    "trigo", "wheat",
}

# Cargar datasets
df1 = pd.read_csv(f"{BASE}/crop-recommendation/Crop_recommendation.csv")
df2 = pd.read_csv(f"{BASE}/crops-npk/sensor_Crop_Dataset (1).csv")

print("=" * 65)
print("  ANÁLISIS DE RELEVANCIA PARA AGRICULTURA COLOMBIANA")
print("=" * 65)

# ── Dataset 1 ──
print("\n📊 DATASET 1: Crop Recommendation (Kaggle/atharvaingle)")
print(f"   {len(df1):,} registros | {df1['label'].nunique()} cultivos")
crops1 = set(df1['label'].str.lower().str.strip())
match1 = crops1 & CULTIVOS_COLOMBIA
no_match1 = crops1 - CULTIVOS_COLOMBIA
print(f"   Cultivos relevantes para Colombia: {len(match1)}/{len(crops1)}")
print(f"   ✅ Coinciden: {sorted(match1)}")
print(f"   ❌ No coinciden: {sorted(no_match1)}")
print(f"   Rangos climáticos: T={df1['temperature'].min():.0f}-{df1['temperature'].max():.0f}°C, "
      f"Humedad={df1['humidity'].min():.0f}-{df1['humidity'].max():.0f}%, "
      f"Lluvia={df1['rainfall'].min():.0f}-{df1['rainfall'].max():.0f}mm")
print(f"   ⚠️  Origen: India. Clima monzónico ≠ clima tropical andino colombiano.")

# ── Dataset 2 ──
print(f"\n📊 DATASET 2: Crops NPK (Kaggle/javakhan)")
print(f"   {len(df2):,} registros | {df2['Crop'].nunique()} cultivos")
crops2 = set(df2['Crop'].str.lower().str.strip())
match2 = crops2 & CULTIVOS_COLOMBIA
no_match2 = crops2 - CULTIVOS_COLOMBIA
print(f"   Cultivos relevantes para Colombia: {len(match2)}/{len(crops2)}")
print(f"   ✅ Coinciden: {sorted(match2)}")
print(f"   ❌ No coinciden: {sorted(no_match2)}")
print(f"   Tipos de suelo: {sorted(df2['Soil_Type'].dropna().unique())}")
print(f"   Rangos: T={df2['Temperature'].min():.0f}-{df2['Temperature'].max():.0f}°C, "
      f"pH={df2['pH_Value'].min():.1f}-{df2['pH_Value'].max():.1f}")
print(f"   ⚠️  Mismo origen: India. Sin datos del trópico andino.")

# ── Comparación con necesidades del proyecto ──
print("\n" + "=" * 65)
print("  BRECHAS vs REQUERIMIENTOS DE AgroIA")
print("=" * 65)

print("""
❌ BRECHA 1 — Café (cultivo principal del piloto Quindío):
   Ninguno de los dos datasets incluye café. El piloto valida con
   café en el Eje Cafetero. Sin datos de café, estos datasets NO
   sirven para el Modelo 1 (clasificación UPRA) ni para calibrar
   el sistema experto de Cenicafé.

❌ BRECHA 2 — Clima y geografía:
   Ambos datasets son de India (clima monzónico, llanuras).
   Colombia tiene clima tropical andino con pisos térmicos
   (0-5,000 msnm). Las relaciones suelo-clima-cultivo son
   fundamentalmente distintas. Un modelo entrenado con datos
   indios hará predicciones ERRÓNEAS en el Quindío.

❌ BRECHA 3 — Variables de suelo:
   Solo incluyen N-P-K + pH + humedad + temperatura + lluvia.
   Faltan las 14+ variables que AgroIA necesita medir:
   Ca, Mg, S, Fe, Mn, Zn, Cu, B, MO, CIC, textura, CE.
   El motor de recomendaciones requiere 18 variables.

❌ BRECHA 4 — Clasificación UPRA:
   AgroIA usa el estándar colombiano UPRA (Alta/Media/Baja/No apta).
   Estos datasets usan clasificación arbitraria sin respaldo
   institucional colombiano.

⚠️  UTILIDAD REAL (limitada):
   - Sirven como baseline metodológico para PROBAR que el pipeline
     de ML funciona (train/test split, validación cruzada, métricas).
   - NO deben usarse para generar recomendaciones a agricultores.
   - El documento RFP ya advierte: "Nunca usar estos datasets como
     única fuente de verdad para recomendaciones que se muestren
     al agricultor."
""")

# ── Recomendación ──
print("=" * 65)
print("  RECOMENDACIÓN")
print("=" * 65)
print("""
✅ CONSERVAR los datasets para:
   1. Pruebas unitarias del pipeline de ML (sintaxis, shapes, métricas)
   2. Validación de que el código de entrenamiento/inferencia funciona
   3. Demo técnica (no funcional) del flujo ML

⚠️  NO USAR para:
   1. Entrenar modelos que generen recomendaciones reales
   2. Calibrar umbrales agronómicos
   3. Validar precisión del sistema experto

🎯 PRÓXIMOS PASOS para datos colombianos reales:
   1. AGROSAVIA — Descargar dataset de análisis de suelos (datos.gov.co)
      → ÚNICO dataset público colombiano con variables reales de suelo
   2. IDEAM — Construir conector SODA API para estaciones del Quindío
   3. Cenicafé — Gestionar acceso a biblioteca técnica para umbrales café
   4. Piloto Quindío — Datos de sensores IoT propios (fuente definitiva)
   5. UPRA — Descargar zonificaciones de café como ground truth
""")

# ── Estadísticas finales ──
total_crops = crops1 | crops2
relevantes = total_crops & CULTIVOS_COLOMBIA
print(f"\n📊 Resumen: {len(relevantes)}/{len(total_crops)} cultivos tienen "
      f"alguna relevancia para Colombia ({len(relevantes)/len(total_crops)*100:.0f}%)")
print(f"   Café (cultivo principal del piloto): {'✅' if 'coffee' in total_crops or 'cafe' in total_crops else '❌ AUSENTE'}")
