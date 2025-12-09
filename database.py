# database.py
"""
Module central pour l'accès à la base de données NEON (PostgreSQL).

Contient :
- la configuration de connexion (DATABASE_URL)
- une fonction pour tester la connexion (test_connection)
- une fonction pour récupérer les premiers répondants (fetch_premier_repondants)
"""

import os
from typing import List, Dict, Any, Optional

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


def fetch_premier_repondant(numero_pr: str) -> Optional[Dict[str, Any]]:
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


def update_premier_repondant(numero_pr: str, updates: Dict[str, Any]) -> bool:
    """Met à jour un intervenant identifié par `numero_pr`.

    Args:
        numero_pr: identifiant du premier répondant
        updates: dict colonne->valeur à mettre à jour

    Retourne True si la mise à jour s'est bien passée, False sinon.
    """
    if not numero_pr:
        return False

    if not updates:
        return True

    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL n'est pas défini. Créez un fichier .env ou définissez la variable d'environnement.")

    # Construction paramétrée de la requête
    cols = []
    params = []
    for k, v in updates.items():
        cols.append(f"{k} = %s")
        params.append(v)

    params.append(numero_pr)
    set_clause = ", ".join(cols)
    query = f"UPDATE public.intervenant_pr SET {set_clause} WHERE numero_pr = %s;"

    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))
                conn.commit()
        return True
    except Exception as e:
        print("Erreur update_premier_repondant:", e)
        return False


def insert_premier_repondant(values: Dict[str, Any]) -> (bool, Optional[str]):
    """Insère un nouveau premier répondant.

    `values` est un dict colonne->valeur. La fonction construira
    une requête INSERT paramétrée pour les colonnes fournies.

    Retourne True si l'insertion réussit.
    """
    if not values:
        return False

    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL n'est pas défini. Créez un fichier .env ou définissez la variable d'environnement.")

    # Récupérer colonnes existantes pour éviter d'insérer des colonnes inexistantes
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'intervenant_pr';"
                )
                existing = {r[0] for r in cur.fetchall()}
    except Exception as e:
        print("Erreur lecture colonnes BD :", e)
        return False

    cols = []
    params = []
    placeholders = []

    # Détecter colonnes NOT NULL sans valeur par défaut pour fournir des valeurs par défaut
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT column_name, is_nullable, data_type, column_default FROM information_schema.columns "
                    "WHERE table_schema = 'public' AND table_name = 'intervenant_pr';"
                )
                cols_meta = {row[0]: {'is_nullable': row[1], 'data_type': row[2], 'default': row[3]} for row in cur.fetchall()}
    except Exception as e:
        print("Erreur lecture métadonnées BD :", e)
        return False

    # Préparer valeurs à insérer : prendre uniquement les colonnes existantes
    for k, v in values.items():
        if k in existing:
            cols.append(k)
            params.append(v)
            placeholders.append("%s")

    # Ajouter valeurs par défaut pour les colonnes NOT NULL manquantes
    for col_name, meta in cols_meta.items():
        if col_name in cols:
            continue
        is_nullable = (meta.get('is_nullable') or '').upper() == 'YES'
        has_default = meta.get('default') is not None
        if not is_nullable and not has_default:
            # fournir une valeur par défaut sûre selon le type
            dtype = (meta.get('data_type') or '').lower()
            if 'bool' in dtype:
                default_val = False
            elif 'int' in dtype or 'numeric' in dtype or 'decimal' in dtype:
                default_val = 0
            else:
                default_val = ""

            cols.append(col_name)
            params.append(default_val)
            placeholders.append("%s")

    if not cols:
        # Aucune colonne valide à insérer
        print("Aucune colonne valide à insérer pour intervenant_pr.")
        return False

    cols_clause = ", ".join(cols)
    ph_clause = ", ".join(placeholders)
    query = f"INSERT INTO public.intervenant_pr ({cols_clause}) VALUES ({ph_clause});"

    try:
        # Coerce certains types : remplacer '' par None pour types non textuels
        for i, col_name in enumerate(cols):
            meta = cols_meta.get(col_name, {})
            dtype = (meta.get('data_type') or '').lower()
            val = params[i]
            if isinstance(val, str) and val == "":
                # pour les timestamps/dates/nombres, utiliser NULL plutôt que empty string
                if any(t in dtype for t in ("timestamp", "date", "time", "int", "numeric", "decimal")):
                    params[i] = None

        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))
                conn.commit()
        return True, None
    except Exception as e:
        err = str(e)
        print("Erreur insert_premier_repondant:", err)
        return False, err


def get_table_columns(table_name: str) -> List[Dict[str, Any]]:
    """Retourne la liste des colonnes pour `table_name` dans le schema public.

    Chaque élément est un dict contenant :
      - column_name
      - is_nullable ("YES"/"NO")
      - data_type
      - column_default (peut être None)

    Lève une exception si DATABASE_URL n'est pas configuré.
    """
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL n'est pas défini.")

    query = (
        "SELECT column_name, is_nullable, data_type, column_default "
        "FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = %s "
        "ORDER BY ordinal_position;"
    )

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (table_name,))
            rows = cur.fetchall()

    cols = []
    for r in rows:
        cols.append({
            "column_name": r[0],
            "is_nullable": r[1],
            "data_type": r[2],
            "column_default": r[3],
        })

    return cols
