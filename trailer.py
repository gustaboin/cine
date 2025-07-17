"""
# solo 100 requets por dia me ofrece yt

import pyodbc
import requests
import time

# Claves de configuración.-

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

# Conexión a la base de datos
conn = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=MovieDB;Trusted_Connection=yes;")
cursor = conn.cursor()

def buscar_trailer_en_youtube(titulo):
    params = {
        "part": "snippet",
        "q": f"{titulo} trailer",
        "type": "video",
        "key": API_KEY,
        "maxResults": 1
    }
    response = requests.get(YOUTUBE_SEARCH_URL, params=params)
    data = response.json()

    items = data.get("items")
    if items:
        return items[0]["id"]["videoId"]
    return None

# Leer todas las películas que no tengan trailer
cursor.execute("SELECT MovieID, Title FROM Movies WHERE TrailerURL IS NULL")
peliculas = cursor.fetchall()

for movie in peliculas:
    movie_id, titulo = movie
    try:
        video_id = buscar_trailer_en_youtube(titulo)
        if video_id:
            cursor.execute("UPDATE Movies SET TrailerURL = ? WHERE MovieID = ?", video_id, movie_id)
            print(f"[✔] Trailer guardado para '{titulo}' → {video_id}")
            conn.commit()
        else:
            print(f"[✘] No se encontró trailer para '{titulo}'")
        time.sleep(1)  # Esperar para no sobrepasar el límite de cuota
    except Exception as e:
        print(f"[⚠️] Error con '{titulo}': {e}")
        continue

cursor.close()
conn.close()

"""
import requests
import pyodbc
import time
import os
from dotenv import load_dotenv

# Configuración TMDb
load_dotenv()
TMDB_API_KEY = os.getenv("API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
#print("api_key", TMDB_API_KEY)

# Conexión a la base de datos
conn_str = os.getenv("conn_str")
conn = pyodbc.connect(conn_str)
#print("connection", conn)
cursor = conn.cursor()

def obtener_trailer_key(titulo):
    try:
        # 1. Buscar la película
        search_url = f"{TMDB_BASE_URL}/search/movie"
        search_params = {
            "api_key": TMDB_API_KEY,
            "query": titulo
        }
        search_resp = requests.get(search_url, params=search_params)
        search_data = search_resp.json()

        if not search_data["results"]:
            return None

        movie_id = search_data["results"][0]["id"]

        # 2. Buscar los videos (trailers)
        video_url = f"{TMDB_BASE_URL}/movie/{movie_id}/videos"
        video_params = {"api_key": TMDB_API_KEY}
        video_resp = requests.get(video_url, params=video_params)
        video_data = video_resp.json()

        for video in video_data.get("results", []):
            if video["site"] == "YouTube" and video["type"] == "Trailer":
                return video["key"]

        return None
    except Exception as e:
        print(f"❌ Error buscando trailer para {titulo}: {e}")
        return None

# Obtener películas sin trailer
cursor.execute("SELECT MovieID, Title FROM Movies WHERE TrailerURL IS NULL")
peliculas = cursor.fetchall()

for movie_id, title in peliculas:
    print(f"🔍 Buscando trailer para: {title}")
    trailer_key = obtener_trailer_key(title)
    
    if trailer_key:
        cursor.execute("UPDATE Movies SET TrailerURL = ? WHERE MovieID = ?", (trailer_key, movie_id))
        conn.commit()
        print(f"✅ Trailer agregado: {trailer_key}")
    else:
        print(f"⚠️ No se encontró trailer para {title}")
    
    # Esperá un poquito entre requests para evitar rate limits
    time.sleep(0.5)

cursor.close()
conn.close()
print("🎬 ¡Proceso completado!")
