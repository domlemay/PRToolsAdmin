from typing import Dict

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QInputDialog,
    QAbstractItemView,
)
from PyQt6.QtCore import QThread, pyqtSignal

from database import fetch_premier_repondants, fetch_premier_repondant
from windows.info_user import InfoUtilisateurWindow


class PageUserAdmin(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        layout_principal = QVBoxLayout()
        layout_btn = QHBoxLayout()

        # Boutons Ajouter
        self.btn_ajouter = QPushButton("Nouveau Utilisateur")
        layout_btn.addWidget(self.btn_ajouter)
        

        # Bouton Info Utilisateur
        self.btn_info_user = QPushButton("Info Utilisateur")
        layout_btn.addWidget(self.btn_info_user)

        # Bouton Actualiser
        self.btn_refresh = QPushButton("Actualiser")
        layout_btn.addWidget(self.btn_refresh)

        # Ajouter la barre de boutons au layout principal
        layout_principal.addLayout(layout_btn)

        # Label de statut (chargement / erreurs)
        self.status_label = QLabel("")
        layout_principal.addWidget(self.status_label)

        # Tableau des PR
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Prénom", "Nom", "Email", "Cellulaire", "No. PR", "Actif"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        layout_principal.addWidget(self.table)
        self.setLayout(layout_principal)

        # Connexions boutons
        self.btn_ajouter.clicked.connect(self.ajouter_utilisateur)
        self.btn_info_user.clicked.connect(self.info_utilisateur)
        self.btn_refresh.clicked.connect(self.load_premiers_repondants)

        # Thread de chargement
        self._load_thread: QThread | None = None

        # Charger les données au démarrage
        self.load_premiers_repondants()

    # ------------------------------------------------------------------
    #  Ajout manuel d'un utilisateur (pour l'instant seulement dans la GUI)
    # ------------------------------------------------------------------

    def ajouter_utilisateur(self):
        """Ouvre la fenêtre pour saisir les informations d'un nouvel utilisateur
        et l'ajoute à la table.
        """
        prenom, ok = QInputDialog.getText(self, "Prénom", "Entrez le prénom :")
        if not ok or not prenom:
            return

        nom, ok = QInputDialog.getText(self, "Nom", "Entrez le nom :")
        if not ok or not nom:
            return

        email, ok = QInputDialog.getText(self, "Email", "Entrez l'email :")
        if not ok:
            email = ""

        cellulaire, ok = QInputDialog.getText(self, "Cellulaire", "Entrez le cellulaire :")
        if not ok:
            cellulaire = ""

        no_pr, ok = QInputDialog.getText(self, "No. PR", "Entrez le numéro PR :")
        if not ok:
            no_pr = ""

        actif_item, ok = QInputDialog.getItem(
            self,
            "Actif",
            "Utilisateur actif ?",
            ["Oui", "Non"],
            0,
            False,
        )
        actif = actif_item == "Oui" if ok else False

        # IMPORTANT : on utilise les mêmes clés que la BD
        # Adapte ces noms aux colonnes réelles de ta table premier_repondant.
        pr: Dict[str, object] = {
            "prenom": prenom,
            "nom": nom,
            "email": email,
            "cellulaire": cellulaire,
            "numero_pr": no_pr,   # ou "matricule" si ta colonne s'appelle comme ça
            "actif": actif,
        }

        # Pour l'instant : uniquement dans la table UI.
        # Plus tard : on fera un INSERT en BD ici.
        self.ajouter_ligne_table(pr)

    def ajouter_ligne_table(self, pr: Dict[str, object]):
        """Ajoute une ligne au tableau des PR à partir d'un dict."""

        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

        self.table.setItem(
            row_position, 0, QTableWidgetItem(str(pr.get("prenom", "")))
        )
        self.table.setItem(
            row_position, 1, QTableWidgetItem(str(pr.get("nom", "")))
        )
        self.table.setItem(
            row_position, 2, QTableWidgetItem(str(pr.get("email", "")))
        )
        self.table.setItem(
            row_position, 3, QTableWidgetItem(str(pr.get("cellulaire", "")))
        )
        # Adapte "numero_pr" à ton vrai nom de colonne si différent
        self.table.setItem(
            row_position, 4, QTableWidgetItem(str(pr.get("numero_pr", "")))
        )

        actif = pr.get("actif", False)
        self.table.setItem(
            row_position, 5, QTableWidgetItem("✅" if actif else "❌")
        )

    # ------------------------------------------------------------------
    #  Chargement asynchrone depuis la BD
    # ------------------------------------------------------------------

    def load_premiers_repondants(self):
        """
        Lance un thread pour aller chercher les premiers répondants
        sans bloquer l'interface.
        """
        # Désactiver les actions pendant le chargement
        self.btn_ajouter.setEnabled(False)
        self.btn_info_user.setEnabled(False)
        self.btn_refresh.setEnabled(False)
        self.status_label.setText("Chargement des premiers répondants...")

        # Si un thread tourne déjà, on ne relance pas
        if self._load_thread is not None and self._load_thread.isRunning():
            return

        class _LoadThread(QThread):
            finished = pyqtSignal(list)
            error = pyqtSignal(str)

            def run(self_inner):
                try:
                    prs = fetch_premier_repondants()
                    self_inner.finished.emit(prs)
                except Exception as e:
                    self_inner.error.emit(str(e))

        self._load_thread = _LoadThread(self)
        self._load_thread.finished.connect(self._on_load_finished)
        self._load_thread.error.connect(self._on_load_error)
        self._load_thread.start()

    def _on_load_finished(self, prs: list):
        # Vider le tableau
        while self.table.rowCount() > 0:
            self.table.removeRow(0)

        # Ajouter chaque PR
        for pr in prs:
            # pr est un dict retourné par fetch_premier_repondants()
            # dont les clés doivent correspondre à celles utilisées dans ajouter_ligne_table
            self.ajouter_ligne_table(pr)

        self.status_label.setText("")
        self.btn_ajouter.setEnabled(True)
        self.btn_info_user.setEnabled(True)
        self.btn_refresh.setEnabled(True)
        self._load_thread = None  # libérer la référence

    def _on_load_error(self, message: str):
        self.status_label.setText("")
        QMessageBox.warning(
            self,
            "Erreur DB",
            f"Impossible de charger les premiers répondants :\n{message}",
        )
        self.btn_ajouter.setEnabled(True)
        self.btn_info_user.setEnabled(True)
        self.btn_refresh.setEnabled(True)
        self._load_thread = None

    def info_utilisateur(self):
        """Ouvre la fenêtre d'information pour l'utilisateur sélectionné dans le tableau."""
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Aucune sélection", "Veuillez sélectionner un utilisateur dans le tableau.")
            return

        row = selected[0].row()

        def get_text(col: int) -> str:
            item = self.table.item(row, col)
            return item.text() if item else ""

        numero_pr = get_text(4)
        if not numero_pr:
            QMessageBox.warning(self, "Pas de numéro PR", "L'utilisateur sélectionné n'a pas de numéro PR dans la table.")
            return

        # Récupérer l'enregistrement complet depuis la BD
        try:
            full_user = fetch_premier_repondant(numero_pr)
        except Exception as e:
            QMessageBox.warning(self, "Erreur DB", f"Impossible de récupérer l'utilisateur :\n{e}")
            return

        if not full_user:
            QMessageBox.information(self, "Non trouvé", "Aucun utilisateur trouvé en base pour ce numéro PR.")
            return

        # Conserver la fenêtre pour éviter qu'elle soit garbage-collected
        self._info_window = InfoUtilisateurWindow(self)
        self._info_window.show_user(full_user)
        self._info_window.show()


