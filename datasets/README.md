# Datasets para AgroIA

Datasets descargados para el entrenamiento inicial (cold-start) de los modelos de ML de AgroIA.

## 📥 Datasets descargados

| Dataset | Archivo | Registros | Tamaño | Fuente | Uso |
|---------|---------|-----------|--------|--------|-----|
| **Crop Recommendation** | `crop-recommendation/Crop_recommendation.csv` | 2,200 | 147 KB | Kaggle (atharvaingle) | Modelo 2 — Predicción cultivo ideal (baseline) |
| **Crops NPK** | `crops-npk/sensor_Crop_Dataset (1).csv` | 20,000 | 2.9 MB | Kaggle (javakhan) | Modelo 3 — Deficiencias nutricionales (baseline) |

## ⚠️ Datasets NO descargados

Los siguientes requieren acceso interactivo, API keys, o son demasiado grandes para almacenar en git:

| Dataset | Motivo |
|---------|--------|
| **PlantVillage** (50,000+ imágenes) | ~5 GB — descargar bajo demanda para visión artificial (post-MVP) |
| **AGROSAVIA suelos** | Portal datos.gov.co — requiere navegación interactiva / API |
| **IDEAM** | API Socrata SODA — requiere registro y dataset ID específico del Quindío |
| **IGAC shapefiles** | Portal geoportal.igac.gov.co — descarga interactiva por departamento |
| **UPRA zonificaciones** | Portal sipra.upra.gov.co — descarga interactiva |
| **DANE EVA / SIPSA** | APIs web — requieren construcción del conector |
| **SoilGrids (ISRIC)** | API REST — consumo on-demand, no descarga masiva |
| **FAO GAEZ** | Portal web — descarga interactiva |
| **Copernicus/Sentinel-2** | API + Google Earth Engine — imágenes satelitales bajo demanda |
| **Cenicafé** | Portal biblioteca.cenicafe.org — documentos PDF, licencia CC BY-NC-ND |

## 🔄 Estrategia de uso

1. **Datasets Kaggle:** usar SOLO como baseline metodológico. NO mostrar recomendaciones basadas en estos datos a usuarios reales sin calibrar con datos colombianos.
2. **Calibración:** durante el piloto (meses 1-6), reentrenar con datos reales del Quindío (sensores IoT + AGROSAVIA + IDEAM).
3. **Producción:** modelos entrenados exclusivamente con datos colombianos validados.

---

> **Descargado:** 2026-08-04 | **Script:** `kagglehub` Python package
