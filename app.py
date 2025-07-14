from flask import Flask, render_template, request, redirect, url_for, jsonify
import pyodbc
import math


app = Flask(__name__)

# 🔗 Conexión a SQL Server
conn_str = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=HOME;"  # Cambiá esto según tu instancia
    "Database=MovieDB;"
    "Trusted_Connection=yes;"
)

# 📄 Ruta principal + search
@app.route('/')
def index():
    search = request.args.get('search', '')
    actor = request.args.get('actor', '')
    country = request.args.get('country', '')
    page = int(request.args.get('page', 1))
    per_page = 30
    offset = (page - 1) * per_page

    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()

        # Conteo total para paginación
        if actor:
            count_query = """
                SELECT COUNT(DISTINCT M.MovieID)
                FROM Movies M
                JOIN MovieActors MA ON M.MovieID = MA.MovieID
                JOIN Actors A ON MA.ActorID = A.ActorID
                WHERE A.Name LIKE ?
            """
            cursor.execute(count_query, ('%' + actor + '%',))
            total = cursor.fetchone()[0]

            query = """
                SELECT DISTINCT M.MovieID, M.Title, M.ReleaseYear, M.ImageFilename, D.Name AS Director, G.Name AS Genre, M.CountryID as CountryID, M.Watched
                FROM Movies M
                JOIN Directors D ON M.DirectorID = D.DirectorID
                JOIN Genres G ON M.GenreID = G.GenreID
                JOIN MovieActors MA ON M.MovieID = MA.MovieID
                JOIN Actors A ON MA.ActorID = A.ActorID
                WHERE A.Name LIKE ?
                ORDER BY M.ReleaseYear
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """
            cursor.execute(query, ('%' + actor + '%', offset, per_page))

        elif search:
            count_query = "SELECT COUNT(*) FROM Movies WHERE Title LIKE ?"
            cursor.execute(count_query, ('%' + search + '%',))
            total = cursor.fetchone()[0]

            query = """
                SELECT M.MovieID, M.Title, M.ReleaseYear, M.ImageFilename, D.Name AS Director, G.Name AS Genre, M.CountryID as CountryID, M.Watched
                FROM Movies M
                JOIN Directors D ON M.DirectorID = D.DirectorID
                JOIN Genres G ON M.GenreID = G.GenreID
                WHERE M.Title LIKE ?
                ORDER BY M.ReleaseYear
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """
            cursor.execute(query, ('%' + search + '%', offset, per_page))
        
        elif country:
            count_query = "SELECT COUNT(*) FROM Movies WHERE CountryID = ?"
            cursor.execute(count_query, (country,))
            total = cursor.fetchone()[0]

            query = """
                SELECT M.MovieID, M.Title, M.ReleaseYear, M.ImageFilename, D.Name AS Director, G.Name AS Genre, M.CountryID as CountryID, M.Watched
                FROM Movies M
                JOIN Directors D ON M.DirectorID = D.DirectorID
                JOIN Genres G ON M.GenreID = G.GenreID
                WHERE M.CountryID = ?
                ORDER BY M.ReleaseYear
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """
            cursor.execute(query, (country, offset, per_page))

        else:
            count_query = "SELECT COUNT(*) FROM Movies"
            cursor.execute(count_query)
            total = cursor.fetchone()[0]

            query = """
                SELECT M.MovieID, M.Title, M.ReleaseYear, M.ImageFilename, D.Name AS Director, G.Name AS Genre, M.CountryID as CountryID, M.Watched
                FROM Movies M
                JOIN Directors D ON M.DirectorID = D.DirectorID
                JOIN Genres G ON M.GenreID = G.GenreID
                ORDER BY M.ReleaseYear
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """
            cursor.execute(query, (offset, per_page))
        movies = cursor.fetchall()
        
        total_pages = math.ceil(total / per_page)

        cursor.execute("SELECT CountryID, Name FROM Countries ORDER BY Name")
        countries_list = cursor.fetchall()
        
    return render_template("index.html", movies=movies, page=page, total_pages=total_pages, search=search, actor=actor,countries_list=countries_list)

# 🎬 Detalle de película
@app.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT M.Title, M.ReleaseYear, M.ImageFilename, M.Watched, D.Name as Director, G.Name as Genre, C.Name as Country
            FROM Movies M
            JOIN Directors D ON M.DirectorID = D.DirectorID
            JOIN Genres G ON M.GenreID = G.GenreID
            JOIN Countries C ON M.CountryID = C.CountryID
            WHERE M.MovieID = ?
        """, (movie_id,))
        movie = cursor.fetchone()

        cursor.execute("""
            SELECT A.Name
            FROM MovieActors MA
            JOIN Actors A ON MA.ActorID = A.ActorID
            WHERE MA.MovieID = ?
        """, (movie_id,))
        actors = cursor.fetchall()

        cast = [actor[0] for actor in actors]
    return render_template("movie_detail.html", movie=movie, cast=cast)

# Agrego un upd para marcar las pelis vista
@app.route('/mark_watched/<int:movie_id>', methods=['POST'])
def mark_watched(movie_id):
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE Movies SET Watched = 1 WHERE MovieID = ?", movie_id)
        conn.commit()
    # Redirige a la página anterior (referrer) o al home
    #return redirect(request.referrer or url_for('index'))
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(debug=True)
