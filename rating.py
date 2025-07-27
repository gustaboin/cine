import requests
import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("YT_API_KEY")
#print ("api_key", API_KEY)

conn_str = os.getenv("conn_str")
conn = pyodbc.connect(conn_str)
#print("connection", conn)
cursor = conn.cursor()

cursor.execute("SELECT MovieID, Title, ReleaseYear FROM Movies WHERE directorID = 83 and ImdbRating is null") #ImdbRating is null and EnglishTitle is not null")
movies = cursor.fetchall()

for movie in movies:
    movie_id, title, year = movie
    url = f"http://www.omdbapi.com/?apikey={API_KEY}&t={title}&y={year}"
    resp = requests.get(url)
    data = resp.json()
    
    if data.get("Response") == "True":
        rating = data.get("imdbRating")
        if rating and rating != "N/A":
            print(f"{title} ({year}) ➜ {rating}")
            cursor.execute("UPDATE Movies SET ImdbRating = ? WHERE MovieID = ?", float(rating), movie_id)
            conn.commit()
        else:
            print(f"{title} ➜ Rating no disponible")
    else:
        print(f"{title} ➜ No encontrado")

conn.close()
