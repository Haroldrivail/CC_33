# rsa.py

import json
import base64
import secrets
import math
from sympy import isprime


def generer_nombre_premier(min_val: int, max_val: int) -> int:
    while True:
        n = secrets.randbelow(max_val - min_val + 1) + min_val
        if isprime(n):
            return n


def euclide_etendu(e: int, phi_n: int) -> int:
    old_r, r = phi_n, e
    old_s, s = 0, 1
    while r != 0:
        quotient = old_r // r
        old_r, r = r, old_r - quotient * r
        old_s, s = s, old_s - quotient * s
    return old_s % phi_n


def generer_cles(taille_min: int, taille_max: int) -> tuple[tuple[int, int], tuple[int, int]]:
    # Générer deux nombres premiers distincts p et q
    p = generer_nombre_premier(taille_min, taille_max)
    q = generer_nombre_premier(taille_min, taille_max)
    while q == p:
        q = generer_nombre_premier(taille_min, taille_max)
    
    # Calculer n = p * q (le module)
    n = p * q
    
    # Calculer ϕ(n) = (p-1)(q-1) (indicatrice d'Euler)
    phi_n = (p - 1) * (q - 1)
    
    # Choisir e tel que 1 < e < ϕ(n) et pgcd(e, ϕ(n)) = 1
    while True:
        e = secrets.randbelow(phi_n - 2) + 2  # e dans [2, phi_n - 1]
        if math.gcd(e, phi_n) == 1:
            break
    
    # Calculer d, l'inverse modulaire de e mod ϕ(n) grace à l'algorithme d'Euclide étendu
    d = euclide_etendu(e, phi_n)
    
    cle_publique = (n, e)
    cle_privee = (n, d)
    
    return cle_publique, cle_privee


def chiffrer_rsa(message: int, n: int, e: int) -> int:
    if message >= n:
        raise ValueError(f"Le message ({message}) doit être inférieur à n ({n})")
    return pow(message, e, n)


def dechiffrer_rsa(chiffre: int, n: int, d: int) -> int:
    return pow(chiffre, d, n)


def generer_cles_rsa(taille_min: int = 50000, taille_max: int = 200000):
    cle_pub, cle_priv = generer_cles(taille_min, taille_max)
    return {"n": cle_pub[0], "e": cle_pub[1]}, {"n": cle_priv[0], "d": cle_priv[1]}


def cles_vers_json(public, private):
    return json.dumps({k: str(v) for k, v in public.items()}), json.dumps({k: str(v) for k, v in private.items()})


def json_vers_cle_publique(s):
    data = json.loads(s)
    return {"n": int(data["n"]), "e": int(data["e"])}


def json_vers_cle_privee(s):
    data = json.loads(s)
    return {"n": int(data["n"]), "d": int(data["d"])}


def chiffrer_vote(candidat_id, electeur_id, cle_pub):
    vote = json.dumps({"candidat_id": candidat_id, "electeur_id": electeur_id})
    m = int.from_bytes(vote.encode(), 'big')
    c = chiffrer_rsa(m, cle_pub["n"], cle_pub["e"])
    vote_b64 = base64.b64encode(c.to_bytes((c.bit_length() + 7) // 8, 'big')).decode()
    return {"vote_chiffre": vote_b64, "hash": str(hash(vote))}


def dechiffrer_vote(vote_chiffre, cle_priv):
    c = int.from_bytes(base64.b64decode(vote_chiffre), 'big')
    m = dechiffrer_rsa(c, cle_priv["n"], cle_priv["d"])  # m = c^d mod n
    vote_json = m.to_bytes((m.bit_length() + 7) // 8, 'big').decode()
    return json.loads(vote_json)


def signer_message(message, cle_priv):
    h = hash(message) % cle_priv["n"]
    return str(dechiffrer_rsa(h, cle_priv["n"], cle_priv["d"]))

