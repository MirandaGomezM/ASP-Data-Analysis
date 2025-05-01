import os
import json
import requests
import pandas as pd
from google.oauth2 import service_account
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from datetime import datetime

# --- Obtener el tráiler de una película ---
def get_movie_trailer(movie_id, api_key):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos"
    params = {"api_key": api_key}
    response = requests.get(url, params=params)
    data = response.json()
    
    for video in data.get("results", []):
        if video["site"] == "YouTube" and video["type"] == "Trailer":
            return f"https://www.youtube.com/watch?v={video['key']}"
    return None

# --- Descargar próximas películas desde TMDB ---
def download_upcoming_movies():
    api_key = os.getenv('TMDB_API_KEY')
    base_url = "https://api.themoviedb.org/3/movie/upcoming"
    params = {"api_key": api_key, "language": "es-ES", "page": 1}
    
    movies = []
    
    while True:
        response = requests.get(base_url, params=params)
        data = response.json()

        for movie in data.get("results", []):
            trailer_url = get_movie_trailer(movie["id"], api_key)
            movies.append({
                "id": movie["id"],
                "poster_path": movie["poster_path"],
                "title": movie["title"],
                "release_date": movie["release_date"],
                "rating": movie.get("vote_average", 0),
                "count": movie.get("vote_count", 0),
                "overview": movie["overview"],
                "popularity": movie["popularity"],
                "trailer_url": trailer_url
            })

        if params["page"] >= data.get("total_pages", 1):
            break
        params["page"] += 1
    
    df_movies = pd.DataFrame(movies)
    df_movies["load_date"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return df_movies

# --- Subir los datos a Google BigQuery ---
def upload_to_bigquery(df_movies):
    google_credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    credentials = service_account.Credentials.from_service_account_file(
        google_credentials_path, scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    
    client = bigquery.Client(credentials=credentials, project=credentials.project_id)
    dataset_id = 'ASP'
    table_id = 'upcoming_movies'
    
    try:
        table_ref = client.dataset(dataset_id).table(table_id)
        client.get_table(table_ref)  # Verificar si la tabla existe
        print(f"La tabla {table_id} ya existe. Se reemplazará.")
        
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE", autodetect=True)
        load_job = client.load_table_from_dataframe(df_movies, table_ref, job_config=job_config)
        load_job.result()
        print(f"Datos subidos a BigQuery en la tabla {table_id} del dataset {dataset_id}.")
        
    except NotFound:
        print(f"La tabla {table_id} no existe. Se creará.")
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_EMPTY", autodetect=True)
        load_job = client.load_table_from_dataframe(df_movies, table_ref, job_config=job_config)
        load_job.result()
        print(f"Datos subidos a BigQuery en la tabla {table_id} del dataset {dataset_id}.")

# --- Ejecución ---
if __name__ == "__main__":
    df_movies = download_upcoming_movies()
    upload_to_bigquery(df_movies)
