# Proyecto TMDB a BigQuery con Visualización en Looker

Este proyecto automatiza la recolección, almacenamiento y visualización de datos de películas y series desde TMDB. La información se carga diariamente en BigQuery mediante GitHub Actions, se visualiza en Looker Studio, y los dashboards se publican en un sitio de Google Sites.

## 1. Flujo del Proyecto

### 1.1 Extracción de datos desde TMDB con Python
Los scripts `Cartelera.py`, `Populares.py`, `Rated.py`, `Proximas.py`, `Reviews.py` y `Analisis.py` utilizan la API de TMDB para obtener datos como películas en cartelera, populares, mejor valoradas, próximas y reseñas.

### 1.2 Carga de datos a BigQuery
El script `Conexiones.py` maneja la conexión con Google Cloud y realiza la carga de los datos procesados a BigQuery.

### 1.3 Automatización con GitHub Actions
En la carpeta `.github/workflows`, el archivo `Job.yaml` define un flujo de trabajo que ejecuta automáticamente la ingesta todos los días.

### 1.4 Visualización con Looker Studio
Los datos almacenados en BigQuery se utilizan para construir dashboards interactivos en Looker Studio.

### 1.5 Publicación en Google Sites
Los dashboards de Looker Studio se integran en un sitio público creado con Google Sites.

## 2. Estructura del Repositorio

```txt
├── .github/workflows/Job.yaml               # GitHub Actions workflow de ingesta
├── Analisis.py                              # Análisis de emociones y sentimiento
├── Cartelera.py                             # Películas en cartelera 
├── Conexiones.py                            # Conexiones a TMDB y BigQuery 
├── Populares.py                             # Películas populares 
├── Proximas.py                              # Próximos estrenos 
├── Rated.py                                 # Mejor valoradas 
├── Reviews.py                               # Reseñas de películas 
├── requirements.txt                         # Dependencias de Python  
```

## 3. Automatización

El flujo de trabajo definido en `.github/workflows/Job.yaml` se ejecuta diariamente y realiza lo siguiente:

- Ejecuta los scripts de extracción de datos.
- Carga los datos a BigQuery.
- Asegura la ingesta automática y actualizada.

## 4. Visualización de Resultados

### 4.1 Dashboard en Looker Studio  
[Looker Studio](https://lookerstudio.google.com/s/o6DJlU1lWtY)

### 4.2 Sitio en Google Sites con dashboards integrados  
[Google Site](https://sites.google.com/view/cinedata-hub/p%C3%A1gina-principal)

## 5. Requisitos

- API Key de TMDB: https://www.themoviedb.org/
- Proyecto de Google Cloud con BigQuery habilitado
- Archivo de credenciales `.json` para autenticación con GCP
