import requests
import pyodbc
import os
from dotenv import load_dotenv


# Cargar API KEY desde .env
load_dotenv()
TMDB_API_KEY = os.getenv("API_KEY")

# Conexión a tu base de datos
conn_str = os.getenv("conn_str")
conn = pyodbc.connect(conn_str)

cursor = conn.cursor()

# Seleccionar películas que no tengan título en inglés
cursor.execute("SELECT MovieID, Title, ReleaseYear FROM Movies WHERE EnglishTitle is null")
peliculas = cursor.fetchall()

for pelicula in peliculas:
    movie_id, title, year = pelicula

    # Llamada a TMDb
    url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "year": year
    }

    response = requests.get(url, params=params)
    search_data = response.json()

    # Validar resultados
    if search_data.get("results"):
        movie_tmdb_id = search_data["results"][0]["id"]

    # Paso 2: Obtener detalles con lenguaje en inglés
        details_url = f"https://api.themoviedb.org/3/movie/{movie_tmdb_id}"
        details_params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US"
        }

        details_response = requests.get(details_url, params=details_params)
        details_data = details_response.json()

        english_title = details_data.get("title")
        if english_title:
            print(f"✔️ {title} => {english_title}")
            cursor.execute("UPDATE Movies SET EnglishTitle = ? WHERE MovieID = ?", english_title, movie_id)
            conn.commit()
        else:
            print(f"⚠️ No se encontró original_title para {title}")
    else:
        print(f"❌ No se encontró resultado para {title}")

cursor.close()
conn.close()
