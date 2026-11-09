CREATE DATABASE IF NOT EXISTS gm_soft_tasktracker
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE gm_soft_tasktracker;

-- ============================================
-- TABLE : ROLES
-- ============================================

CREATE TABLE IF NOT EXISTS roles (
    id_role INT AUTO_INCREMENT PRIMARY KEY,
    nom_role VARCHAR(30) NOT NULL UNIQUE
);

-- ============================================
-- TABLE : UTILISATEURS
-- ============================================

CREATE TABLE IF NOT EXISTS utilisateurs (
    id_utilisateur INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    mot_de_passe VARCHAR(255) NOT NULL,
    id_role INT NOT NULL,

    CONSTRAINT fk_utilisateur_role
        FOREIGN KEY (id_role)
        REFERENCES roles(id_role)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- ============================================
-- TABLE : PROJETS
-- ============================================

CREATE TABLE IF NOT EXISTS projets (
    id_projet INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(150) NOT NULL,
    description TEXT,
    date_debut DATE NOT NULL,
    date_fin DATE,
    statut VARCHAR(30) NOT NULL DEFAULT 'EN_ATTENTE'
);

-- ============================================
-- TABLE : TACHES
-- ============================================

CREATE TABLE IF NOT EXISTS taches (
    id_tache INT AUTO_INCREMENT PRIMARY KEY,
    titre VARCHAR(150) NOT NULL,
    description TEXT,
    date_debut DATE,
    date_echeance DATE,
    statut VARCHAR(20) NOT NULL DEFAULT 'A_FAIRE',
    id_projet INT NOT NULL,
    id_utilisateur INT NOT NULL,

    CONSTRAINT fk_tache_projet
        FOREIGN KEY (id_projet)
        REFERENCES projets(id_projet)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_tache_utilisateur
        FOREIGN KEY (id_utilisateur)
        REFERENCES utilisateurs(id_utilisateur)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

INSERT INTO roles (nom_role)
VALUES
    ('ADMIN'),
    ('UTILISATEUR');
    
