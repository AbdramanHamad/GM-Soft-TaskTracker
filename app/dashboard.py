from app.database import obtenir_connexion

from datetime import date


def obtenir_statistiques():
    connexion = obtenir_connexion()

    statistiques = {
        "total_projets": 0,
        "total_taches": 0,
        "taches_terminees": 0,
        "taches_en_cours": 0,
        "taches_en_retard": 0,
        "total_utilisateurs": 0,
        "repartition_statuts": [],
        "taches_par_projet": [],
        "dernieres_taches": []
    }

    if connexion is None:
        return statistiques

    curseur = None

    try:
        curseur = connexion.cursor(dictionary=True)

        # 1. Nombre total de projets
        curseur.execute("""
            SELECT COUNT(*) AS total
            FROM projets
        """)
        statistiques["total_projets"] = curseur.fetchone()["total"]

        # 2. Nombre total de tâches
        curseur.execute("""
            SELECT COUNT(*) AS total
            FROM taches
        """)
        statistiques["total_taches"] = curseur.fetchone()["total"]

        # 3. Nombre de tâches terminées
        curseur.execute("""
            SELECT COUNT(*) AS total
            FROM taches
            WHERE statut = 'TERMINE'
        """)
        statistiques["taches_terminees"] = curseur.fetchone()["total"]

        # 4. Nombre de tâches en cours
        curseur.execute("""
            SELECT COUNT(*) AS total
            FROM taches
            WHERE statut = 'EN_COURS'
        """)
        statistiques["taches_en_cours"] = curseur.fetchone()["total"]

        # 5. Nombre de tâches en retard
        curseur.execute("""
            SELECT COUNT(*) AS total
            FROM taches
            WHERE date_echeance < CURDATE()
              AND statut <> 'TERMINE'
        """)
        statistiques["taches_en_retard"] = curseur.fetchone()["total"]

        # 6. Nombre total d'utilisateurs
        curseur.execute("""
            SELECT COUNT(*) AS total
            FROM utilisateurs
        """)
        statistiques["total_utilisateurs"] = curseur.fetchone()["total"]

        # 7. Répartition des tâches par statut
        curseur.execute("""
            SELECT statut, COUNT(*) AS total
            FROM taches
            GROUP BY statut
            ORDER BY total DESC
        """)
        statistiques["repartition_statuts"] = curseur.fetchall()

        # 8. Nombre de tâches par projet
        curseur.execute("""
            SELECT p.id_projet,
                   p.nom AS nom_projet,
                   COUNT(t.id_tache) AS total_taches
            FROM projets p
            LEFT JOIN taches t ON t.id_projet = p.id_projet
            GROUP BY p.id_projet, p.nom
            ORDER BY total_taches DESC, p.nom ASC
            LIMIT 10
        """)
        statistiques["taches_par_projet"] = curseur.fetchall()

        # 9. Dernières tâches enregistrées
        curseur.execute("""
            SELECT t.id_tache,
                   t.titre,
                   t.statut,
                   t.date_echeance,
                   p.nom AS nom_projet
            FROM taches t
            LEFT JOIN projets p ON p.id_projet = t.id_projet
            ORDER BY t.id_tache DESC
            LIMIT 5
        """)
        statistiques["dernieres_taches"] = curseur.fetchall()

    finally:
        if curseur is not None:
            curseur.close()

        connexion.close()

    return statistiques
