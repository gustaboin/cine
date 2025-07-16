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
            SELECT DISTINCT M.MovieID, M.Title, M.ReleaseYear, M.ImageFilename, 
                    D.Name AS Director, G.Name AS Genre, M.CountryID, M.Watched
            FROM Movies M
            LEFT JOIN MovieActors MA ON M.MovieID = MA.MovieID
            LEFT JOIN Actors A ON MA.ActorID = A.ActorID
            JOIN Directors D ON M.DirectorID = D.DirectorID
            JOIN Genres G ON M.GenreID = G.GenreID
            {where_clause}
            ORDER BY M.ReleaseYear desc
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        cursor.execute(query, params + [offset, per_page])
        movies = cursor.fetchall()

        total_pages = math.ceil(total / per_page)

        # Lista de países
        cursor.execute("SELECT CountryID, Name FROM Countries ORDER BY Name")
        countries_list = cursor.fetchall()

    return render_template("index.html",
                            movies=movies,
                            page=page,
                            total_pages=total_pages,
                            search=search,
                            actor=actor,
                            director=director,
                            country=country,
                            countries_list=countries_list,
                            total_movies=total
    )


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
            SELECT A.Name, A.ImageFilename
            FROM MovieActors MA
            JOIN Actors A ON MA.ActorID = A.ActorID
            WHERE MA.MovieID = ?
        """, (movie_id,))
        
        actors = [{'Name': row.Name, 'ImageFilename': row.ImageFilename} for row in cursor.fetchall()]

        
    return render_template("movie_detail.html", movie=movie, actors=actors)

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
