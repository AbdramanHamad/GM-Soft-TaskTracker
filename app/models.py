from app.database import obtenir_connexion


def obtenir_utilisateur_par_email(email):
    connexion = obtenir_connexion()

    if connexion is None:
        return None

    curseur = None

    try:
        curseur = connexion.cursor(dictionary=True)

        requete = """
            SELECT
                u.id_utilisateur,
                u.nom,
                u.prenom,
                u.email,
                u.mot_de_passe,
                r.nom_role
            FROM utilisateurs u
            INNER JOIN roles r
                ON u.id_role = r.id_role
            WHERE u.email = %s
        """

        curseur.execute(requete, (email,))
        utilisateur = curseur.fetchone()

        return utilisateur

    finally:
        if curseur is not None:
            curseur.close()

        connexion.close()