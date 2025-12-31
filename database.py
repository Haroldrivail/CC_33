# database.py
import sqlite3
import hashlib
from contextlib import contextmanager

DATABASE_PATH = "vote_system.db"


# Helpers
@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def query(sql, params=(), one=False):
    with get_db() as conn:
        rows = conn.execute(sql, params).fetchall()
        if one:
            return dict(rows[0]) if rows else None
        return [dict(r) for r in rows]


def execute(sql, params=()):
    with get_db() as conn:
        cursor = conn.execute(sql, params)
        return cursor.lastrowid


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# Initialisation
TABLES_SQL = """
CREATE TABLE IF NOT EXISTS electeurs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL, prenom TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
    mot_de_passe TEXT NOT NULL,
    date_inscription TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titre TEXT NOT NULL, description TEXT,
    salt TEXT NOT NULL,
    cle_publique_vote TEXT, cle_privee_vote TEXT,
    statut TEXT DEFAULT 'en_attente', date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vote_id INTEGER NOT NULL,
    libelle TEXT NOT NULL, description TEXT, photo TEXT,
    date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vote_id) REFERENCES votes(id)
);
CREATE TABLE IF NOT EXISTS jetons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vote_id INTEGER NOT NULL,
    jeton_hash TEXT NOT NULL UNIQUE,
    utilise INTEGER DEFAULT 0,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vote_id) REFERENCES votes(id)
);
CREATE TABLE IF NOT EXISTS bulletins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vote_id INTEGER NOT NULL,
    bulletin_chiffre TEXT NOT NULL,
    jeton_hash TEXT NOT NULL,
    date_bulletin TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vote_id) REFERENCES votes(id)
);
CREATE TABLE IF NOT EXISTS administrateurs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL, mot_de_passe TEXT NOT NULL,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS resultats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vote_id INTEGER NOT NULL, option_id INTEGER NOT NULL, nombre_bulletins INTEGER DEFAULT 0,
    date_decompte TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vote_id) REFERENCES votes(id),
    FOREIGN KEY (option_id) REFERENCES options(id)
);
"""

def init_database():
    with get_db() as conn:
        conn.executescript(TABLES_SQL)
        if conn.execute("SELECT COUNT(*) FROM administrateurs").fetchone()[0] == 0:
            conn.execute("INSERT INTO administrateurs (username, mot_de_passe) VALUES (?, ?)",
                        ("admin", hash_password("admin123")))
    print("Base de données initialisée avec succès.")


# Electeurs
def ajouter_electeur(nom, prenom, email, mot_de_passe):
    try:
        id = execute("INSERT INTO electeurs (nom, prenom, email, mot_de_passe) VALUES (?, ?, ?, ?)",
                     (nom, prenom, email, hash_password(mot_de_passe)))
        return {"success": True, "id": id}
    except sqlite3.IntegrityError:
        return {"success": False, "error": "Cet email existe déjà"}

def authentifier_electeur(email, mot_de_passe):
    electeur = query("SELECT * FROM electeurs WHERE email = ? AND mot_de_passe = ?",
                     (email, hash_password(mot_de_passe)), one=True)
    if electeur:
        return {"success": True, "electeur": electeur}
    return {"success": False, "error": "Email ou mot de passe incorrect"}

def get_electeur(electeur_id):
    return query("SELECT * FROM electeurs WHERE id = ?", (electeur_id,), one=True)

def get_all_electeurs():
    return query("SELECT id, nom, prenom, email, date_inscription FROM electeurs")


# Options
def ajouter_option(vote_id, libelle, description="", photo=""):
    id = execute("INSERT INTO options (vote_id, libelle, description, photo) VALUES (?, ?, ?, ?)",
                 (vote_id, libelle, description, photo))
    return {"success": True, "id": id}

def get_options_by_vote(vote_id):
    return query("SELECT * FROM options WHERE vote_id = ? ORDER BY libelle", (vote_id,))

def get_all_options():
    return query("SELECT o.*, v.titre as vote_titre FROM options o JOIN votes v ON o.vote_id = v.id ORDER BY o.libelle")

def supprimer_option(option_id):
    execute("DELETE FROM options WHERE id = ?", (option_id,))
    return {"success": True}


# Jetons (anonymat)
def generer_jeton(electeur_id, vote_id, salt):
    data = f"{salt}:{electeur_id}:{vote_id}"
    return hashlib.sha256(data.encode()).hexdigest()

def hash_jeton(jeton):
    return hashlib.sha256(jeton.encode()).hexdigest()

def creer_jeton(vote_id, jeton_hash):
    try:
        execute("INSERT INTO jetons (vote_id, jeton_hash) VALUES (?, ?)", (vote_id, jeton_hash))
        return {"success": True}
    except sqlite3.IntegrityError:
        return {"success": False, "error": "Jeton déjà existant"}

def jeton_existe(jeton_hash):
    return query("SELECT * FROM jetons WHERE jeton_hash = ?", (jeton_hash,), one=True)

def marquer_jeton_utilise(jeton_hash):
    execute("UPDATE jetons SET utilise = 1 WHERE jeton_hash = ?", (jeton_hash,))


# Bulletins (anonymes)
def enregistrer_bulletin(vote_id, bulletin_chiffre, jeton_hash):
    jeton = jeton_existe(jeton_hash)
    if not jeton:
        return {"success": False, "error": "Jeton invalide"}
    if jeton['utilise']:
        return {"success": False, "error": "Vous avez déjà voté"}
    try:
        with get_db() as conn:
            conn.execute("INSERT INTO bulletins (vote_id, bulletin_chiffre, jeton_hash) VALUES (?, ?, ?)",
                        (vote_id, bulletin_chiffre, jeton_hash))
            conn.execute("UPDATE jetons SET utilise = 1 WHERE jeton_hash = ?", (jeton_hash,))
            return {"success": True, "bulletin_id": conn.execute("SELECT last_insert_rowid()").fetchone()[0]}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_bulletins_by_vote(vote_id):
    return query("SELECT id, vote_id, bulletin_chiffre, date_bulletin FROM bulletins WHERE vote_id = ? ORDER BY date_bulletin", (vote_id,))

def get_all_bulletins():
    return query("SELECT id, vote_id, date_bulletin FROM bulletins ORDER BY date_bulletin")

def get_nombre_bulletins(vote_id=None):
    if vote_id:
        return query("SELECT COUNT(*) as total FROM bulletins WHERE vote_id = ?", (vote_id,), one=True)['total']
    return query("SELECT COUNT(*) as total FROM bulletins", one=True)['total']


# Votes (campagnes)
def generer_salt():
    import secrets
    return secrets.token_hex(32)

def creer_vote(titre, description, cle_publique="", cle_privee=""):
    salt = generer_salt()
    id = execute("""INSERT INTO votes (titre, description, salt,
                    cle_publique_vote, cle_privee_vote, statut) VALUES (?, ?, ?, ?, ?, 'en_attente')""",
                 (titre, description, salt, cle_publique, cle_privee))
    return {"success": True, "id": id}

def get_vote_actif():
    return query("SELECT * FROM votes WHERE statut = 'active' ORDER BY id DESC LIMIT 1", one=True)

def get_all_votes():
    return query("SELECT * FROM votes ORDER BY id DESC")

def get_vote(vote_id):
    return query("SELECT * FROM votes WHERE id = ?", (vote_id,), one=True)

def changer_statut_vote(vote_id, statut):
    execute("UPDATE votes SET statut = ? WHERE id = ?", (statut, vote_id))
    return {"success": True}


# Administrateurs
def authentifier_admin(username, mot_de_passe):
    admin = query("SELECT * FROM administrateurs WHERE username = ? AND mot_de_passe = ?",
                  (username, hash_password(mot_de_passe)), one=True)
    if admin:
        return {"success": True, "admin": admin}
    return {"success": False, "error": "Identifiants incorrects"}


# Resultats
def enregistrer_resultat(vote_id, option_id, nombre_bulletins):
    execute("INSERT INTO resultats (vote_id, option_id, nombre_bulletins) VALUES (?, ?, ?)",
            (vote_id, option_id, nombre_bulletins))

def resultats_existent(vote_id):
    return query("SELECT COUNT(*) as count FROM resultats WHERE vote_id = ?", (vote_id,), one=True)['count'] > 0

def vote_en_cours_ou_termine():
    return query("SELECT * FROM votes WHERE statut IN ('active', 'terminee') LIMIT 1", one=True) is not None

def get_resultats(vote_id=None):
    sql = """SELECT r.*, o.libelle FROM resultats r 
             JOIN options o ON r.option_id = o.id"""
    if vote_id:
        return query(sql + " WHERE r.vote_id = ? ORDER BY r.nombre_bulletins DESC", (vote_id,))
    return query(sql + " ORDER BY r.nombre_bulletins DESC")

def get_statistiques():
    with get_db() as conn:
        total_electeurs = conn.execute("SELECT COUNT(*) FROM electeurs").fetchone()[0]
        jetons_utilises = conn.execute("SELECT COUNT(*) FROM jetons WHERE utilise = 1").fetchone()[0]
        return {
            'total_electeurs': total_electeurs,
            'jetons_distribues': conn.execute("SELECT COUNT(*) FROM jetons").fetchone()[0],
            'jetons_utilises': jetons_utilises,
            'total_options': conn.execute("SELECT COUNT(*) FROM options").fetchone()[0],
            'total_bulletins': conn.execute("SELECT COUNT(*) FROM bulletins").fetchone()[0],
            'total_votes': conn.execute("SELECT COUNT(*) FROM votes").fetchone()[0],
            'taux_participation': round((jetons_utilises / total_electeurs) * 100, 2) if total_electeurs > 0 else 0
        }


if __name__ == "__main__":
    init_database()
