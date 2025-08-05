import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Cargar variables de entorno (asegúrate de que el .env esté cargado al inicio de app.py también)
load_dotenv() 
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "your_mariadb_database")

class MariaDBConnection:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def __enter__(self):
        try:
            self.conn = mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )
            self.conn.autocommit = False # Desactivar autocommit para gestionar transacciones
            self.cursor = self.conn.cursor(dictionary=True) 
            return self.cursor
        except Error as e:
            print(f"Error al conectar a la base de datos MariaDB: {e}")
            raise # Relanza la excepción

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None: # No hubo excepción, commit
            if self.conn:
                self.conn.commit()
        else: # Hubo una excepción, rollback
            if self.conn:
                self.conn.rollback()
        
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        return False # Propaga la excepción si hubo una