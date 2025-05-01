import os
import json
import requests
import pandas as pd
from google.oauth2 import service_account
from google.cloud import storage, bigquery
from google.cloud.exceptions import NotFound
from datetime import datetime

# --- Validar conexión a TMDB ---
def validate_tdbm():
    api_key = os.getenv('TMDB_API_KEY')
    if not api_key:
        return "No se encontró la clave de TMDB."
    
    try:
        url = f"https://api.themoviedb.org/3/movie/popular?api_key={api_key}&language=es-ES&page=1"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if data.get('results'):
            return f"Conexión exitosa con TMDB. Título de la primera película popular: {data['results'][0]['title']}"
        else:
            return "No se encontraron resultados en la respuesta de TMDB."
    except requests.exceptions.RequestException as e:
        return f"Error al conectar con TMDB: {e}"

# --- Validar conexión con Google Cloud Storage ---
def validate_google_cloud():
    project_id = "rock-atlas-435913-t7"
    google_credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if not os.path.exists(google_credentials_path):
        return f"No se encontró el archivo de credenciales: {google_credentials_path}"
    
    try:
        credentials = service_account.Credentials.from_service_account_file(google_credentials_path)
        client = storage.Client(credentials=credentials, project=project_id)
        return "Conexión exitosa con Google Cloud Storage."
    except Exception as e:
        return f"Error al conectar con Google Cloud Storage: {e}"
    
# --- Ejecución ---
if __name__ == "__main__":
    tdbm_message = validate_tdbm()
    print(tdbm_message)
    
    if "exitosa" in tdbm_message:
        google_cloud_message = validate_google_cloud()
        print(google_cloud_message)
