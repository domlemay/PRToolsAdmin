## Commandes utiles

### Prérequis
- Python 3.x installé
- Fichier dependencies : `requirements.txt` (si présent)

### Créer et activer l'environnement virtuel
macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Windows (cmd):
```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
```

### Installer les dépendances
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Lancer le projet
Remplacez `main.py` / `app` par le point d'entrée de votre projet.

Exemple (script Python) :
```bash
python main.py
```

Flask :
```bash
export FLASK_APP=app.py        # macOS / Linux
export FLASK_ENV=development
flask run
```
ou (Windows PowerShell)
```powershell
$env:FLASK_APP = "app.py"
$env:FLASK_ENV = "development"
flask run
```

Django :
```bash
python manage.py runserver
```

### Tests
```bash
pytest
# ou
python -m pytest
```

### Quitter l'environnement virtuel
```bash
deactivate
```

(Remplacez les noms de fichiers/commandes selon l'architecture du projet.)