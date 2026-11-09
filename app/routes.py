from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from werkzeug.security import check_password_hash
from app.models import obtenir_utilisateur_par_email
from app.dashboard import obtenir_statistiques
from app.database import obtenir_connexion

main = Blueprint("main", __name__)


# =====================================================
# ACCUEIL
# =====================================================

@main.route("/")
def accueil():
    return redirect(url_for("main.connexion"))


# =====================================================
# CONNEXION
# =====================================================

@main.route("/connexion", methods=["GET", "POST"])
def connexion():

    if "id_utilisateur" in session:
        return redirect(url_for("main.tableau_de_bord"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        mot_de_passe = request.form.get("mot_de_passe", "")

        utilisateur = obtenir_utilisateur_par_email(email)

        if utilisateur and check_password_hash(
            utilisateur["mot_de_passe"],
            mot_de_passe
        ):
            session["id_utilisateur"] = utilisateur["id_utilisateur"]
            session["nom"] = utilisateur["nom"]
            session["prenom"] = utilisateur["prenom"]
            session["email"] = utilisateur["email"]
            session["role"] = utilisateur["nom_role"]

            return redirect(url_for("main.tableau_de_bord"))

        flash("Adresse e-mail ou mot de passe incorrect.")

    return render_template("connexion.html")


# =====================================================
# TABLEAU DE BORD
# =====================================================

@main.route("/tableau-de-bord")
def tableau_de_bord():

    if "id_utilisateur" not in session:
        return redirect(url_for("main.connexion"))

    statistiques = obtenir_statistiques()

    return render_template(
        "tableau_de_bord.html",
        statistiques=statistiques
    )


# =====================================================
# LISTE DES PROJETS
# =====================================================

@main.route("/projets")
def projets():

    if "id_utilisateur" not in session:
        return redirect(url_for("main.connexion"))

    connexion = obtenir_connexion()

    if connexion is None:
        flash("Impossible de se connecter à la base de données.", "danger")
        return render_template("projets.html", projets=[])

    curseur = None
    try:
        curseur = connexion.cursor(dictionary=True)

        curseur.execute("""
            SELECT
                id_projet,
                nom,
                description,
                date_debut,
                date_fin,
                statut
            FROM projets
            ORDER BY id_projet DESC
        """)

        liste_projets = curseur.fetchall()

        return render_template(
            "projets.html",
            projets=liste_projets
        )

    except Exception:
        flash("Erreur lors du chargement des projets.", "danger")
        return render_template("projets.html", projets=[])

    finally:
        try:
            if curseur is not None:
                curseur.close()
        finally:
            connexion.close()


# =====================================================
# AJOUTER UN PROJET
# =====================================================

@main.route("/projets/ajouter", methods=["GET", "POST"])
def ajouter_projet():

    if "id_utilisateur" not in session:
        return redirect(url_for("main.connexion"))

    if session.get("role") != "ADMIN":
        flash("Vous n'avez pas l'autorisation de créer un projet.", "danger")
        return redirect(url_for("main.projets"))

    if request.method == "POST":
        nom = request.form.get("nom", "").strip()
        description = request.form.get("description", "").strip()
        date_debut = request.form.get("date_debut", "")
        date_fin = request.form.get("date_fin", "") or None
        statut = request.form.get("statut", "EN_ATTENTE")

        statuts_autorises = {"EN_ATTENTE", "EN_COURS", "TERMINE"}

        if not nom or not date_debut:
            flash("Le nom et la date de début sont obligatoires.", "danger")
            return redirect(url_for("main.ajouter_projet"))

        if statut not in statuts_autorises:
            flash("Le statut sélectionné est invalide.", "danger")
            return redirect(url_for("main.ajouter_projet"))

        if date_fin and date_fin < date_debut:
            flash("La date de fin ne peut pas précéder la date de début.", "danger")
            return redirect(url_for("main.ajouter_projet"))

        connexion = obtenir_connexion()

        if connexion is None:
            flash("Impossible de se connecter à la base de données.", "danger")
            return redirect(url_for("main.ajouter_projet"))

        curseur = None
        try:
            curseur = connexion.cursor()

            curseur.execute("""
                INSERT INTO projets
                    (nom, description, date_debut, date_fin, statut)
                VALUES (%s, %s, %s, %s, %s)
            """, (nom, description or None, date_debut, date_fin, statut))

            connexion.commit()

            flash("Projet créé avec succès.", "success")
            return redirect(url_for("main.projets"))

        except Exception:
            connexion.rollback()
            flash("Une erreur est survenue lors de la création du projet.", "danger")
            return redirect(url_for("main.ajouter_projet"))

        finally:
            try:
                if curseur is not None:
                    curseur.close()
            finally:
                connexion.close()

    return render_template("ajouter_projet.html")




# GESTION DES TÂCHES
@main.route("/taches")
def taches():
    if "id_utilisateur" not in session:
        return redirect(url_for("main.connexion"))

    connexion = obtenir_connexion()

    if connexion is None:
        flash("Impossible de se connecter à la base de données.", "danger")
        return render_template(
            "taches.html",
            taches=[],
            projets=[],
            utilisateurs=[]
        )

    curseur = None
    try:
        curseur = connexion.cursor(dictionary=True)

        # Récupérer toutes les tâches
        curseur.execute("""
            SELECT
                t.id_tache,
                t.titre,
                t.description,
                t.date_debut,
                t.date_echeance,
                t.statut,
                t.id_projet,
                t.id_utilisateur,
                p.nom AS nom_projet,
                CONCAT(u.prenom, ' ', u.nom) AS nom_utilisateur
            FROM taches t
            INNER JOIN projets p
                ON t.id_projet = p.id_projet
            INNER JOIN utilisateurs u
                ON t.id_utilisateur = u.id_utilisateur
            ORDER BY t.id_tache DESC
        """)
        liste_taches = curseur.fetchall()

        # Récupérer les projets disponibles
        curseur.execute("""
            SELECT id_projet, nom
            FROM projets
            ORDER BY nom
        """)
        liste_projets = curseur.fetchall()

        # Récupérer les utilisateurs disponibles
        curseur.execute("""
            SELECT id_utilisateur, nom, prenom
            FROM utilisateurs
            ORDER BY nom, prenom
        """)
        liste_utilisateurs = curseur.fetchall()

        return render_template(
            "taches.html",
            taches=liste_taches,
            projets=liste_projets,
            utilisateurs=liste_utilisateurs
        )

    except Exception as erreur:
        print(f"Erreur lors du chargement des tâches : {erreur}")
        flash("Erreur lors du chargement des tâches.", "danger")

        return render_template(
            "taches.html",
            taches=[],
            projets=[],
            utilisateurs=[]
        )

    finally:
        try:
            if curseur is not None:
                curseur.close()
        finally:
            connexion.close()


# AJOUTER UNE TÂCHE
@main.route("/taches/ajouter", methods=["POST"])
def ajouter_tache():
    if "id_utilisateur" not in session:
        return redirect(url_for("main.connexion"))

    if session.get("role") != "ADMIN":
        flash("Vous n'avez pas l'autorisation de créer une tâche.", "danger")
        return redirect(url_for("main.taches"))

    titre = request.form.get("titre", "").strip()
    description = request.form.get("description", "").strip()
    id_projet = request.form.get("id_projet", "")
    id_utilisateur = request.form.get("id_utilisateur", "")
    date_debut = request.form.get("date_debut", "") or None
    date_echeance = request.form.get("date_echeance", "") or None
    statut = request.form.get("statut", "A_FAIRE")

    statuts_autorises = {"A_FAIRE", "EN_COURS", "TERMINE"}

    # Vérifier les champs obligatoires
    if not titre or not id_projet or not id_utilisateur:
        flash("Veuillez remplir tous les champs obligatoires.", "danger")
        return redirect(url_for("main.taches"))

    # Vérifier le statut
    if statut not in statuts_autorises:
        flash("Le statut sélectionné est invalide.", "danger")
        return redirect(url_for("main.taches"))

    # Vérifier la cohérence des dates
    if date_debut and date_echeance and date_echeance < date_debut:
        flash("La date d'échéance ne peut pas précéder la date de début.", "danger")
        return redirect(url_for("main.taches"))

    try:
        id_projet = int(id_projet)
        id_utilisateur = int(id_utilisateur)
    except (ValueError, TypeError):
        flash("Le projet ou l'utilisateur sélectionné est invalide.", "danger")
        return redirect(url_for("main.taches"))

    connexion = obtenir_connexion()

    if connexion is None:
        flash("Impossible de se connecter à la base de données.", "danger")
        return redirect(url_for("main.taches"))

    curseur = None
    try:
        curseur = connexion.cursor()

        # Vérifier que le projet existe
        curseur.execute(
            "SELECT id_projet FROM projets WHERE id_projet = %s",
            (id_projet,)
        )

        if curseur.fetchone() is None:
            flash("Le projet sélectionné n'existe pas.", "danger")
            return redirect(url_for("main.taches"))

        # Vérifier que l'utilisateur existe
        curseur.execute(
            "SELECT id_utilisateur FROM utilisateurs WHERE id_utilisateur = %s",
            (id_utilisateur,)
        )

        if curseur.fetchone() is None:
            flash("L'utilisateur sélectionné n'existe pas.", "danger")
            return redirect(url_for("main.taches"))

        # Enregistrer la tâche
        curseur.execute("""
            INSERT INTO taches (
                titre,
                description,
                date_debut,
                date_echeance,
                statut,
                id_projet,
                id_utilisateur
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            titre,
            description or None,
            date_debut,
            date_echeance,
            statut,
            id_projet,
            id_utilisateur
        ))

        connexion.commit()

        flash("La tâche a été créée avec succès.", "success")

    except Exception as erreur:
        connexion.rollback()
        print(f"Erreur lors de la création de la tâche : {erreur}")
        flash("Une erreur est survenue lors de la création de la tâche.", "danger")

    finally:
        try:
            if curseur is not None:
                curseur.close()
        finally:
            connexion.close()

    return redirect(url_for("main.taches"))
# MODIFIER UNE TÂCHE
@main.route("/taches/modifier/<int:id_tache>", methods=["POST"])
def modifier_tache(id_tache):
    if "id_utilisateur" not in session:
        return redirect(url_for("main.connexion"))

    if session.get("role") != "ADMIN":
        flash("Vous n'avez pas l'autorisation de modifier une tâche.", "danger")
        return redirect(url_for("main.taches"))

    titre = request.form.get("titre", "").strip()
    description = request.form.get("description", "").strip()
    id_projet = request.form.get("id_projet", "")
    id_utilisateur = request.form.get("id_utilisateur", "")
    date_debut = request.form.get("date_debut", "") or None
    date_echeance = request.form.get("date_echeance", "") or None
    statut = request.form.get("statut", "A_FAIRE")

    statuts_autorises = {"A_FAIRE", "EN_COURS", "TERMINE"}

    if not titre or not id_projet or not id_utilisateur:
        flash("Le titre, le projet et le responsable sont obligatoires.", "danger")
        return redirect(url_for("main.taches"))

    if statut not in statuts_autorises:
        flash("Le statut sélectionné est invalide.", "danger")
        return redirect(url_for("main.taches"))

    if date_debut and date_echeance and date_echeance < date_debut:
        flash("La date d'échéance ne peut pas précéder la date de début.", "danger")
        return redirect(url_for("main.taches"))

    try:
        id_projet = int(id_projet)
        id_utilisateur = int(id_utilisateur)
    except (ValueError, TypeError):
        flash("Le projet ou le responsable sélectionné est invalide.", "danger")
        return redirect(url_for("main.taches"))

    connexion = obtenir_connexion()

    if connexion is None:
        flash("Impossible de se connecter à la base de données.", "danger")
        return redirect(url_for("main.taches"))

    curseur = None
    try:
        curseur = connexion.cursor()

        curseur.execute(
            "SELECT id_tache FROM taches WHERE id_tache = %s",
            (id_tache,)
        )
        if curseur.fetchone() is None:
            flash("La tâche demandée n'existe pas.", "danger")
            return redirect(url_for("main.taches"))

        curseur.execute(
            "SELECT id_projet FROM projets WHERE id_projet = %s",
            (id_projet,)
        )
        if curseur.fetchone() is None:
            flash("Le projet sélectionné n'existe pas.", "danger")
            return redirect(url_for("main.taches"))

        curseur.execute(
            "SELECT id_utilisateur FROM utilisateurs WHERE id_utilisateur = %s",
            (id_utilisateur,)
        )
        if curseur.fetchone() is None:
            flash("L'utilisateur sélectionné n'existe pas.", "danger")
            return redirect(url_for("main.taches"))

        curseur.execute("""
            UPDATE taches
            SET titre = %s,
                description = %s,
                date_debut = %s,
                date_echeance = %s,
                statut = %s,
                id_projet = %s,
                id_utilisateur = %s
            WHERE id_tache = %s
        """, (
            titre,
            description or None,
            date_debut,
            date_echeance,
            statut,
            id_projet,
            id_utilisateur,
            id_tache
        ))

        connexion.commit()
        flash("La tâche a été modifiée avec succès.", "success")

    except Exception as erreur:
        connexion.rollback()
        print(f"Erreur lors de la modification de la tâche : {erreur}")
        flash("Une erreur est survenue lors de la modification.", "danger")

    finally:
        try:
            if curseur is not None:
                curseur.close()
        finally:
            connexion.close()

    return redirect(url_for("main.taches"))

# SUPPRIMER UNE TÂCHE
@main.route("/taches/supprimer/<int:id_tache>", methods=["POST"])
def supprimer_tache(id_tache):
    if "id_utilisateur" not in session:
        return redirect(url_for("main.connexion"))

    if session.get("role") != "ADMIN":
        flash("Vous n'avez pas l'autorisation de supprimer une tâche.", "danger")
        return redirect(url_for("main.taches"))

    connexion = obtenir_connexion()

    if connexion is None:
        flash("Impossible de se connecter à la base de données.", "danger")
        return redirect(url_for("main.taches"))

    curseur = None
    try:
        curseur = connexion.cursor()

        # Vérifier que la tâche existe
        curseur.execute(
            "SELECT id_tache FROM taches WHERE id_tache = %s",
            (id_tache,)
        )

        if curseur.fetchone() is None:
            flash("La tâche demandée n'existe pas.", "warning")
            return redirect(url_for("main.taches"))

        # Supprimer la tâche
        curseur.execute(
            "DELETE FROM taches WHERE id_tache = %s",
            (id_tache,)
        )

        connexion.commit()
        flash("La tâche a été supprimée avec succès.", "success")

    except Exception as erreur:
        connexion.rollback()
        print(f"Erreur lors de la suppression de la tâche : {erreur}")
        flash("Impossible de supprimer cette tâche.", "danger")

    finally:
        try:
            if curseur is not None:
                curseur.close()
        finally:
            connexion.close()

    return redirect(url_for("main.taches"))

# GESTION DES UTILISATEURS
@main.route("/utilisateurs")
def utilisateurs():
    # Vérifier la connexion
    if "id_utilisateur" not in session:
        return redirect(url_for("main.connexion"))

    # Réserver cette page aux administrateurs
    if session.get("role") != "ADMIN":
        flash(
            "Accès réservé aux administrateurs.",
            "danger"
        )
        return redirect(url_for("main.tableau_de_bord"))

    connexion = obtenir_connexion()

    if connexion is None:
        flash(
            "Impossible de se connecter à la base de données.",
            "danger"
        )
        return render_template(
            "utilisateurs.html",
            utilisateurs=[]
        )

    curseur = None
    try:
        curseur = connexion.cursor(dictionary=True)

        curseur.execute("""
            SELECT
                u.id_utilisateur,
                u.nom,
                u.prenom,
                u.email,
                r.nom_role
            FROM utilisateurs u
            INNER JOIN roles r
                ON u.id_role = r.id_role
            ORDER BY u.id_utilisateur DESC
        """)

        liste_utilisateurs = curseur.fetchall()

        return render_template(
            "utilisateurs.html",
            utilisateurs=liste_utilisateurs
        )

    except Exception as erreur:
        print(
            f"Erreur lors du chargement des utilisateurs : {erreur}"
        )

        flash(
            "Une erreur est survenue lors du chargement des utilisateurs.",
            "danger"
        )

        return render_template(
            "utilisateurs.html",
            utilisateurs=[]
        )

    finally:
        try:
            if curseur is not None:
                curseur.close()
        finally:
            connexion.close()

# AJOUTER UN UTILISATEUR
@main.route("/utilisateurs/ajouter", methods=["POST"])
def ajouter_utilisateur():
    if "id_utilisateur" not in session:
        return redirect(url_for("main.connexion"))

    if session.get("role") != "ADMIN":
        flash("Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("main.tableau_de_bord"))

    nom = request.form.get("nom", "").strip()
    prenom = request.form.get("prenom", "").strip()
    email = request.form.get("email", "").strip().lower()
    mot_de_passe = request.form.get("mot_de_passe", "")
    id_role = request.form.get("id_role", "")

    # Vérifier les champs obligatoires
    if not nom or not prenom or not email or not mot_de_passe or not id_role:
        flash("Veuillez remplir tous les champs obligatoires.", "danger")
        return redirect(url_for("main.utilisateurs"))

    # Vérifier la longueur du mot de passe
    if len(mot_de_passe) < 8:
        flash("Le mot de passe doit contenir au moins 8 caractères.", "danger")
        return redirect(url_for("main.utilisateurs"))

    # Vérifier l'identifiant du rôle
    try:
        id_role = int(id_role)
    except (ValueError, TypeError):
        flash("Le rôle sélectionné est invalide.", "danger")
        return redirect(url_for("main.utilisateurs"))

    connexion = obtenir_connexion()

    if connexion is None:
        flash("Impossible de se connecter à la base de données.", "danger")
        return redirect(url_for("main.utilisateurs"))

    curseur = None
    try:
        curseur = connexion.cursor(dictionary=True)

        # Vérifier que le rôle existe
        curseur.execute(
            "SELECT id_role FROM roles WHERE id_role = %s",
            (id_role,)
        )

        if curseur.fetchone() is None:
            flash("Le rôle sélectionné n'existe pas.", "danger")
            return redirect(url_for("main.utilisateurs"))

        # Vérifier si l'adresse e-mail est déjà utilisée
        curseur.execute(
            "SELECT id_utilisateur FROM utilisateurs WHERE email = %s",
            (email,)
        )

        if curseur.fetchone():
            flash("Cette adresse e-mail est déjà utilisée.", "danger")
            return redirect(url_for("main.utilisateurs"))

        # Hacher le mot de passe
        from werkzeug.security import generate_password_hash
        mot_de_passe_hache = generate_password_hash(mot_de_passe)

        # Enregistrer le nouvel utilisateur
        curseur.execute("""
            INSERT INTO utilisateurs (
                nom,
                prenom,
                email,
                mot_de_passe,
                id_role
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (
            nom,
            prenom,
            email,
            mot_de_passe_hache,
            id_role
        ))

        connexion.commit()
        flash("Le compte utilisateur a été créé avec succès.", "success")

    except Exception as erreur:
        connexion.rollback()
        print(f"Erreur lors de la création de l'utilisateur : {erreur}")
        flash("Une erreur est survenue lors de la création du compte.", "danger")

    finally:
        try:
            if curseur is not None:
                curseur.close()
        finally:
            connexion.close()

    return redirect(url_for("main.utilisateurs"))


# MODIFIER UN UTILISATEUR
@main.route("/utilisateurs/modifier/<int:id_utilisateur>", methods=["POST"])
def modifier_utilisateur(id_utilisateur):
    if "id_utilisateur" not in session:
        return redirect(url_for("main.connexion"))

    if session.get("role") != "ADMIN":
        flash("Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("main.tableau_de_bord"))

    nom = request.form.get("nom", "").strip()
    prenom = request.form.get("prenom", "").strip()
    email = request.form.get("email", "").strip().lower()
    id_role = request.form.get("id_role", "")
    nouveau_mot_de_passe = request.form.get("nouveau_mot_de_passe", "")

    if not nom or not prenom or not email or not id_role:
        flash("Veuillez remplir tous les champs obligatoires.", "danger")
        return redirect(url_for("main.utilisateurs"))

    if nouveau_mot_de_passe and len(nouveau_mot_de_passe) < 8:
        flash("Le nouveau mot de passe doit contenir au moins 8 caractères.", "danger")
        return redirect(url_for("main.utilisateurs"))

    try:
        id_role = int(id_role)
    except (ValueError, TypeError):
        flash("Le rôle sélectionné est invalide.", "danger")
        return redirect(url_for("main.utilisateurs"))

    connexion = obtenir_connexion()

    if connexion is None:
        flash("Impossible de se connecter à la base de données.", "danger")
        return redirect(url_for("main.utilisateurs"))

    curseur = None
    try:
        curseur = connexion.cursor(dictionary=True)

        # Vérifier que l'utilisateur existe
        curseur.execute(
            "SELECT id_utilisateur FROM utilisateurs WHERE id_utilisateur = %s",
            (id_utilisateur,)
        )

        if curseur.fetchone() is None:
            flash("L'utilisateur demandé n'existe pas.", "danger")
            return redirect(url_for("main.utilisateurs"))

        # Vérifier que le rôle existe
        curseur.execute(
            "SELECT id_role, nom_role FROM roles WHERE id_role = %s",
            (id_role,)
        )
        role_selectionne = curseur.fetchone()

        if role_selectionne is None:
            flash("Le rôle sélectionné n'existe pas.", "danger")
            return redirect(url_for("main.utilisateurs"))

        # Vérifier que l'adresse e-mail n'appartient pas à un autre compte
        curseur.execute("""
            SELECT id_utilisateur
            FROM utilisateurs
            WHERE email = %s AND id_utilisateur != %s
        """, (email, id_utilisateur))

        if curseur.fetchone():
            flash("Cette adresse e-mail est déjà utilisée.", "danger")
            return redirect(url_for("main.utilisateurs"))

        # Mettre à jour les informations du compte
        if nouveau_mot_de_passe:
            from werkzeug.security import generate_password_hash

            mot_de_passe_hache = generate_password_hash(nouveau_mot_de_passe)

            curseur.execute("""
                UPDATE utilisateurs
                SET nom = %s,
                    prenom = %s,
                    email = %s,
                    id_role = %s,
                    mot_de_passe = %s
                WHERE id_utilisateur = %s
            """, (
                nom,
                prenom,
                email,
                id_role,
                mot_de_passe_hache,
                id_utilisateur
            ))

        else:
            curseur.execute("""
                UPDATE utilisateurs
                SET nom = %s,
                    prenom = %s,
                    email = %s,
                    id_role = %s
                WHERE id_utilisateur = %s
            """, (
                nom,
                prenom,
                email,
                id_role,
                id_utilisateur
            ))

        connexion.commit()

        # Actualiser la session si l'administrateur modifie son propre compte
        if session.get("id_utilisateur") == id_utilisateur:
            session["nom"] = nom
            session["prenom"] = prenom
            session["email"] = email
            session["role"] = role_selectionne["nom_role"]

            # Si son rôle devient UTILISATEUR, il perd immédiatement
            # l'accès aux fonctions réservées aux administrateurs.
            if session["role"] != "ADMIN":
                flash("Votre compte a été modifié. Votre rôle administrateur a été retiré.", "warning")
                return redirect(url_for("main.tableau_de_bord"))

        flash("L'utilisateur a été modifié avec succès.", "success")

    except Exception as erreur:
        connexion.rollback()
        print(f"Erreur lors de la modification de l'utilisateur : {erreur}")
        flash("Une erreur est survenue lors de la modification.", "danger")

    finally:
        try:
            if curseur is not None:
                curseur.close()
        finally:
            connexion.close()

    return redirect(url_for("main.utilisateurs"))
# SUPPRIMER UN UTILISATEUR
@main.route("/utilisateurs/supprimer/<int:id_utilisateur>", methods=["POST"])
def supprimer_utilisateur(id_utilisateur):
    # Vérifier la connexion
    if "id_utilisateur" not in session:
        return redirect(url_for("main.connexion"))

    # Réserver cette action aux administrateurs
    if session.get("role") != "ADMIN":
        flash("Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("main.tableau_de_bord"))

    # Empêcher la suppression de son propre compte
    if session.get("id_utilisateur") == id_utilisateur:
        flash("Vous ne pouvez pas supprimer votre propre compte.", "danger")
        return redirect(url_for("main.utilisateurs"))

    connexion = obtenir_connexion()

    if connexion is None:
        flash("Impossible de se connecter à la base de données.", "danger")
        return redirect(url_for("main.utilisateurs"))

    curseur = None
    try:
        curseur = connexion.cursor()

        # Vérifier que l'utilisateur existe
        curseur.execute(
            "SELECT id_utilisateur FROM utilisateurs WHERE id_utilisateur = %s",
            (id_utilisateur,)
        )

        if curseur.fetchone() is None:
            flash("L'utilisateur demandé n'existe pas.", "warning")
            return redirect(url_for("main.utilisateurs"))

        # Vérifier si l'utilisateur possède encore des tâches
        curseur.execute(
            "SELECT COUNT(*) FROM taches WHERE id_utilisateur = %s",
            (id_utilisateur,)
        )

        nombre_taches = curseur.fetchone()[0]

        if nombre_taches > 0:
            flash(
                "Impossible de supprimer cet utilisateur : "
                "réattribuez d'abord ses tâches.",
                "danger"
            )
            return redirect(url_for("main.utilisateurs"))

        # Supprimer l'utilisateur
        curseur.execute(
            "DELETE FROM utilisateurs WHERE id_utilisateur = %s",
            (id_utilisateur,)
        )

        connexion.commit()

        flash("L'utilisateur a été supprimé avec succès.", "success")

    except Exception as erreur:
        connexion.rollback()
        print(f"Erreur lors de la suppression de l'utilisateur : {erreur}")
        flash(
            "Une erreur est survenue lors de la suppression du compte.",
            "danger"
        )

    finally:
        try:
            if curseur is not None:
                curseur.close()
        finally:
            connexion.close()

    return redirect(url_for("main.utilisateurs"))
# =====================================================
# DÉCONNEXION
# =====================================================

@main.route("/deconnexion")
def deconnexion():
    session.clear()
    return redirect(url_for("main.connexion"))
