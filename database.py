
import sqlite3
import hashlib
import random
import string

DATABASE_PATH = "vote_system.db"


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def generer_salt():
    caracteres = string.ascii_letters + string.digits
    salt = ""
    for i in range(64):
        salt = salt + random.choice(caracteres)
    return salt


def init_database():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS electeurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            mot_de_passe TEXT NOT NULL,
            date_inscription TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titre TEXT NOT NULL,
            description TEXT,
            salt TEXT NOT NULL,
            cle_publique_vote TEXT,
            cle_privee_vote TEXT,
            statut TEXT DEFAULT 'en_attente',
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vote_id INTEGER NOT NULL,
            libelle TEXT NOT NULL,
            description TEXT,
            photo TEXT,
            date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vote_id) REFERENCES votes(id)
        )
    """)
    

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jetons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vote_id INTEGER NOT NULL,
            jeton_hash TEXT NOT NULL UNIQUE,
            utilise INTEGER DEFAULT 0,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vote_id) REFERENCES votes(id)
        )
    """)
    

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bulletins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vote_id INTEGER NOT NULL,
            bulletin_chiffre TEXT NOT NULL,
            jeton_hash TEXT NOT NULL,
            date_bulletin TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vote_id) REFERENCES votes(id)
        )
    """)
    

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS administrateurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            mot_de_passe TEXT NOT NULL,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resultats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vote_id INTEGER NOT NULL,
            option_id INTEGER NOT NULL,
            nombre_bulletins INTEGER DEFAULT 0,
            date_decompte TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vote_id) REFERENCES votes(id),
            FOREIGN KEY (option_id) REFERENCES options(id)
        )
    """)
    

    cursor.execute("SELECT COUNT(*) FROM administrateurs")
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.execute(
            "INSERT INTO administrateurs (username, mot_de_passe) VALUES (?, ?)",
            ("admin", hash_password("admin123"))
        )
    
    conn.commit()
    conn.close()
    print("Base de donnees initialisee avec succes.")



def ajouter_electeur(nom, prenom, email, mot_de_passe):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO electeurs (nom, prenom, email, mot_de_passe) VALUES (?, ?, ?, ?)",
            (nom, prenom, email, hash_password(mot_de_passe))
        )
        conn.commit()
        electeur_id = cursor.lastrowid
        conn.close()
        return {"success": True, "id": electeur_id}
    except sqlite3.IntegrityError:
        conn.close()
        return {"success": False, "error": "Cet email existe deja"}


def authentifier_electeur(email, mot_de_passe):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nom, prenom, email, date_inscription FROM electeurs WHERE email = ? AND mot_de_passe = ?",
        (email, hash_password(mot_de_passe))
    )
    row = cursor.fetchone()
    conn.close()
    
    if row:
        electeur = {
            "id": row[0],
            "nom": row[1],
            "prenom": row[2],
            "email": row[3],
            "date_inscription": row[4]
        }
        return {"success": True, "electeur": electeur}
    else:
        return {"success": False, "error": "Email ou mot de passe incorrect"}


def get_electeur(electeur_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nom, prenom, email, date_inscription FROM electeurs WHERE id = ?", (electeur_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row[0],
            "nom": row[1],
            "prenom": row[2],
            "email": row[3],
            "date_inscription": row[4]
        }
    else:
        return None


def get_all_electeurs():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nom, prenom, email, date_inscription FROM electeurs")
    rows = cursor.fetchall()
    conn.close()
    
    electeurs = []
    for row in rows:
        electeur = {
            "id": row[0],
            "nom": row[1],
            "prenom": row[2],
            "email": row[3],
            "date_inscription": row[4]
        }
        electeurs.append(electeur)
    return electeurs



def ajouter_option(vote_id, libelle, description="", photo=""):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO options (vote_id, libelle, description, photo) VALUES (?, ?, ?, ?)",
        (vote_id, libelle, description, photo)
    )
    conn.commit()
    option_id = cursor.lastrowid
    conn.close()
    return {"success": True, "id": option_id}


def get_options_by_vote(vote_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, vote_id, libelle, description, photo, date_ajout FROM options WHERE vote_id = ? ORDER BY libelle", (vote_id,))
    rows = cursor.fetchall()
    conn.close()
    
    options = []
    for row in rows:
        option = {
            "id": row[0],
            "vote_id": row[1],
            "libelle": row[2],
            "description": row[3],
            "photo": row[4],
            "date_ajout": row[5]
        }
        options.append(option)
    return options


def get_all_options():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.id, o.vote_id, o.libelle, o.description, o.photo, o.date_ajout, v.titre 
        FROM options o 
        JOIN votes v ON o.vote_id = v.id 
        ORDER BY o.libelle
    """)
    rows = cursor.fetchall()
    conn.close()
    
    options = []
    for row in rows:
        option = {
            "id": row[0],
            "vote_id": row[1],
            "libelle": row[2],
            "description": row[3],
            "photo": row[4],
            "date_ajout": row[5],
            "vote_titre": row[6]
        }
        options.append(option)
    return options


def supprimer_option(option_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM options WHERE id = ?", (option_id,))
    conn.commit()
    conn.close()
    return {"success": True}



def generer_jeton(electeur_id, vote_id, salt):
    data = str(salt) + ":" + str(electeur_id) + ":" + str(vote_id)
    return hashlib.sha256(data.encode()).hexdigest()


def hash_jeton(jeton):
    return hashlib.sha256(jeton.encode()).hexdigest()


def creer_jeton(vote_id, jeton_hash):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO jetons (vote_id, jeton_hash) VALUES (?, ?)", (vote_id, jeton_hash))
        conn.commit()
        conn.close()
        return {"success": True}
    except sqlite3.IntegrityError:
        conn.close()
        return {"success": False, "error": "Jeton deja existant"}


def jeton_existe(jeton_hash):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, vote_id, jeton_hash, utilise, date_creation FROM jetons WHERE jeton_hash = ?", (jeton_hash,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row[0],
            "vote_id": row[1],
            "jeton_hash": row[2],
            "utilise": row[3],
            "date_creation": row[4]
        }
    else:
        return None


def marquer_jeton_utilise(jeton_hash):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE jetons SET utilise = 1 WHERE jeton_hash = ?", (jeton_hash,))
    conn.commit()
    conn.close()



def enregistrer_bulletin(vote_id, bulletin_chiffre, jeton_hash):

    jeton = jeton_existe(jeton_hash)
    if not jeton:
        return {"success": False, "error": "Jeton invalide"}
    

    if jeton["utilise"] == 1:
        return {"success": False, "error": "Vous avez deja vote"}
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
    
        cursor.execute(
            "INSERT INTO bulletins (vote_id, bulletin_chiffre, jeton_hash) VALUES (?, ?, ?)",
            (vote_id, bulletin_chiffre, jeton_hash)
        )
    
        cursor.execute("UPDATE jetons SET utilise = 1 WHERE jeton_hash = ?", (jeton_hash,))
        conn.commit()
        bulletin_id = cursor.lastrowid
        conn.close()
        return {"success": True, "bulletin_id": bulletin_id}
    except Exception as e:
        conn.close()
        return {"success": False, "error": str(e)}


def get_bulletins_by_vote(vote_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, vote_id, bulletin_chiffre, date_bulletin FROM bulletins WHERE vote_id = ? ORDER BY date_bulletin",
        (vote_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    
    bulletins = []
    for row in rows:
        bulletin = {
            "id": row[0],
            "vote_id": row[1],
            "bulletin_chiffre": row[2],
            "date_bulletin": row[3]
        }
        bulletins.append(bulletin)
    return bulletins


def get_all_bulletins():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, vote_id, date_bulletin FROM bulletins ORDER BY date_bulletin")
    rows = cursor.fetchall()
    conn.close()
    
    bulletins = []
    for row in rows:
        bulletin = {
            "id": row[0],
            "vote_id": row[1],
            "date_bulletin": row[2]
        }
        bulletins.append(bulletin)
    return bulletins


def get_nombre_bulletins(vote_id=None):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    if vote_id:
        cursor.execute("SELECT COUNT(*) FROM bulletins WHERE vote_id = ?", (vote_id,))
    else:
        cursor.execute("SELECT COUNT(*) FROM bulletins")
    count = cursor.fetchone()[0]
    conn.close()
    return count



def creer_vote(titre, description, cle_publique="", cle_privee=""):
    salt = generer_salt()
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO votes (titre, description, salt, cle_publique_vote, cle_privee_vote, statut) VALUES (?, ?, ?, ?, ?, 'en_attente')",
        (titre, description, salt, cle_publique, cle_privee)
    )
    conn.commit()
    vote_id = cursor.lastrowid
    conn.close()
    return {"success": True, "id": vote_id}


def get_vote_actif():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, titre, description, salt, cle_publique_vote, cle_privee_vote, statut, date_creation FROM votes WHERE statut = 'active' ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row[0],
            "titre": row[1],
            "description": row[2],
            "salt": row[3],
            "cle_publique_vote": row[4],
            "cle_privee_vote": row[5],
            "statut": row[6],
            "date_creation": row[7]
        }
    else:
        return None


def get_all_votes():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, titre, description, salt, cle_publique_vote, cle_privee_vote, statut, date_creation FROM votes ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    votes = []
    for row in rows:
        vote = {
            "id": row[0],
            "titre": row[1],
            "description": row[2],
            "salt": row[3],
            "cle_publique_vote": row[4],
            "cle_privee_vote": row[5],
            "statut": row[6],
            "date_creation": row[7]
        }
        votes.append(vote)
    return votes


def get_vote(vote_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, titre, description, salt, cle_publique_vote, cle_privee_vote, statut, date_creation FROM votes WHERE id = ?", (vote_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row[0],
            "titre": row[1],
            "description": row[2],
            "salt": row[3],
            "cle_publique_vote": row[4],
            "cle_privee_vote": row[5],
            "statut": row[6],
            "date_creation": row[7]
        }
    else:
        return None


def changer_statut_vote(vote_id, statut):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE votes SET statut = ? WHERE id = ?", (statut, vote_id))
    conn.commit()
    conn.close()
    return {"success": True}



def authentifier_admin(username, mot_de_passe):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, date_creation FROM administrateurs WHERE username = ? AND mot_de_passe = ?",
        (username, hash_password(mot_de_passe))
    )
    row = cursor.fetchone()
    conn.close()
    
    if row:
        admin = {
            "id": row[0],
            "username": row[1],
            "date_creation": row[2]
        }
        return {"success": True, "admin": admin}
    else:
        return {"success": False, "error": "Identifiants incorrects"}



def enregistrer_resultat(vote_id, option_id, nombre_bulletins):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO resultats (vote_id, option_id, nombre_bulletins) VALUES (?, ?, ?)",
        (vote_id, option_id, nombre_bulletins)
    )
    conn.commit()
    conn.close()


def resultats_existent(vote_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM resultats WHERE vote_id = ?", (vote_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0


def vote_en_cours_ou_termine():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM votes WHERE statut IN ('active', 'terminee') LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row is not None


def get_resultats(vote_id=None):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    if vote_id:
        cursor.execute("""
            SELECT r.id, r.vote_id, r.option_id, r.nombre_bulletins, r.date_decompte, o.libelle 
            FROM resultats r 
            JOIN options o ON r.option_id = o.id 
            WHERE r.vote_id = ? 
            ORDER BY r.nombre_bulletins DESC
        """, (vote_id,))
    else:
        cursor.execute("""
            SELECT r.id, r.vote_id, r.option_id, r.nombre_bulletins, r.date_decompte, o.libelle 
            FROM resultats r 
            JOIN options o ON r.option_id = o.id 
            ORDER BY r.nombre_bulletins DESC
        """)
    
    rows = cursor.fetchall()
    conn.close()
    
    resultats = []
    for row in rows:
        resultat = {
            "id": row[0],
            "vote_id": row[1],
            "option_id": row[2],
            "nombre_bulletins": row[3],
            "date_decompte": row[4],
            "libelle": row[5]
        }
        resultats.append(resultat)
    return resultats


def get_statistiques():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    

    cursor.execute("SELECT COUNT(*) FROM electeurs")
    total_electeurs = cursor.fetchone()[0]
    

    cursor.execute("SELECT COUNT(*) FROM jetons")
    jetons_distribues = cursor.fetchone()[0]
    

    cursor.execute("SELECT COUNT(*) FROM jetons WHERE utilise = 1")
    jetons_utilises = cursor.fetchone()[0]
    

    cursor.execute("SELECT COUNT(*) FROM options")
    total_options = cursor.fetchone()[0]
    

    cursor.execute("SELECT COUNT(*) FROM bulletins")
    total_bulletins = cursor.fetchone()[0]
    

    cursor.execute("SELECT COUNT(*) FROM votes")
    total_votes = cursor.fetchone()[0]
    
    conn.close()
    

    if total_electeurs > 0:
        taux_participation = round((jetons_utilises / total_electeurs) * 100, 2)
    else:
        taux_participation = 0
    
    return {
        "total_electeurs": total_electeurs,
        "jetons_distribues": jetons_distribues,
        "jetons_utilises": jetons_utilises,
        "total_options": total_options,
        "total_bulletins": total_bulletins,
        "total_votes": total_votes,
        "taux_participation": taux_participation
    }


if __name__ == "__main__":
    init_database()
