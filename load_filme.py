import os
import re
import time
import requests
import pyodbc

API_KEY = 'cb88900896421377af357e7889a646c0'
BASE_URL = 'https://api.themoviedb.org/3'
conn_str = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=MovieDB;Trusted_Connection=yes;'

def buscar_pelicula_tmdb(title, year):
    url = f"{BASE_URL}/search/movie"
    params = {
        'api_key': API_KEY,
        'query': title,
        'year': year
    }
    resp = requests.get(url, params=params)
    data = resp.json()
    results = data.get('results', [])
    if results:
        return results[0]['id']
    return None

def obtener_cast(tmdb_id):
    url = f"{BASE_URL}/movie/{tmdb_id}/credits"
    params = {'api_key': API_KEY}
    resp = requests.get(url, params=params)
    data = resp.json()
    cast = data.get('cast', [])
    return [actor['name'] for actor in cast[:5]]  # top 5 actores

def insertar_si_no_existe(cursor, tabla, columna, valor):
    # Mapeo explícito del nombre de la columna ID
    id_column_map = {
        'Countries': 'CountryID',
        'Directors': 'DirectorID',
        'Genres': 'GenreID'
    }

    id_col = id_column_map.get(tabla)
    if not id_col:
        raise ValueError(f"No se conoce la clave primaria para la tabla '{tabla}'")

    cursor.execute(f"SELECT {id_col} FROM {tabla} WHERE {columna} = ?", valor)
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute(f"INSERT INTO {tabla} ({columna}) VALUES (?)", valor)
    cursor.execute("SELECT SCOPE_IDENTITY()")
    return cursor.fetchone()[0]


def insertar_actor(cursor, actor_name):
    cursor.execute("SELECT ActorID FROM Actors WHERE Name = ?", actor_name)
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute("INSERT INTO Actors (Name) VALUES (?)", actor_name)
    cursor.execute("SELECT SCOPE_IDENTITY()")
    return cursor.fetchone()[0]

def insertar_relacion_pelicula_actor(cursor, movie_id, actor_id):
    cursor.execute("SELECT 1 FROM MovieActors WHERE MovieID = ? AND ActorID = ?", movie_id, actor_id)
    if not cursor.fetchone():
        cursor.execute("INSERT INTO MovieActors (MovieID, ActorID) VALUES (?, ?)", movie_id, actor_id)

def insertar_en_db(title, year, director, genre, country, filename, cursor):
    country_id = insertar_si_no_existe(cursor, 'Countries', 'Name', country)
    director_id = insertar_si_no_existe(cursor, 'Directors', 'Name', director)
    genre_id = insertar_si_no_existe(cursor, 'Genres', 'Name', genre)

    cursor.execute("""
        INSERT INTO Movies (Title, ReleaseYear, DirectorID, GenreID, CountryID, ImageFilename)
        VALUES (?, ?, ?, ?, ?, ?)""",
        title, year, director_id, genre_id, country_id, filename)
    cursor.execute("SELECT SCOPE_IDENTITY()")
    movie_id = cursor.fetchone()[0]

    # Buscar TMDb y obtener actores
    tmdb_id = buscar_pelicula_tmdb(title, year)
    if tmdb_id:
        cast = obtener_cast(tmdb_id)
        for actor_name in cast:
            actor_id = insertar_actor(cursor, actor_name)
            insertar_relacion_pelicula_actor(cursor, movie_id, actor_id)

    cursor.connection.commit()
    time.sleep(0.5)  # pausa para respetar límites API

def extraer_info(nombre_archivo):
    # Ejemplo para extraer título y año del nombre: "1953 - Il sole negli occhi"
    match = re.match(r'(\d{4}) - (.+)', nombre_archivo)
    if match:
        return match.group(2).strip(), int(match.group(1))
    return nombre_archivo, None

def recorrer_carpeta(base_path):
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()
        for root, dirs, files in os.walk(base_path):
            for file in files:
                if file.lower().endswith(('.mp4', '.avi', '.mkv')):
                    # Por ejemplo, la carpeta tiene info de director, género, país...
                    # Vos deberías ajustar para sacar esos datos según tu estructura
                    # Aquí un ejemplo simplificado:
                    director = "Unknown Director"
                    genre = "Unknown Genre"
                    country = "Unknown Country"

                    # Extraer título y año del archivo
                    title, year = extraer_info(file)

                    print(f"Procesando: {title} ({year})")
                    insertar_en_db(title, year, director, genre, country, file, cursor)

if __name__ == '__main__':
    carpeta_base = 'T:\Cine\Adam McKay'
    recorrer_carpeta(carpeta_base)
