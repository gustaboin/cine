from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
import pyodbc
import math
import random
import os
import requests
from dotenv import load_dotenv
from datetime import timedelta
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from urllib.parse import urlencode


# Inicialización
app = Flask(__name__)
app.secret_key = 'claveGus'
app.permanent_session_lifetime = timedelta(seconds=180)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Cargar variables de entorno
load_dotenv()
conn_str = os.getenv("conn_str")
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "password")

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

# 🔗 Conexión a SQL Server

@app.route('/')
def index():
    search = request.args.get('search', '')
    actor = request.args.get('actor', '')
    director = request.args.get('director', '')
    country = request.args.get('country', '')
    genre = request.args.get('genre', '')
    order_by = request.args.get('order_by', 'IMDbRating')  # Parámetro de ordenación
    page = int(request.args.get('page', 1))
    per_page = 9
    offset = (page - 1) * per_page

    filters = []
    params = []

    # Filtros dinámicos
    if search:
        filters.append("M.Title COLLATE Latin1_General_CI_AI LIKE ?")
        params.append(f"%{search}%")
    if actor:
        filters.append("A.Name COLLATE Latin1_General_CI_AI LIKE ?")
        params.append(f"%{actor}%")
    if director:
        filters.append("D.Name COLLATE Latin1_General_CI_AI LIKE ?")
        params.append(f"%{director}%")
    if country:
        filters.append("M.CountryID = ?")
        params.append(country)
    if genre:
        filters.append("M.GenreID = ?")
        params.append(genre)

    where_clause = "WHERE " + " AND ".join(filters) if filters else ""

    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()

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
        total = cursor.fetchone()[0]

        # Películas paginadas
        order_clause = {
            'title': 'M.Title ASC',
            'release_year': 'M.ReleaseYear DESC',  
            'genre': 'G.Name ASC',
            'IMDbRating': 'M.IMDbRating DESC',  # Calificación
            'country': 'C.Name ASC',
            'watched': 'M.Watched DESC',
            'random': 'NEWID()'  # aleatorio!
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
                ORDER BY {order_clause}  -- Asegúrate de tener un ORDER BY aquí
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
                """
        cursor.execute(query, params + [offset, per_page])
        movies = cursor.fetchall()

        total_pages = math.ceil(total / per_page)

        # Lista de países
        cursor.execute("SELECT CountryID, Name FROM Countries ORDER BY Name")
        countries_list = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) FROM Movies WHERE Watched = 1")
        total_watched = cursor.fetchone()[0]

        
        cursor.execute("SELECT GenreID, Name FROM Genres ORDER BY Name")
        genre_list = cursor.fetchall()

    query_dict = {
        'search': search,
        'actor': actor,
        'director': director,
        'country': country,
        'genre': genre,
        'order_by': order_by
    }

    # Eliminar campos vacíos y construir string de query
    query_params = '&' + urlencode({k: v for k, v in query_dict.items() if v})

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
                            order_by=order_by,  # Pasar el orden a la plantilla
                            genre_list=genre_list,
                            query_params = query_params
    )

# 🎬 Detalle de película
@app.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT M.movieID, M.Title, M.ReleaseYear, M.ImageFilename, M.Watched, M.IMDbRating, M.TrailerURL, D.Name as Director, G.Name as Genre, C.Name as Country, M.CountryID
            FROM Movies M
            JOIN Directors D ON M.DirectorID = D.DirectorID
            JOIN Genres G ON M.GenreID = G.GenreID
            JOIN Countries C ON M.CountryID = C.CountryID
            WHERE M.MovieID = ?
        """, (movie_id,))
        movie = cursor.fetchone()

        cursor.execute("""
            SELECT A.Name, A.ImageFilename, A.ActorID
            FROM MovieActors MA
            JOIN Actors A ON MA.ActorID = A.ActorID
            WHERE MA.MovieID = ?
        """, (movie_id,))
        
        actors = [{'ActorID':row.ActorID, 'Name': row.Name, 'ImageFilename': row.ImageFilename} for row in cursor.fetchall()]

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

# Agrego un upd para marcar las pelis vista
@app.route('/mark_watched/<int:movie_id>', methods=['POST'])
def mark_watched(movie_id):
    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE Movies SET Watched = 1 WHERE MovieID = ?", (movie_id,))
            conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        print(f"[ERROR] Al marcar como vista: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# aca va el desarrollo para las Sagas

@app.route('/sagas')
def sagas():
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()

        # Obtener todas las sagas con conteo de películas y vistas
        cursor.execute("""
            SELECT S.SagaID, S.Name, S.Slug, S.Description, S.ImageFilename,
                ISNULL(COUNT(M.MovieID),0) AS total,
                SUM(CASE WHEN M.Watched = 1 THEN 1 ELSE 0 END) AS watched
            FROM Saga S
            LEFT JOIN Movies M ON S.SagaID = M.SagaID
            GROUP BY S.SagaID, S.Name, S.Slug, S.Description, S.ImageFilename
        """)
        
        sagas = []
        for row in cursor.fetchall():
            sagas.append({
                'id': row.SagaID,
                'name': row.Name,
                'slug': row.Slug,
                'description': row.Description,
                'image': row.ImageFilename,
                'watched': row.watched or 0,
                'total': row.total or 0
            })

    return render_template("sagas.html", menu='sagas', sagas=sagas)


@app.route('/saga/<slug>')
def ver_saga(slug):
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()

        # Obtener datos de la saga
        cursor.execute("SELECT SagaID, Name, Description FROM Saga WHERE Slug = ?", slug)
        saga = cursor.fetchone()
        if not saga:
            return "Saga no encontrada", 404

        # Obtener las películas de esa saga
        cursor.execute("""
            SELECT MovieID, Title, ReleaseYear, Watched, ImageFilename
            FROM Movies
            WHERE SagaID = ?
            ORDER BY ReleaseYear
        """, saga.SagaID)

        movies = cursor.fetchall()

    return render_template("ver_saga.html", saga=saga, movies=movies)

# en la siguiente seccion va una ruta para administrar las peliculas

# login para que solo una persona pueda editar las pelis

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == ADMIN_USER and password == ADMIN_PASS:
            user = User(id=username)
            login_user(user)
            session.permanent = True
            return redirect(url_for('admin_movies'))
        else:
            flash('Credenciales incorrectas. Intenta de nuevo.', 'danger')

    return render_template('login.html')


#logout
@app.route('/logout')
@login_required
def logout():
    logout_user()  # Cierra la sesión del usuario
    flash('Has cerrado sesión exitosamente.', 'success')  # Mensaje de éxito
    return redirect(request.referrer or url_for('index')) # Redirige a la página de inicio de sesión


@app.route('/admin/movies')
def admin_movies():

    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    page = int(request.args.get('page', 1))
    per_page = 15
    offset = (page - 1) * per_page

    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()

        # Contar el total de películas
        cursor.execute("SELECT COUNT(*) FROM Movies")
        total_movies = cursor.fetchone()[0]

        # Obtener las películas paginadas
        cursor.execute("SELECT MovieID, Title, ReleaseYear, CountryID FROM Movies ORDER BY Title OFFSET ? ROWS FETCH NEXT ? ROWS ONLY", (offset, per_page))
        movies = cursor.fetchall()

    total_pages = math.ceil(total_movies / per_page)

     # Calcular el rango de páginas a mostrar
    page_range = 2  # Número de páginas a mostrar a cada lado de la página actual
    start_page = max(1, page - page_range)
    end_page = min(total_pages, page + page_range)

    return render_template("admin.html", movies=movies, page=page, total_pages=total_pages, start_page=start_page, end_page=end_page)


@app.route('/edit_movie/<int:movie_id>', methods=['GET', 'POST'])
def edit_movie(movie_id):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()

        if request.method == 'POST':
            title = request.form['title']
            release_year = request.form['release_year']
            country_id = request.form['country_id']
            director_id = request.form['director_id']
            ImageFilename = request.form['Filename'] or None
            IMDbRating = request.form['IMDbRating'] or None
            TrailerURL = request.form['TrailerURL'] or None
            SagaId =  request.form['saga_id'] or None
            
            print(f"Updating movie: {title}, {release_year}, {country_id}, {director_id}, {ImageFilename}, {IMDbRating}, {TrailerURL}, {SagaId}, {movie_id}")

            try:
                cursor.execute("""
                    UPDATE Movies
                    SET Title = ?, ReleaseYear = ?, CountryID = ?, DirectorID = ?, ImageFilename = ?,  IMDbRating =?, TrailerURL=?, SagaId=?
                    WHERE MovieID = ?
                """, (title, release_year, country_id, director_id, ImageFilename, IMDbRating,TrailerURL,SagaId, movie_id))
                conn.commit()
                flash('Pelicula Actualizada Correctamente.', 'success')
                return redirect(url_for('movie_detail', movie_id=movie_id))  # Redirigir a los detalles de la película
            except Exception as e:
                print(f"[ERROR] Al editar película: {e}")
        # Cargar datos de la película
        cursor.execute("SELECT * FROM Movies WHERE MovieID = ?", (movie_id,))
        movie = cursor.fetchone()

        # Obtener listas de países y directores para el formulario
        cursor.execute("SELECT CountryID, Name FROM Countries ORDER BY Name")
        countries_list = cursor.fetchall()

        cursor.execute("SELECT DirectorID, Name FROM Directors ORDER BY Name")
        directors_list = cursor.fetchall()
        
        cursor.execute("SELECT SagaID, Name FROM Saga ORDER BY Name")
        saga_list = cursor.fetchall()

    return render_template("edit_movie.html", movie=movie, countries_list=countries_list, directors_list=directors_list, saga_list=saga_list)

# agrego un apartado para actores

@app.route("/actor/<int:actor_id>")
def actor_profile(actor_id): 
    
    # Conexión a la base de datos
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()

        # Obtener datos del actor incluyendo el TmdbID
        cursor.execute("""
            SELECT a.Name, p.Bio, p.BirthDate, p.Country, p.ImageFilename, p.TmdbID, p.Imdb_id
            FROM ActorProfiles p
            JOIN Actors a ON a.ActorID = p.ActorID
            WHERE p.ActorID = ?
        """, actor_id)

        row = cursor.fetchone()
        
        if not row:
            return "Actor no encontrado", 404

        actor = {
            "name": row.Name,
            "bio": row.Bio or "Nothing here ",
            "birthdate": row.BirthDate or "2018-09-12",
            "country": row.Country or "no country for old men",
            "image": row.ImageFilename or "null.jpg",
            "tmdb_id": row.TmdbID,  # Usamos el TmdbID del actor, no el imdb_id
            "imdb_id": row.Imdb_id or "not"
        }



        # 1. Obtener las películas del actor desde TMDb usando el TmdbID
        movies_tmdb = get_actor_movies(actor["tmdb_id"])  # Aquí usamos el TmdbID correcto

        # 2. Obtener los TMDb IDs de las películas
        tmdb_movie_ids = [movie["id"] for movie in movies_tmdb]

        # 3. Verificar qué películas están en tu base de datos
        owned_tmdb_ids = get_movies_in_collection(tmdb_movie_ids)

        # 4. Marcar cuáles películas están en la colección
        for movie in movies_tmdb:
            movie["owned"] = movie["id"] in owned_tmdb_ids

        # Retornar al template con los datos
        return render_template("profile.html", row=row,actor=actor, movies=movies_tmdb)



# me traigo listado de peliculas para la tarjeta de actores

# TMDb
load_dotenv()
API_KEY = os.getenv("API_KEY")
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_DETAIL_URL = "https://api.themoviedb.org/3/movie"


def get_actor_movies(tmdb_actor_id):
    # Usamos el TmdbID del actor
    url = f"https://api.themoviedb.org/3/person/{tmdb_actor_id}/movie_credits?api_key={API_KEY}"
    response = requests.get(url)
    data = response.json()
    
    if response.status_code != 200:
        print(f"Error en la llamada a TMDb: {data.get('status_message', 'Desconocido')}")
        return []

    # Obtener las películas del actor (filtrar las que tienen fecha de estreno)
    movies = data.get("cast", [])
    movies = sorted(
        [m for m in movies if m.get("release_date")],
        key=lambda x: x["release_date"],
        reverse=True
    )
    return movies


def get_movies_in_collection(tmdb_ids):
    if not tmdb_ids:  # Si no hay IDs, no hacemos la consulta
        return set()

    # Establecer la conexión a la base de datos aquí
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()

        # Crear los placeholders para la consulta
        placeholders = ','.join(['?'] * len(tmdb_ids))
        query = f"SELECT TmdbID FROM Movies WHERE TmdbID IN ({placeholders})"
        cursor.execute(query, tmdb_ids)
        
        # Recuperar los TmdbID de las películas que están en la colección
        movies_in_db = set(row[0] for row in cursor.fetchall())

        print(f"Películas en la base de datos: {movies_in_db}")  # Verifica las películas en tu colección
        
        return movies_in_db


if __name__ == "__main__":
    app.run(debug=True)