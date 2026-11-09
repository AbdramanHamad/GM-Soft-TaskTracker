import mysql.connector
from mysql.connector import Error

from config import Config


def obtenir_connexion():
    try:
        connexion = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            database=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )

        return connexion

    except Error as erreur:
        print(f"Erreur de connexion MySQL : {erreur}")
        return None