import os
import re
import requests
import pyodbc
import time
from urllib.parse import quote
from dotenv import load_dotenv

# TMDb
load_dotenv()
API_KEY = os.getenv("API_KEY")
print("API KEY TMDB:", API_KEY)
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_DETAIL_URL = "https://api.themoviedb.org/3/movie"

# SQL Server connection
conn_str = os.getenv("conn_str")
print (conn_str)

# Carpeta raíz donde están las películas
carpeta_base = r"T:\Cine\a"
#carpeta_base = r'X:\Descargas\u-torrent\descargado\Action'

print(carpeta_base)
# Dónde guardar las imágenes
carpeta_imagenes = "static/images"

os.makedirs(carpeta_imagenes, exist_ok=True)

def limpiar_nombre(nombre):
    nombre = nombre.lower()
    nombre = re.sub(r"[^\w\s]", '', nombre)
    nombre = re.sub(r"\s+", '_', nombre)
    return nombre.strip()

def buscar_pelicula_tmdb(titulo, anio):
    params = {"api_key": API_KEY, "query": titulo, "year": anio, "language": "en-US"}
    r = requests.get(TMDB_SEARCH_URL, params=params)
    data = r.json()
    return data["results"][0] if data["results"] else None

def obtener_detalles_tmdb(movie_id):
    r = requests.get(f"{TMDB_DETAIL_URL}/{movie_id}?api_key={API_KEY}&append_to_response=credits")
    return r.json()

def guardar_imagen(poster_path, nombre_archivo):
    url = f"https://image.tmdb.org/t/p/w500{poster_path}"
    ruta = os.path.join(carpeta_imagenes, nombre_archivo)
    r = requests.get(url)
    if r.status_code == 200:
        with open(ruta, 'wb') as f:
            f.write(r.content)
        return True
    return False

def insertar_en_db(titulo, anio, director, genero, country_code, country_name, filename, cast):
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()

        # Insertar país (primero, y solo una vez)
        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM Countries WHERE CountryID = ?)
            INSERT INTO Countries (CountryID, Name) VALUES (?, ?)
        """, country_code, country_code, country_name)

        # Insertar director
        cursor.execute("IF NOT EXISTS (SELECT 1 FROM Directors WHERE Name=?) INSERT INTO Directors(Name) VALUES (?)", director, director)
        cursor.execute("SELECT DirectorID FROM Directors WHERE Name=?", director)
        director_id = cursor.fetchone()[0]

        # Insertar género
        cursor.execute("IF NOT EXISTS (SELECT 1 FROM Genres WHERE Name=?) INSERT INTO Genres(Name) VALUES (?)", genero, genero)
        cursor.execute("SELECT GenreID FROM Genres WHERE Name=?", genero)
        genre_id = cursor.fetchone()[0]

        # Insertar película
        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM Movies WHERE Title=? AND ReleaseYear=?)
            INSERT INTO Movies (Title, ReleaseYear, DirectorID, GenreID, CountryID, ImageFilename)
            VALUES (?, ?, ?, ?, ?, ?)
        """, titulo, anio, titulo, anio, director_id, genre_id, country_code, filename)

        # Obtener MovieID
        cursor.execute("SELECT MovieID FROM Movies WHERE Title=? AND ReleaseYear=?", titulo, anio)
        movie_id_row = cursor.fetchone()
        if not movie_id_row:
            print(f"❌ No se pudo obtener MovieID para {titulo} ({anio})")
            return
        movie_id = movie_id_row[0]

        # Insertar actores
        for actor in cast[:5]:
            cursor.execute("IF NOT EXISTS (SELECT 1 FROM Actors WHERE Name=?) INSERT INTO Actors(Name) VALUES (?)", actor, actor)
            cursor.execute("SELECT ActorID FROM Actors WHERE Name=?", actor)
            actor_id = cursor.fetchone()[0]

            cursor.execute("IF NOT EXISTS (SELECT 1 FROM MovieActors WHERE MovieID=? AND ActorID=?) "
                "INSERT INTO MovieActors(MovieID, ActorID) VALUES (?, ?)",
                movie_id, actor_id, movie_id, actor_id)

        conn.commit()



def recorrer_carpeta(base):
    for root, dirs, files in os.walk(base):
        for nombre in dirs:
            match = re.match(r"(\d{4}) - (.+)", nombre)
            if match:
                anio, titulo = match.groups()
                anio = int(anio)
                director = os.path.basename(os.path.dirname(root))

                print(f"🎬 Procesando: {titulo} ({anio}) - Dir: {director}")
                info = buscar_pelicula_tmdb(titulo, anio)
                if not info:
                    print(f"⚠️ No encontrada: {titulo}")
                    continue

                detalles = obtener_detalles_tmdb(info["id"])
                cast = [actor["name"] for actor in detalles.get("credits", {}).get("cast", [])]
                poster_path = detalles.get("poster_path")
                genero = detalles["genres"][0]["name"] if detalles["genres"] else "Desconocido"

                director_api = ""
                for crew in detalles["credits"]["crew"]:
                    if crew["job"] == "Director":
                        director_api = crew["name"]
                        break

                paises = detalles.get("production_countries", [])
                if paises:
                    country_code = paises[0]["iso_3166_1"]
                    country_name = paises[0]["name"]
                else:
                    country_code = 'XX'
                    country_name = 'Unknown'

                filename = limpiar_nombre(titulo) + ".jpg"
                if poster_path:
                    guardar_imagen(poster_path, filename)

                # ⚠️ Acá corregido: pasar country_code y country_name, no 'pais'
                insertar_en_db(titulo, anio, director_api or director, genero, country_code, country_name, filename, cast)

                time.sleep(0.5)

# 🚀 Ejecutar
recorrer_carpeta(carpeta_base)


# otro script para levantar las pelis q tengo en el otro disco

def obtener_saga(collection_id):
    url = f"https://api.themoviedb.org/3/collection/{collection_id}"
    params = {"api_key": API_KEY}  # No pongas language para evitar que 'parts' venga vacío
    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        print(f"❌ Error al obtener la saga (ID {collection_id})")
        return []
    data = resp.json()
    return data.get("parts", [])


def importar_saga(collection_id):
    peliculas = obtener_saga(collection_id)
    if not peliculas:
        print("🛑 No se encontraron películas en la colección.")
        return

    for peli in peliculas:
        titulo = peli.get("title")
        fecha = peli.get("release_date", "")
        anio = int(fecha[:4]) if fecha else 0

        print(f"🎞️ Importando: {titulo} ({anio})")
        info = buscar_pelicula_tmdb(titulo, anio)
        if not info:
            print(f"⚠️ No encontrada: {titulo} ({anio})")
            continue

        detalles = obtener_detalles_tmdb(info["id"])

        # Actores
        cast = [actor["name"] for actor in detalles.get("credits", {}).get("cast", [])]

        # Poster
        poster_path = detalles.get("poster_path")
        filename = limpiar_nombre(titulo) + ".jpg"
        if poster_path:
            guardar_imagen(poster_path, filename)

        # Género principal
        genero = detalles["genres"][0]["name"] if detalles["genres"] else "Desconocido"

        # Director
        director_api = ""
        for crew in detalles.get("credits", {}).get("crew", []):
            if crew["job"] == "Director":
                director_api = crew["name"]
                break

        # País
        paises = detalles.get("production_countries", [])
        if paises:
            country_code = paises[0]["iso_3166_1"]
            country_name = paises[0]["name"]
        else:
            country_code = 'XX'
            country_name = 'Unknown'

        insertar_en_db(
            titulo,
            anio,
            director_api or "Desconocido",
            genero,
            country_code,
            country_name,
            filename,
            cast
        )

    time.sleep(0.4)  # evitar rate limit

importar_saga(1241)
