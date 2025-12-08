from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
)
from PyQt6.QtCore import Qt


class InfoUtilisateurWindow(QWidget):
    """Fenêtre simple pour afficher les informations d'un utilisateur.

    Méthode publique `show_user(user_dict)` pour remplir les champs.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Information Utilisateur")
        self.resize(420, 320)

        main_layout = QVBoxLayout()

        # Scroll area pour supporter beaucoup de champs si besoin
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QFrame()
        self.form_layout = QFormLayout()
        content.setLayout(self.form_layout)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        # Bouton fermer
        self.btn_close = QPushButton("Fermer")
        self.btn_close.clicked.connect(self.close)
        main_layout.addWidget(self.btn_close, alignment=Qt.AlignmentFlag.AlignRight)

        self.setLayout(main_layout)

        # Dictionnaire de QLabel pour les champs connus
        self._labels = {}

        # Ordre et étiquettes par défaut (adaptables)
        self._default_fields = [
            ("prenom", "Prénom"),
            ("nom", "Nom"),
            ("email", "Email"),
            ("cellulaire", "Cellulaire"),
            ("numero_pr", "No. PR"),
            ("actif", "Actif"),
        ]

        # Créer les widgets pour les champs par défaut
        for key, label in self._default_fields:
            value_label = QLabel("")
            value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self._labels[key] = value_label
            self.form_layout.addRow(label + ":", value_label)

    def clear(self):
        # Réinitialiser les valeurs des labels par défaut
        for lbl in self._labels.values():
            lbl.setText("")

        # Supprimer les lignes supplémentaires (au-delà des défauts)
        # On reconstruit la form si nécessaire
        # (méthode simple : on garde seulement le nombre de champs par défaut)
        while self.form_layout.rowCount() > len(self._default_fields):
            # removeRow n'existe pas sur QFormLayout; on retire les widgets manuellement
            idx = self.form_layout.rowCount() - 1
            item_label = self.form_layout.itemAt(idx, QFormLayout.ItemRole.LabelRole)
            item_field = self.form_layout.itemAt(idx, QFormLayout.ItemRole.FieldRole)
            if item_label:
                w = item_label.widget()
                if w:
                    w.deleteLater()
            if item_field:
                w2 = item_field.widget()
                if w2:
                    w2.deleteLater()

    def show_user(self, user: dict):
        """Remplit la fenêtre avec les données du dict `user`.

        Les clés seront affichées; les champs connus sont formatés proprement.
        """
        if not isinstance(user, dict):
            return

        self.clear()

        # Remplir champs par défaut si présents
        for key, _ in self._default_fields:
            val = user.get(key, "")
            if key == "actif":
                # Normaliser l'affichage Bool -> Oui/Non
                if isinstance(val, bool):
                    text = "Oui" if val else "Non"
                else:
                    text = str(val)
            else:
                text = str(val)
            self._labels[key].setText(text)

        # Afficher les clés supplémentaires non présentes dans les défauts
        known_keys = {k for k, _ in self._default_fields}
        for key, val in user.items():
            if key in known_keys:
                continue
            lbl_key = QLabel(str(key) + ":")
            lbl_val = QLabel(str(val))
            lbl_val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.form_layout.addRow(lbl_key, lbl_val)

        # Afficher la fenêtre (l'appelant peut la `show()` ou `exec()`)
        self.show()
