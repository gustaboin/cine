from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
# Ya no necesitamos importar mysql.connector directamente aquí, lo hacemos a través de nuestro conector
# import mysql.connector 
import math
import random
import os
from dotenv import load_dotenv
from datetime import timedelta
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from urllib.parse import urlencode
import requests 

# --- Importamos nuestra clase de conexión personalizada ---
from mariadb_connector import MariaDBConnection
from mysql.connector import Error # Importamos Error para el manejo de excepciones

# Inicialización
app = Flask(__name__)
app.secret_key = 'claveGus' # ¡Recuerda, usa una clave segura en producción!
app.permanent_session_lifetime = timedelta(seconds=180)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Cargar variables de entorno (solo las que no van en MariaDBConnection)
load_dotenv()
# DB_HOST, DB_USER, DB_PASSWORD, DB_NAME ya se cargan dentro de mariadb_connector.py
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "password")
API_KEY = os.getenv("API_KEY") # Para tus llamadas a TMDb

# Clase de usuario
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Cargador de usuario para Flask-Login
@login_manager.user_loader
def load_user(user_id):
    if user_id == ADMIN_USER:
        return User(id=user_id)
    return None

# Renovar sesión en cada petición
@app.before_request
def renovar_sesion():
    session.permanent = True

# --- Eliminamos la función get_db_connection(), ya no la necesitamos ---
# La clase MariaDBConnection se encarga de esto.

@app.route('/')
def index():
    search = request.args.get('search', '')
    actor = request.args.get('actor', '')
    director = request.args.get('director', '')
    country = request.args.get('country', '')
    genre = request.args.get('genre', '')
    order_by = request.args.get('order_by', 'IMDbRating')
    page = int(request.args.get('page', 1))
    per_page = 9
    offset = (page - 1) * per_page

    filters = []
    params = []

    if search:
        filters.append("M.Title LIKE %s")
        params.append(f"%{search}%")
    if actor:
        filters.append("A.Name LIKE %s")
        params.append(f"%{actor}%")
    if director:
        filters.append("D.Name LIKE %s")
        params.append(f"%{director}%")
    if country:
        filters.append("M.CountryID = %s")
        params.append(country)
    if genre:
        filters.append("M.GenreID = %s")
        params.append(genre)

    where_clause = "WHERE " + " AND ".join(filters) if filters else ""

    # Inicializamos las variables que se usan en el template, para que siempre existan
    movies = []
    countries_list = []
    genre_list = []
    total = 0
    total_pages = 0
    total_watched = 0

    try:
        # --- Usamos el context manager para la conexión ---
        with MariaDBConnection() as cursor:
            # Total para paginación
            count_query = f"""
                SELECT COUNT(DISTINCT M.MovieID)
                FROM Movies M
                LEFT JOIN MovieActors MA ON M.MovieID = MA.MovieID
                LEFT JOIN Actors A ON MA.ActorID = A.ActorID
                JOIN Directors D ON M.DirectorID = D.DirectorID
                LEFT JOIN Genres G ON M.GenreID = G.GenreID
                {where_clause}
            """
            cursor.execute(count_query, params)
            total = cursor.fetchone()['COUNT(DISTINCT M.MovieID)']

            order_clause = {
                'title': 'M.Title ASC',
                'release_year': 'M.ReleaseYear DESC',
                'genre': 'G.Name ASC',
                'IMDbRating': 'M.IMDbRating DESC',
                'country': 'C.Name ASC',
                'watched': 'M.Watched DESC',
                'random': 'RAND()'
            }.get(order_by, 'M.IMDbRating DESC')

            query = f"""
                        SELECT M.MovieID, M.Title, M.ReleaseYear, M.ImageFilename, M.TrailerURL, M.CountryID, 
                        M.GenreID, D.Name AS Director, G.Name AS Genre, C.Name AS Country, M.Watched, M.IMDbRating
                        FROM Movies M
                        LEFT JOIN MovieActors MA ON M.MovieID = MA.MovieID
                        LEFT JOIN Actors A ON MA.ActorID = A.ActorID
                        JOIN Directors D ON M.DirectorID = D.DirectorID
                        JOIN Genres G ON M.GenreID = G.GenreID
                        JOIN Countries C ON M.CountryID = C.CountryID
                        {where_clause}
                        GROUP BY M.MovieID, M.Title, M.ReleaseYear, M.ImageFilename, M.TrailerURL, 
                        M.GenreID, D.Name, G.Name, C.Name, M.Watched, M.IMDbRating, M.CountryID
                        ORDER BY {order_clause}
                        LIMIT %s OFFSET %s 
                        """
            cursor.execute(query, params + [per_page, offset])
            movies = cursor.fetchall()

            total_pages = math.ceil(total / per_page)

            cursor.execute("SELECT CountryID, Name FROM Countries C WHERE EXISTS (SELECT 1 FROM Movies M WHERE M.CountryID = C.CountryID) ORDER BY Name")
            countries_list = cursor.fetchall()
            #print(f"DEBUG: Contenido de countries_list: {countries_list}")

            cursor.execute("SELECT COUNT(*) FROM Movies WHERE Watched = 1")
            total_watched = cursor.fetchone()['COUNT(*)']

            cursor.execute("SELECT GenreID, Name FROM Genres ORDER BY Name")
            genre_list = cursor.fetchall()
            #print(f"DEBUG: Contenido de genre_list: {genre_list}")

    except Error as err: # Capturamos el error específico de mysql.connector
        print(f"Error en la consulta a la base de datos en index: {err}")
        flash('Error al cargar las películas. Intenta nuevamente más tarde.', 'danger')
        # Las variables ya están inicializadas, no es necesario reasignar aquí

    query_dict = {
        'search': search,
        'actor': actor,
        'director': director,
        'country': country,
        'genre': genre,
        'order_by': order_by
        }
    # Filtra los valores vacíos para no incluirlos en la URL
    encoded_params = urlencode({k: v for k, v in query_dict.items() if v})
    # Añade el '&' solo si hay parámetros codificados
    query_params = '&' + encoded_params if encoded_params else ''

    countries_list = [(c['CountryID'], c['Name']) for c in countries_list]
    genre_list = [(g['GenreID'], g['Name']) for g in genre_list]

    return render_template("index.html",
                            menu='index',
                            movies=movies,
                            page=page,
                            total_pages=total_pages,
                            search=search,
                            actor=actor,
                            director=director,
                            country=country,
                            countries_list=countries_list,
                            total_movies=total,
                            total_watched=total_watched,
                            order_by=order_by,
                            genre_list=genre_list,
                            query_params = query_params
    )

# Rutas de Películas


@app.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    movie = None
    actors = []
    
    try:
        with MariaDBConnection() as cursor:
            cursor.execute("""
                SELECT M.movieID, M.Title, M.ReleaseYear, M.ImageFilename, M.Watched, M.IMDbRating, M.TrailerURL, D.Name as Director, G.Name as Genre, C.Name as Country, M.CountryID
                FROM Movies M
                JOIN Directors D ON M.DirectorID = D.DirectorID
                JOIN Genres G ON M.GenreID = G.GenreID
                JOIN Countries C ON M.CountryID = C.CountryID
                WHERE M.MovieID = %s
            """, (movie_id,))
            movie = cursor.fetchone()

            cursor.execute("""
                SELECT A.Name, A.ImageFilename, A.ActorID
                FROM MovieActors MA
                JOIN Actors A ON MA.ActorID = A.ActorID
                WHERE MA.MovieID = %s
            """, (movie_id,))
            
            actors = cursor.fetchall()

    except Error as err:
        print(f"Error al obtener detalles de la película {movie_id}: {err}")
        flash('Error al cargar los detalles de la película. Intenta nuevamente.', 'danger')
        # Podrías redirigir a una página de error o al índice
        return redirect(url_for('index'))

    if not movie:
        return "Película no encontrada", 404

    null_images = ['null.jpg', 'null1.jpg', 'null2.jpg', 'null3.jpg', 'null5.jpg', 'null6.jpg']

    # Asignar imagen aleatoria a actores sin imagen
    for actor in actors:
        if not actor['ImageFilename']:
            actor['ImageFilename'] = random.choice(null_images)
            actor['is_null'] = True
        else:
            actor['is_null'] = False
            
    previous_url = request.referrer or url_for('index')
            
    return render_template("movie_detail.html", movie=movie, actors=actors, previous_url=previous_url)

@app.route('/mark_watched/<int:movie_id>', methods=['POST'])
@login_required # Solo usuarios logueados pueden marcar como vista
def mark_watched(movie_id):
    try:
        with MariaDBConnection() as cursor:
            # El commit/rollback se maneja automáticamente por el __exit__ del context manager
            cursor.execute("UPDATE Movies SET Watched = 1 WHERE MovieID = %s", (movie_id,))
        return jsonify({"success": True})
    except Error as e:
        print(f"[ERROR] Al marcar como vista: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# Rutas de Sagas


@app.route('/sagas')
def sagas():
    sagas_data = [] # Cambié el nombre para evitar confusión con el módulo saga
    try:
        with MariaDBConnection() as cursor:
            # Obtener todas las sagas con conteo de películas y vistas
            cursor.execute("""
                SELECT S.SagaID, S.Name, S.Slug, S.Description, S.ImageFilename,
                    IFNULL(COUNT(M.MovieID),0) AS total,
                    SUM(CASE WHEN M.Watched = 1 THEN 1 ELSE 0 END) AS watched
                FROM Saga S
                LEFT JOIN Movies M ON S.SagaID = M.SagaID
                GROUP BY S.SagaID, S.Name, S.Slug, S.Description, S.ImageFilename
            """)
            
            for row in cursor.fetchall():
                sagas_data.append({ # Usamos sagas_data aquí
                    'id': row['SagaID'],
                    'name': row['Name'],
                    'slug': row['Slug'],
                    'description': row['Description'],
                    'image': row['ImageFilename'],
                    'watched': row['watched'] or 0, # Asegúrate de que 'watched' sea 0 si es NULL
                    'total': row['total'] or 0 # Asegúrate de que 'total' sea 0 si es NULL
                })
    except Error as err:
        print(f"Error al cargar las sagas: {err}")
        flash('Error al cargar las sagas. Intenta nuevamente.', 'danger')

    return render_template("sagas.html", menu='sagas', sagas=sagas_data) # Pasamos sagas_data al template

@app.route('/saga/<slug>')
def ver_saga(slug):
    saga = None
    movies = []
    try:
        with MariaDBConnection() as cursor:
            # Obtener datos de la saga
            cursor.execute("SELECT SagaID, Name, Description FROM Saga WHERE Slug = %s", (slug,))
            saga = cursor.fetchone()
            
            if not saga:
                return "Saga no encontrada", 404 # Mejor manejarlo aquí si no se encuentra la saga

            # Obtener las películas de esa saga
            cursor.execute("""
                SELECT MovieID, Title, ReleaseYear, Watched, ImageFilename
                FROM Movies
                WHERE SagaID = %s
                ORDER BY ReleaseYear
            """, (saga['SagaID'],)) # Accedemos al ID como clave de diccionario

            movies = cursor.fetchall()
            
    except Error as err:
        print(f"Error al cargar la saga {slug}: {err}")
        flash('Error al cargar los detalles de la saga. Intenta nuevamente.', 'danger')
        return redirect(url_for('sagas')) # Redirigir a la lista de sagas en caso de error

    return render_template("ver_saga.html", saga=saga, movies=movies)


# Rutas de Administración


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: # Si ya está logueado, redirigir
        return redirect(url_for('admin_movies'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == ADMIN_USER and password == ADMIN_PASS:
            user = User(id=username)
            login_user(user)
            session.permanent = True
            flash('Inicio de sesión exitoso.', 'success') # Mensaje de éxito
            return redirect(url_for('admin_movies'))
        else:
            flash('Credenciales incorrectas. Intenta de nuevo.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()  # Cierra la sesión del usuario
    flash('Has cerrado sesión exitosamente.', 'success')  # Mensaje de éxito
    return redirect(request.referrer or url_for('index')) 

@app.route('/admin/movies')
@login_required # Protege esta ruta
def admin_movies():
    page = int(request.args.get('page', 1))
    per_page = 15
    offset = (page - 1) * per_page

    movies = []
    total_movies = 0
    total_pages = 0

    try:
        with MariaDBConnection() as cursor:
            # Contar el total de películas
            cursor.execute("SELECT COUNT(*) FROM Movies")
            total_movies = cursor.fetchone()['COUNT(*)']

            # Obtener las películas paginadas
            cursor.execute("SELECT MovieID, Title, ReleaseYear, CountryID FROM Movies ORDER BY Title LIMIT %s OFFSET %s", (per_page, offset))
            movies = cursor.fetchall()
            
            total_pages = math.ceil(total_movies / per_page)

    except Error as err:
        print(f"Error al cargar películas de administración: {err}")
        flash('Error al cargar las películas para administración. Intenta nuevamente.', 'danger')

    # Calcular el rango de páginas a mostrar
    page_range = 2  # Número de páginas a mostrar a cada lado de la página actual
    start_page = max(1, page - page_range)
    end_page = min(total_pages, page + page_range)

    return render_template("admin.html", movies=movies, page=page, total_pages=total_pages, start_page=start_page, end_page=end_page)


@app.route('/edit_movie/<int:movie_id>', methods=['GET', 'POST'])
@login_required # Protege esta ruta
def edit_movie(movie_id):
    movie = None
    countries_list = []
    directors_list = []
    saga_list = []

    try:
        with MariaDBConnection() as cursor:
            if request.method == 'POST':
                title = request.form['title']
                release_year = request.form['release_year']
                country_id = request.form['country_id']
                director_id = request.form['director_id']
                ImageFilename = request.form['Filename'] or None
                IMDbRating = request.form['IMDbRating'] or None
                TrailerURL = request.form['TrailerURL'] or None
                SagaId = request.form['saga_id'] or None
                
                print(f"Updating movie: {title}, {release_year}, {country_id}, {director_id}, {ImageFilename}, {IMDbRating}, {TrailerURL}, {SagaId}, {movie_id}")

                cursor.execute("""
                    UPDATE Movies
                    SET Title = %s, ReleaseYear = %s, CountryID = %s, DirectorID = %s, ImageFilename = %s, IMDbRating =%s, TrailerURL=%s, SagaId=%s
                    WHERE MovieID = %s
                """, (title, release_year, country_id, director_id, ImageFilename, IMDbRating, TrailerURL, SagaId, movie_id))
                # El commit se hace automáticamente en __exit__ si no hay errores

                flash('Película Actualizada Correctamente.', 'success')
                return redirect(url_for('movie_detail', movie_id=movie_id)) 
            
            # Cargar datos de la película (para GET request o si POST falla)
            cursor.execute("SELECT * FROM Movies WHERE MovieID = %s", (movie_id,))
            movie = cursor.fetchone()

            # Obtener listas de países y directores para el formulario
            cursor.execute("SELECT CountryID, Name FROM Countries ORDER BY Name")
            countries_list = cursor.fetchall()

            cursor.execute("SELECT DirectorID, Name FROM Directors ORDER BY Name")
            directors_list = cursor.fetchall()
            
            cursor.execute("SELECT SagaID, Name FROM Saga ORDER BY Name")
            saga_list = cursor.fetchall()

    except Error as e:
        print(f"[ERROR] Al editar película: {e}")
        flash('Error al actualizar la película. Intenta nuevamente.', 'danger')
        # Si ocurre un error en GET, movie y listas estarán vacías, lo que el template debería manejar.
        # Podrías redirigir a admin_movies si no se encuentra la película o hay un error de DB
        if not movie: # Si la película no se cargó, redirigir
            return redirect(url_for('admin_movies'))

    # Si movie es None aquí, significa que no se encontró la película por ID (en GET)
    if not movie and request.method == 'GET':
        return "Película no encontrada", 404

    return render_template("edit_movie.html", movie=movie, countries_list=countries_list, directors_list=directors_list, saga_list=saga_list)


# Rutas de Actores y TMDb


@app.route("/actor/<int:actor_id>")
def actor_profile(actor_id): 
    actor_data = None
    movies_tmdb = []
    
    try:
        with MariaDBConnection() as cursor:
            # Obtener datos del actor incluyendo el TmdbID
            cursor.execute("""
                SELECT a.Name, p.Bio, p.BirthDate, p.Country, p.ImageFilename, p.TmdbID, p.Imdb_id
                FROM ActorProfiles p
                JOIN Actors a ON a.ActorID = p.ActorID
                WHERE p.ActorID = %s
            """, (actor_id,))

            actor_data = cursor.fetchone() # Usamos actor_data para no confundir con 'actor' en el loop
            
            if not actor_data:
                return "Actor no encontrado", 404

            # Accedemos a los valores del diccionario
            actor_display = { # Usamos un nombre diferente para la variable que se pasa al template
                "name": actor_data['Name'],
                "bio": actor_data['Bio'] or "Nada que ver", # Mejor un mensaje más descriptivo que "Nothing here"
                "birthdate": actor_data['BirthDate'], 
                "country": actor_data['Country'] or "País no especificado", 
                "image": actor_data['ImageFilename'] or "null.jpg",
                "tmdb_id": actor_data['TmdbID'],
                "imdb_id": actor_data['Imdb_id'] or "N/A"
            }

        # Fuera del bloque 'with' para llamadas a API externa
        # 1. Obtener las películas del actor desde TMDb usando el TmdbID
        movies_tmdb = get_actor_movies(actor_display["tmdb_id"])

        # 2. Obtener los TMDb IDs de las películas
        tmdb_movie_ids = [movie["id"] for movie in movies_tmdb]

        # 3. Verificar qué películas están en tu base de datos
        owned_tmdb_ids = get_movies_in_collection(tmdb_movie_ids)

        # 4. Marcar cuáles películas están en la colección
        for movie in movies_tmdb:
            movie["owned"] = movie["id"] in owned_tmdb_ids

    except Error as err:
        print(f"Error al obtener perfil del actor {actor_id}: {err}")
        flash('Error al cargar el perfil del actor. Intenta nuevamente.', 'danger')
        return redirect(url_for('index')) # Redirigir en caso de error

    return render_template("profile.html", actor=actor_display, movies=movies_tmdb)


# TMDb API calls
# Las variables de entorno ya están cargadas al inicio del script
# API_KEY está definido globalmente arriba
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_DETAIL_URL = "https://api.themoviedb.org/3/movie"


def get_actor_movies(tmdb_actor_id):
    url = f"https://api.themoviedb.org/3/person/{tmdb_actor_id}/movie_credits?api_key={API_KEY}&language=es-ES"
    response = requests.get(url)
    data = response.json()
    
    if response.status_code != 200:
        print(f"Error en la llamada a TMDb: {data.get('status_message', 'Desconocido')}")
        return []

    movies = data.get("cast", [])
    movies = sorted(
        [m for m in movies if m.get("release_date")],
        key=lambda x: x["release_date"],
        reverse=True
    )
    return movies


def get_movies_in_collection(tmdb_ids):
    if not tmdb_ids:
        return set()

    movies_in_db = set()
    try:
        # --- Usamos el context manager aquí también ---
        with MariaDBConnection() as cursor:
            placeholders = ','.join(['%s'] * len(tmdb_ids))
            query = f"SELECT TmdbID FROM Movies WHERE TmdbID IN ({placeholders})"
            cursor.execute(query, tmdb_ids)
            
            # Recuperar los TmdbID de las películas que están en la colección
            movies_in_db = set(row['TmdbID'] for row in cursor.fetchall()) # Acceder por clave si dictionary=True
            
            print(f"Películas en la base de datos: {movies_in_db}") 
            
    except Error as e:
        print(f"Error al obtener películas en colección desde DB: {e}")
        # En caso de error, el set vacío inicial se retornará

    return movies_in_db


if __name__ == "__main__":
    app.run(debug=True)