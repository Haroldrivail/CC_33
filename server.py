# server.py
import http.server
import socketserver
import json
import urllib.parse
import database as db
import rsa as crypto

PORT, HOST = 8000, "localhost"
db.init_database()

def generer_cles():
    pub, priv = crypto.generer_cles_rsa(1024)
    return crypto.cles_vers_json(pub, priv)

# Recuperation des routes GET
ROUTES_GET = {
    "/api/options": lambda _: {"success": True, "options": db.get_all_options()},
    "/api/electeurs": lambda _: {"success": True, "electeurs": db.get_all_electeurs()},
    "/api/votes": lambda _: {"success": True, "votes": db.get_all_votes()},
    "/api/vote/actif": lambda _: {"success": True, "vote": db.get_vote_actif()},
    "/api/statistiques": lambda _: {"success": True, "statistiques": db.get_statistiques()},
    "/api/resultats": lambda _: {"success": True, "resultats": db.get_resultats()},
    "/api/bulletins": lambda _: {"success": True, "bulletins": db.get_all_bulletins()},
    "/api/bulletins/count": lambda _: {"success": True, "count": db.get_nombre_bulletins()},
    "/api/generer-cles": lambda _: {"success": True, "cle_publique": generer_cles()[0], "cle_privee": generer_cles()[1]},
}

# Recuperation des routes POST
def post_auth_electeur(d):
    r = db.authentifier_electeur(d.get("email", ""), d.get("mot_de_passe", ""))
    if r["success"]:
        r["electeur"].pop("mot_de_passe", None)
    return r if r["success"] else (r, 401)

def post_auth_admin(d):
    r = db.authentifier_admin(d.get("username", ""), d.get("mot_de_passe", ""))
    if r["success"]: r["admin"].pop("mot_de_passe", None)
    return r if r["success"] else (r, 401)

def post_inscription(d):
    if not all(d.get(f) for f in ["nom", "prenom", "email", "mot_de_passe"]):
        return {"success": False, "error": "Tous les champs sont requis"}
    return db.ajouter_electeur(d["nom"], d["prenom"], d["email"], d["mot_de_passe"])

def post_option(d):
    if not d.get("libelle"):
        return {"success": False, "error": "Libellé requis"}
    if not d.get("vote_id"):
        return {"success": False, "error": "Vote requis"}
    return db.ajouter_option(d["vote_id"], d["libelle"], d.get("description", ""))

def post_supprimer_option(d):
    if not d.get("id"): return {"success": False, "error": "ID requis"}
    if db.vote_en_cours_ou_termine():
        return {"success": False, "error": "Impossible de supprimer une option pendant ou après un vote"}
    return db.supprimer_option(d["id"])

def post_demander_jeton(d):
    """Demande un jeton anonyme pour voter"""
    if not d.get("electeur_id"):
        return {"success": False, "error": "Électeur requis"}
    if not d.get("vote_id"):
        return {"success": False, "error": "Vote requis"}
    
    electeur = db.get_electeur(d["electeur_id"])
    if not electeur:
        return {"success": False, "error": "Électeur non trouvé"}, 404
    
    vote = db.get_vote(d["vote_id"])
    if not vote:
        return {"success": False, "error": "Vote non trouvé"}, 404
    if vote["statut"] != "active":
        return {"success": False, "error": "Ce vote n'est pas actif"}
    
    # Générer le jeton (déterministe : même électeur = même jeton)
    jeton = db.generer_jeton(d["electeur_id"], d["vote_id"], vote["salt"])
    jeton_hash = db.hash_jeton(jeton)
    
    # Vérifier si le jeton existe déjà
    existant = db.jeton_existe(jeton_hash)
    if existant:
        if existant["utilise"]:
            return {"success": False, "error": "Vous avez déjà voté pour ce vote"}
        # Retourner le même jeton
        return {"success": True, "jeton": jeton, "message": "Jeton déjà attribué"}
    
    # Créer le jeton
    db.creer_jeton(d["vote_id"], jeton_hash)
    return {"success": True, "jeton": jeton}

def post_voter(d):
    """Vote anonyme avec jeton"""
    if not d.get("jeton"):
        return {"success": False, "error": "Jeton requis"}
    if not d.get("option_id"):
        return {"success": False, "error": "Option requise"}
    
    jeton_hash = db.hash_jeton(d["jeton"])
    jeton = db.jeton_existe(jeton_hash)
    
    if not jeton:
        return {"success": False, "error": "Jeton invalide"}
    if jeton["utilise"]:
        return {"success": False, "error": "Ce jeton a déjà été utilisé"}
    
    vote = db.get_vote(jeton["vote_id"])
    if not vote:
        return {"success": False, "error": "Vote non trouvé"}, 404
    if vote["statut"] != "active":
        return {"success": False, "error": "Ce vote n'est pas actif"}
    
    try:
        # Chiffrer le bulletin avec la clé publique du vote (anonyme)
        cle_pub = crypto.json_vers_cle_publique(vote["cle_publique_vote"])
        bulletin = crypto.chiffrer_vote(d["option_id"], jeton_hash, cle_pub)
        
        # Enregistrer le bulletin anonyme
        return db.enregistrer_bulletin(vote["id"], bulletin["vote_chiffre"], jeton_hash)
    except Exception as e:
        return {"success": False, "error": str(e)}

def post_vote(d):
    if not d.get("titre"):
        return {"success": False, "error": "Titre requis"}
    pub, priv = generer_cles()
    return db.creer_vote(d["titre"], d.get("description", ""), pub, priv)

def post_vote_statut(d):
    if not all(d.get(f) for f in ["id", "statut"]):
        return {"success": False, "error": "ID et statut requis"}
    return db.changer_statut_vote(d["id"], d["statut"])

def post_decompte(d):
    if not d.get("vote_id"): return {"success": False, "error": "ID vote requis"}
    
    vote = db.get_vote(d["vote_id"])
    if not vote: return {"success": False, "error": "Vote non trouvé"}, 404
    
    # Vérifier si les résultats ont déjà été calculés
    if db.resultats_existent(d["vote_id"]):
        return {"success": True, "resultats": db.get_resultats(d["vote_id"]), "deja_calcule": True}
    
    try:
        cle = crypto.json_vers_cle_privee(vote["cle_privee_vote"])
        decompte = {}
        for b in db.get_bulletins_by_vote(d["vote_id"]):
            try:
                # Déchiffrer le bulletin anonyme
                resultat = crypto.dechiffrer_vote(b["bulletin_chiffre"], cle)
                oid = resultat["candidat_id"]  # option_id
                decompte[oid] = decompte.get(oid, 0) + 1
            except: pass
        
        for oid, nb in decompte.items():
            db.enregistrer_resultat(d["vote_id"], oid, nb)
        
        return {"success": True, "resultats": db.get_resultats(d["vote_id"]), "total_bulletins": sum(decompte.values())}
    except Exception as e:
        return {"success": False, "error": str(e)}

ROUTES_POST = {
    "/api/auth/electeur": post_auth_electeur,
    "/api/auth/admin": post_auth_admin,
    "/api/electeurs/inscription": post_inscription,
    "/api/options": post_option,
    "/api/options/supprimer": post_supprimer_option,
    "/api/jeton": post_demander_jeton,
    "/api/voter": post_voter,
    "/api/votes": post_vote,
    "/api/votes/statut": post_vote_statut,
    "/api/decompte": post_decompte,
}

class VoteRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="static", **kwargs)
    
    def send_json(self, data, status=200):
        self.send_response(status)
        for h, v in [("Content-Type", "application/json; charset=utf-8"), ("Access-Control-Allow-Origin", "*"),
                     ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"), ("Access-Control-Allow-Headers", "Content-Type")]:
            self.send_header(h, v)
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
    
    def get_body(self):
        try: return json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))).decode())
        except: return {}
    
    def do_OPTIONS(self): self.send_json({})
    
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)
        
        if path in ROUTES_GET: 
            self.send_json(ROUTES_GET[path](None))
        elif path == "/api/options/vote":
            vote_id = query.get("vote_id", [None])[0]
            if vote_id:
                self.send_json({"success": True, "options": db.get_options_by_vote(int(vote_id))})
            else:
                self.send_json({"success": False, "error": "vote_id requis"}, 400)
        elif path == "/": 
            self.path = "/index.html"
            super().do_GET()
        elif path.startswith("/api/"): 
            self.send_json({"success": False, "error": "Route non trouvée"}, 404)
        else: 
            super().do_GET()
    
    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        if path not in ROUTES_POST: self.send_json({"success": False, "error": "Route non trouvée"}, 404); return
        r = ROUTES_POST[path](self.get_body())
        status = r[1] if isinstance(r, tuple) else (400 if not r.get("success", True) else 200)
        self.send_json(r[0] if isinstance(r, tuple) else r, status)

if __name__ == "__main__":
    with socketserver.TCPServer((HOST, PORT), VoteRequestHandler) as httpd:
        print(f"\n Serveur de vote: http://{HOST}:{PORT}\n   Admin: admin / admin123\n")
        try: httpd.serve_forever()
        except KeyboardInterrupt: print("\nArrêt.")
