import os
import json
import requests
import pandas as pd
from google.oauth2 import service_account
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from datetime import datetime
import spacy
from transformers import pipeline, AutoTokenizer

# Cargar el modelo de spaCy en español
nlp = spacy.load('es_core_news_sm')

# Cargar el modelo de análisis de sentimientos de Hugging Face
sentiment_analyzer = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")
tokenizer = AutoTokenizer.from_pretrained("nlptown/bert-base-multilingual-uncased-sentiment")

# Cargar el modelo de análisis de emociones en español
emotion_analyzer = pipeline("text-classification", model="finiteautomata/beto-emotion-analysis")

def truncate_text(text, max_length=512):
    # Trunca el texto usando el tokenizer del modelo de sentimientos
    encoding = tokenizer(text, truncation=True, padding='max_length', max_length=max_length, return_tensors='pt')
    return tokenizer.decode(encoding['input_ids'][0], skip_special_tokens=True)

def analyze_sentiments_and_emotions():
    google_credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    credentials = service_account.Credentials.from_service_account_file(
        google_credentials_path, scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    client = bigquery.Client(credentials=credentials, project=credentials.project_id)
    
    dataset_id = 'ASP'
    table_id = 'movie_reviews'
    
    query = f"""
        SELECT movie_id, review_id, review_content FROM {dataset_id}.{table_id}
    """
    df_reviews = client.query(query).to_dataframe()
    
    sentiment_results = []
    
    for index, row in df_reviews.iterrows():
        review_content = row["review_content"]
        truncated_review = truncate_text(review_content)
        
        # Análisis de sentimiento
        sentiment_result = sentiment_analyzer(truncated_review, truncation=True, max_length=512)
        sentiment_label = sentiment_result[0]['label']
        
        sentiment_map = {
            '1 star': 'Muy Negativo',
            '2 stars': 'Negativo',
            '3 stars': 'Neutral',
            '4 stars': 'Positivo',
            '5 stars': 'Muy Positivo'
        }
        sentiment = sentiment_map.get(sentiment_label, 'Desconocido')
        
        # Análisis de emociones en español
        emotion_result = emotion_analyzer(truncated_review, truncation=True, max_length=512)
        emotion_label = emotion_result[0]['label']
        
        emotion_map = {
            'anger': 'Enfado',
            'fear': 'Miedo',
            'joy': 'Felicidad',
            'love': 'Amor',
            'sadness': 'Tristeza',
            'surprise': 'Sorpresa',
            'disgust': 'Disgusto',
            'optimism': 'Optimismo',
            'pessimism': 'Pesimismo',
            'neutral': 'Neutral'
        }
        emotion = emotion_map.get(emotion_label, 'Desconocido')
        
        sentiment_results.append({
            "movie_id": row["movie_id"],
            "review_id": row["review_id"],
            "sentiment": sentiment,
            "emotion": emotion,
            "load_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    df_sentiments = pd.DataFrame(sentiment_results)
    return df_sentiments

def upload_to_bigquery(df_sentiments):
    google_credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    credentials = service_account.Credentials.from_service_account_file(
        google_credentials_path, scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    
    client = bigquery.Client(credentials=credentials, project=credentials.project_id)
    dataset_id = 'ASP'
    table_id = 'reviews_sentiment'
    
    table_ref = client.dataset(dataset_id).table(table_id)
    try:
        client.get_table(table_ref)
        print(f"La tabla {table_id} ya existe. Se insertarán datos nuevos.")
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE",  # Reemplazar los datos existentes
            autodetect=True
        )
    except NotFound:
        print(f"La tabla {table_id} no existe. Se creará.")
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_EMPTY",  # Crear la tabla si no existe
            autodetect=True
        )
    
    load_job = client.load_table_from_dataframe(df_sentiments, table_ref, job_config=job_config)
    load_job.result()
    print(f"Datos subidos a BigQuery en la tabla {table_id} del dataset {dataset_id}.")

if __name__ == "__main__":
    df_sentiments = analyze_sentiments_and_emotions()
    upload_to_bigquery(df_sentiments)
    print("Proceso finalizado exitosamente.")
