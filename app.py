from flask import Flask, render_template, request, redirect, url_for, jsonify
import pyodbc
import math
import random
import os
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()

conn_str = os.getenv("conn_str")

# 🔗 Conexión a SQL Server


@app.route('/')
def index():
    search = request.args.get('search', '')
    actor = request.args.get('actor', '')
    director = request.args.get('director', '')
    country = request.args.get('country', '')
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
            {where_clause}
        """
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]

        # Películas paginadas
        query = f"""
            SELECT DISTINCT M.MovieID, M.Title, M.ReleaseYear, M.ImageFilename, M.TrailerURL,
                    D.Name AS Director, G.Name AS Genre, M.CountryID, M.Watched, M.IMDbRating
            FROM Movies M
            LEFT JOIN MovieActors MA ON M.MovieID = MA.MovieID
            LEFT JOIN Actors A ON MA.ActorID = A.ActorID
            JOIN Directors D ON M.DirectorID = D.DirectorID
            JOIN Genres G ON M.GenreID = G.GenreID
            {where_clause}
            ORDER BY M.IMDbRating desc
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

    return render_template("index.html",
                            menu = 'index',
                            movies=movies,
                            page=page,
                            total_pages=total_pages,
                            search=search,
                            actor=actor,
                            director=director,
                            country=country,
                            countries_list=countries_list,
                            total_movies=total,
                            total_watched = total_watched
    )


# 🎬 Detalle de película
@app.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT M.Title, M.ReleaseYear, M.ImageFilename, M.Watched, M.IMDbRating, M.TrailerURL, D.Name as Director, G.Name as Genre, C.Name as Country
            FROM Movies M
            JOIN Directors D ON M.DirectorID = D.DirectorID
            JOIN Genres G ON M.GenreID = G.GenreID
            JOIN Countries C ON M.CountryID = C.CountryID
            WHERE M.MovieID = ?
        """, (movie_id,))
        movie = cursor.fetchone()

        cursor.execute("""
            SELECT A.Name, A.ImageFilename
            FROM MovieActors MA
            JOIN Actors A ON MA.ActorID = A.ActorID
            WHERE MA.MovieID = ?
        """, (movie_id,))
        
        actors = [{'Name': row.Name, 'ImageFilename': row.ImageFilename} for row in cursor.fetchall()]

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



if __name__ == "__main__":
    app.run(debug=True)
