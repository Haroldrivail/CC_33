
import http.server
import socketserver
import json
import urllib.parse
import database as db
import rsa as crypto

PORT, HOST = 8000, "localhost"
db.init_database()

def generer_cles():
    cle_publique, cle_privee = crypto.generer_cles_rsa(1024)
    cle_pub_json, cle_priv_json = crypto.cles_vers_json(cle_publique, cle_privee)
    return cle_pub_json, cle_priv_json


class VoteRequestHandler(http.server.SimpleHTTPRequestHandler):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="static", **kwargs)
    

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        response = json.dumps(data, ensure_ascii=False)
        self.wfile.write(response.encode())
    

    def get_body(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            return json.loads(body.decode())
        except:
            return {}
    

    def do_OPTIONS(self):
        self.send_json({})
    

    def do_GET(self):
    
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)
        
    
        if path == "/api/options":
            options = db.get_all_options()
            self.send_json({"success": True, "options": options})
        
    
        elif path == "/api/options/vote":
            vote_id = query.get("vote_id", [None])[0]
            if vote_id:
                options = db.get_options_by_vote(int(vote_id))
                self.send_json({"success": True, "options": options})
            else:
                self.send_json({"success": False, "error": "vote_id requis"}, 400)
        
    
        elif path == "/api/electeurs":
            electeurs = db.get_all_electeurs()
            self.send_json({"success": True, "electeurs": electeurs})
        
    
        elif path == "/api/votes":
            votes = db.get_all_votes()
            self.send_json({"success": True, "votes": votes})
        
    
        elif path == "/api/vote/actif":
            vote = db.get_vote_actif()
            self.send_json({"success": True, "vote": vote})
        
    
        elif path == "/api/statistiques":
            stats = db.get_statistiques()
            self.send_json({"success": True, "statistiques": stats})
        
    
        elif path == "/api/resultats":
            resultats = db.get_resultats()
            self.send_json({"success": True, "resultats": resultats})
        
    
        elif path == "/api/bulletins":
            bulletins = db.get_all_bulletins()
            self.send_json({"success": True, "bulletins": bulletins})
        
    
        elif path == "/api/bulletins/count":
            count = db.get_nombre_bulletins()
            self.send_json({"success": True, "count": count})
        
    
        elif path == "/api/generer-cles":
            cle_pub, cle_priv = generer_cles()
            self.send_json({"success": True, "cle_publique": cle_pub, "cle_privee": cle_priv})
        
    
        elif path == "/":
            self.path = "/index.html"
            super().do_GET()
        
    
        elif path.startswith("/api/"):
            self.send_json({"success": False, "error": "Route non trouvee"}, 404)
        
    
        else:
            super().do_GET()
    

    def do_POST(self):
    
        path = urllib.parse.urlparse(self.path).path
        data = self.get_body()
        
    
        if path == "/api/auth/electeur":
            email = data.get("email", "")
            mot_de_passe = data.get("mot_de_passe", "")
            resultat = db.authentifier_electeur(email, mot_de_passe)
            if resultat["success"]:
                self.send_json(resultat)
            else:
                self.send_json(resultat, 401)
        
    
        elif path == "/api/auth/admin":
            username = data.get("username", "")
            mot_de_passe = data.get("mot_de_passe", "")
            resultat = db.authentifier_admin(username, mot_de_passe)
            if resultat["success"]:
                self.send_json(resultat)
            else:
                self.send_json(resultat, 401)
        
    
        elif path == "/api/electeurs/inscription":
            nom = data.get("nom", "")
            prenom = data.get("prenom", "")
            email = data.get("email", "")
            mot_de_passe = data.get("mot_de_passe", "")
            
            if not nom or not prenom or not email or not mot_de_passe:
                self.send_json({"success": False, "error": "Tous les champs sont requis"}, 400)
            else:
                resultat = db.ajouter_electeur(nom, prenom, email, mot_de_passe)
                if resultat["success"]:
                    self.send_json(resultat)
                else:
                    self.send_json(resultat, 400)
        
    
        elif path == "/api/options":
            libelle = data.get("libelle", "")
            vote_id = data.get("vote_id", "")
            description = data.get("description", "")
            
            if not libelle:
                self.send_json({"success": False, "error": "Libelle requis"}, 400)
            elif not vote_id:
                self.send_json({"success": False, "error": "Vote requis"}, 400)
            else:
                resultat = db.ajouter_option(vote_id, libelle, description)
                self.send_json(resultat)
        
    
        elif path == "/api/options/supprimer":
            option_id = data.get("id", "")
            
            if not option_id:
                self.send_json({"success": False, "error": "ID requis"}, 400)
            elif db.vote_en_cours_ou_termine():
                self.send_json({"success": False, "error": "Impossible de supprimer une option pendant ou apres un vote"}, 400)
            else:
                resultat = db.supprimer_option(option_id)
                self.send_json(resultat)
        
    
        elif path == "/api/jeton":
            electeur_id = data.get("electeur_id", "")
            vote_id = data.get("vote_id", "")
            
            if not electeur_id:
                self.send_json({"success": False, "error": "Electeur requis"}, 400)
                return
            if not vote_id:
                self.send_json({"success": False, "error": "Vote requis"}, 400)
                return
            
        
            electeur = db.get_electeur(electeur_id)
            if not electeur:
                self.send_json({"success": False, "error": "Electeur non trouve"}, 404)
                return
            
        
            vote = db.get_vote(vote_id)
            if not vote:
                self.send_json({"success": False, "error": "Vote non trouve"}, 404)
                return
            if vote["statut"] != "active":
                self.send_json({"success": False, "error": "Ce vote n'est pas actif"}, 400)
                return
            
        
            jeton = db.generer_jeton(electeur_id, vote_id, vote["salt"])
            jeton_hash = db.hash_jeton(jeton)
            
        
            existant = db.jeton_existe(jeton_hash)
            if existant:
                if existant["utilise"] == 1:
                    self.send_json({"success": False, "error": "Vous avez deja vote pour ce vote"}, 400)
                else:
                    self.send_json({"success": True, "jeton": jeton, "message": "Jeton deja attribue"})
            else:
            
                db.creer_jeton(vote_id, jeton_hash)
                self.send_json({"success": True, "jeton": jeton})
        
    
        elif path == "/api/voter":
            jeton = data.get("jeton", "")
            option_id = data.get("option_id", "")
            
            if not jeton:
                self.send_json({"success": False, "error": "Jeton requis"}, 400)
                return
            if not option_id:
                self.send_json({"success": False, "error": "Option requise"}, 400)
                return
            
        
            jeton_hash = db.hash_jeton(jeton)
            jeton_data = db.jeton_existe(jeton_hash)
            
            if not jeton_data:
                self.send_json({"success": False, "error": "Jeton invalide"}, 400)
                return
            if jeton_data["utilise"] == 1:
                self.send_json({"success": False, "error": "Ce jeton a deja ete utilise"}, 400)
                return
            
        
            vote = db.get_vote(jeton_data["vote_id"])
            if not vote:
                self.send_json({"success": False, "error": "Vote non trouve"}, 404)
                return
            if vote["statut"] != "active":
                self.send_json({"success": False, "error": "Ce vote n'est pas actif"}, 400)
                return
            
            try:
            
                cle_pub = crypto.json_vers_cle_publique(vote["cle_publique_vote"])
                bulletin = crypto.chiffrer_vote(option_id, jeton_hash, cle_pub)
                
            
                resultat = db.enregistrer_bulletin(vote["id"], bulletin["vote_chiffre"], jeton_hash)
                if resultat["success"]:
                    self.send_json(resultat)
                else:
                    self.send_json(resultat, 400)
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 400)
        
    
        elif path == "/api/votes":
            titre = data.get("titre", "")
            description = data.get("description", "")
            
            if not titre:
                self.send_json({"success": False, "error": "Titre requis"}, 400)
            else:
                cle_pub, cle_priv = generer_cles()
                resultat = db.creer_vote(titre, description, cle_pub, cle_priv)
                self.send_json(resultat)
        
    
        elif path == "/api/votes/statut":
            vote_id = data.get("id", "")
            statut = data.get("statut", "")
            
            if not vote_id or not statut:
                self.send_json({"success": False, "error": "ID et statut requis"}, 400)
            else:
                resultat = db.changer_statut_vote(vote_id, statut)
                self.send_json(resultat)
        
    
        elif path == "/api/decompte":
            vote_id = data.get("vote_id", "")
            
            if not vote_id:
                self.send_json({"success": False, "error": "ID vote requis"}, 400)
                return
            
        
            vote = db.get_vote(vote_id)
            if not vote:
                self.send_json({"success": False, "error": "Vote non trouve"}, 404)
                return
            
        
            if db.resultats_existent(vote_id):
                resultats = db.get_resultats(vote_id)
                self.send_json({"success": True, "resultats": resultats, "deja_calcule": True})
                return
            
            try:
            
                cle_priv = crypto.json_vers_cle_privee(vote["cle_privee_vote"])
                bulletins = db.get_bulletins_by_vote(vote_id)
                
            
                decompte = {}
                for bulletin in bulletins:
                    try:
                        resultat = crypto.dechiffrer_vote(bulletin["bulletin_chiffre"], cle_priv)
                        option_id = resultat["candidat_id"]
                        if option_id in decompte:
                            decompte[option_id] = decompte[option_id] + 1
                        else:
                            decompte[option_id] = 1
                    except:
                        pass
                
            
                for option_id in decompte:
                    nombre = decompte[option_id]
                    db.enregistrer_resultat(vote_id, option_id, nombre)
                
            
                total = 0
                for option_id in decompte:
                    total = total + decompte[option_id]
                
                resultats = db.get_resultats(vote_id)
                self.send_json({"success": True, "resultats": resultats, "total_bulletins": total})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 400)
        
    
        else:
            self.send_json({"success": False, "error": "Route non trouvee"}, 404)


if __name__ == "__main__":
    print("")
    print("Demarrage du serveur de vote...")
    print("URL: http://" + HOST + ":" + str(PORT))
    print("Admin: admin / admin123")
    print("")
    
    serveur = socketserver.TCPServer((HOST, PORT), VoteRequestHandler)
    
    try:
        serveur.serve_forever()
    except KeyboardInterrupt:
        print("")
        print("Arret du serveur.")
        serveur.shutdown()
