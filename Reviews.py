import os
import json
import requests
import re  # Para las expresiones regulares
import pandas as pd
from google.oauth2 import service_account
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from datetime import datetime
from deep_translator import GoogleTranslator

# Cargar lista de palabras prohibidas desde GitHub
url = "https://raw.githubusercontent.com/LDNOOBW/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words/master/es"
response = requests.get(url)
bad_words = response.text.splitlines()

def censor_text(text):
    for word in bad_words:
        pattern = re.compile(r'\b' + word + r'\b', re.IGNORECASE)
        text = pattern.sub(word[0] + '*' * (len(word) - 1), text)
    return text

def censor_bad_words(text):
    """
    Si el texto es tóxico, lo censura. Si no lo es, lo deja tal cual.
    """
    return censor_text(text)

def translate_text(text):
    """
    Traduce texto al español si está en inglés.
    """
    try:
        translated_text = GoogleTranslator(source='auto', target='es').translate(text)
        return translated_text
    except Exception as e:
        print(f"Error en la traducción: {e}")
        return text

def split_text_into_chunks(text, max_length=5000):
    """
    Divide el texto en fragmentos de no más de max_length caracteres.
    """
    chunks = []
    while len(text) > max_length:
        # Encuentra el último espacio antes de alcanzar el límite
        split_point = text.rfind(' ', 0, max_length)
        if split_point == -1:
            # Si no encuentra un espacio, corta directamente en el límite
            split_point = max_length
        chunks.append(text[:split_point].strip())
        text = text[split_point:].strip()
    
    # Agregar el resto del texto como un último chunk
    if text:
        chunks.append(text)
    
    return chunks

# --- Descargar reseñas de películas desde TMDB ---
def download_reviews_from_tmbd():
    google_credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    credentials = service_account.Credentials.from_service_account_file(
        google_credentials_path, scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    client = bigquery.Client(credentials=credentials, project=credentials.project_id)
    
    dataset_id = 'ASP'
    table_id = 'now_playing_movies'
    
    query = f"""
        SELECT id FROM `{dataset_id}.{table_id}`
    """
    df_movies = client.query(query).to_dataframe()

    reviews = []
    api_key = os.getenv('TMDB_API_KEY')
    reviews_url_template = "https://api.themoviedb.org/3/movie/{}/reviews"

    for movie_id in df_movies["id"]:
        page = 1
        while True:
            response = requests.get(reviews_url_template.format(movie_id), params={
                "api_key": api_key,
                "language": "es-ES",
                "page": page
            })
            data = response.json()
            
            for review in data.get("results", []):
                review_content = review["content"]
                
                # Dividir reseñas largas en fragmentos de 5000 caracteres
                chunks = split_text_into_chunks(review_content)
                
                # Concatenar los fragmentos en una sola reseña traducida y censurada
                full_translated_review = ""
                full_censured_review = ""
                for chunk in chunks:
                    # Traducción y censura
                    translated_review = translate_text(chunk)  # Traducción automática
                    censured_review = censor_bad_words(translated_review)  # Moderación
                    
                    full_translated_review += translated_review + " "  # Concatenar
                    full_censured_review += censured_review + " "  # Concatenar

                reviews.append({
                    "review_id": review["id"],  # Nuevo campo
                    "movie_id": movie_id,
                    "rating": review["author_details"].get("rating"),
                    "review_date": review["created_at"],
                    "review_content": review_content,  # Reseña original
                    "translated_review": full_translated_review.strip(),  # Reseña traducida completa
                    "censured_review": full_censured_review.strip()   # Reseña con censura completa
                })
            
            if page >= data.get("total_pages", 1):
                break
            page += 1
    
    df_reviews = pd.DataFrame(reviews)
    
    # Agregar la columna 'load_date' al DataFrame
    df_reviews["load_date"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return df_reviews

# --- Subir los datos a Google BigQuery ---
def upload_to_bigquery(df_reviews):
    google_credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # Cargar las credenciales desde el archivo de servicio
    credentials = service_account.Credentials.from_service_account_file(
        google_credentials_path, scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    
    # Crear el cliente de BigQuery con las credenciales
    client = bigquery.Client(credentials=credentials, project=credentials.project_id)
    dataset_id = 'ASP'
    table_id = 'movie_reviews'
    
    # Verificar si la tabla existe
    table_ref = client.dataset(dataset_id).table(table_id)
    try:
        client.get_table(table_ref)  # Intentar obtener la tabla
        print(f"La tabla {table_id} ya existe. Se insertarán datos nuevos.")
        
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE",  # Reemplazar los datos existentes
            autodetect=True  # Detectar el esquema automáticamente
        )
        
    except NotFound:
        print(f"La tabla {table_id} no existe. Se creará.")
        
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_EMPTY",  # Crear la tabla si no existe
            autodetect=True  # Detectar el esquema automáticamente
        )
    
    # Cargar los datos a BigQuery utilizando el método load_table_from_dataframe
    load_job = client.load_table_from_dataframe(df_reviews, table_ref, job_config=job_config)
    load_job.result()  # Esperar a que el trabajo termine
    print(f"Datos subidos a BigQuery en la tabla {table_id} del dataset {dataset_id}.")

# --- Ejecución ---
if __name__ == "__main__":
    # Descargar las reseñas y cargarlas a BigQuery
    df_reviews = download_reviews_from_tmbd()
    upload_to_bigquery(df_reviews)
    
    print("Proceso finalizado exitosamente.")
