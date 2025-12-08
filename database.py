# database.py
"""
Module central pour l'accès à la base de données NEON (PostgreSQL).

Contient :
- la configuration de connexion (DATABASE_URL)
- une fonction pour tester la connexion (test_connection)
- une fonction pour récupérer les premiers répondants (fetch_premier_repondants)
"""

import os
from typing import List, Dict, Any

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv


# ---------------------------------------------------------------------
#  CONFIGURATION DE LA BASE DE DONNÉES
# ---------------------------------------------------------------------

# Charge les variables du fichier .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Cette ligne permet de s'assurer que DATABASE_URL est bien None si non défini
if not DATABASE_URL:
    DATABASE_URL = None


# ---------------------------------------------------------------------
#  OUTIL : TEST DE CONNEXION
# ---------------------------------------------------------------------

def test_connection() -> bool:
    """
    Vérifie simplement que la base de données est accessible.

    Retourne:
        True  si SELECT 1 fonctionne
        False si une erreur survient
    """
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("SELECT 1 AS ok;")
                row = cur.fetchone()
                return bool(row and row["ok"] == 1)
    except Exception as e:
        print("Erreur de connexion à la base NEON :", e)
        return False


# ---------------------------------------------------------------------
#  REQUÊTES MÉTIER : PREMIERS RÉPONDANTS
# ---------------------------------------------------------------------

def fetch_premier_repondants() -> List[Dict[str, Any]]:
    """
    Récupère tous les premiers répondants dans un format list[dict].

    Chaque élément de la liste est un dict du type :
    {
        "prenom": ...,
        "nom": ...,
        "email": ...,
        "cellulaire": ...,
        "numero_pr": ...,
        "actif": True/False,
    }

    IMPORTANT :
    - Adapte les noms de colonnes (SELECT ...) pour qu'ils
      correspondent à ta vraie structure de table dans PostgreSQL.
    """

    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL n'est pas défini. Créez un fichier .env ou définissez la variable d'environnement.")

    query = """
        SELECT
            prenom,
            nom,
            email,
            cellulaire,
            numero_pr,
            actif
        FROM public.intervenant_pr
        ORDER BY nom, prenom;
    """

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query)
            fetched = cur.fetchall()

    # Normalize output to the expected keys
    results = []
    for r in fetched:
        results.append({
            "prenom": r.get("prenom") or "",
            "nom": r.get("nom") or "",
            "email": r.get("email") or "",
            "cellulaire": r.get("cellulaire") or r.get("telephone") or "",
            "numero_pr": r.get("numero_pr") or r.get("matricule") or r.get("numero_pr") or "",
            "actif": bool(r.get("actif")) if r.get("actif") is not None else False,
        })

    return results


def fetch_premier_repondant(numero_pr: str) -> Dict[str, Any] | None:
    """Récupère un premier répondant par son `numero_pr`.

    Retourne un dict représentant la ligne ou `None` si non trouvé.
    """
    if not numero_pr:
        return None

    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL n'est pas défini. Créez un fichier .env ou définissez la variable d'environnement.")

    query = """
        SELECT *
        FROM public.intervenant_pr
        WHERE numero_pr = %s
        LIMIT 1;
    """

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, (numero_pr,))
            row = cur.fetchone()

    if not row:
        return None

    # Retourner toutes les colonnes sous forme de dict; normaliser quelques clés courantes
    result: Dict[str, Any] = {}
    for k, v in row.items():
        if k == "actif":
            result[k] = bool(v)
        else:
            result[k] = v if v is not None else ""

    return result
