from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QLineEdit,
    QHBoxLayout,
    QDialog,
    QDialogButtonBox,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from typing import Callable, Optional, Dict, Union, List
from database import update_premier_repondant


class InfoUtilisateurWindow(QWidget):
    """Fenêtre simple pour afficher les informations d'un utilisateur.

    Méthode publique `show_user(user_dict)` pour remplir les champs.
    """

    def __init__(self, parent=None, on_saved: Optional[Callable[[dict], None]] = None, on_closed: Optional[Callable[[], None]] = None):
        super().__init__(parent)

        self.setWindowTitle("Information Utilisateur")
        self.resize(600, 900)

        main_layout = QVBoxLayout()

        # Titre en haut
        self.title_label = QLabel("")
        # style titre : plus grand et apparent
        self.title_label.setStyleSheet("font-size:18pt; font-weight:bold; padding:8px 0;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.title_label)

        # Scroll area pour supporter beaucoup de champs si besoin
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QFrame()
        self.form_layout = QFormLayout()
        content.setLayout(self.form_layout)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        # Boutons : par défaut seul `Fermer` est visible.
        self.buttons_row = QHBoxLayout()
        self.btn_close = QPushButton("Fermer")
        self.btn_save = QPushButton("Enregistrer")
        self.btn_cancel = QPushButton("Annuler")

        self.btn_close.clicked.connect(self.close)
        self.btn_save.clicked.connect(self._on_save)
        self.btn_cancel.clicked.connect(self._on_cancel)

        # Au départ, seul `Fermer` visible
        self.buttons_row.addStretch()
        self.buttons_row.addWidget(self.btn_close)
        self.buttons_row.addWidget(self.btn_save)
        self.buttons_row.addWidget(self.btn_cancel)
        self.btn_save.hide()
        self.btn_cancel.hide()
        main_layout.addLayout(self.buttons_row)

        self.setLayout(main_layout)

        # Dictionnaires de widgets pour les champs
        self._fields: Dict[str, Union[QLineEdit, QPushButton, QLabel]] = {}

        # Ordre et étiquettes par défaut (adaptables)
        self._default_fields = [
            ("prenom", "Prénom"),
            ("nom", "Nom"),
            ("email", "Email"),
            ("cellulaire", "Cellulaire"),
            ("numero_pr", "No. PR"),
            ("actif", "Actif"),
        ]

        # Valeurs initiales (pour annulation)
        self._initial_user: dict = {}

        # Callback optionnel pour rafraîchir la table externe
        self.on_saved = on_saved

        # Créer les widgets pour les champs par défaut (QLineEdit pour édition)
        for key, label in self._default_fields:
            if key in ("numero_pr", "id", "matricule"):
                # Identifiants en lecture seule
                w = QLineEdit("")
                w.setReadOnly(True)
                w.setObjectName(key)
                w.textChanged.connect(self._on_field_changed)
            elif key == "actif":
                # Bouton bascule pour bool
                w = QPushButton("Non")
                w.setCheckable(True)
                w.setObjectName(key)
                w.toggled.connect(lambda checked, btn=w: self._on_toggle_changed(btn, checked))
                self._update_toggle_style(w)
            else:
                w = QLineEdit("")
                w.setObjectName(key)
                w.textChanged.connect(self._on_field_changed)

            self._fields[key] = w
            self.form_layout.addRow(label + ":", w)

        # Note: champs supplémentaires seront ajoutés dynamiquement dans show_user
        self._dynamic_keys: List[str] = []
        self._dirty = False

    def _on_field_changed(self, *_args):
        if not self._dirty:
            self._dirty = True
            # Passer en mode édition : masquer Fermer, afficher Enregistrer/Annuler
            self.btn_close.hide()
            self.btn_save.show()
            self.btn_cancel.show()

    def _on_toggle_changed(self, btn: QPushButton, checked: bool):
        # Met à jour apparence et marque comme modifié
        self._update_toggle_style(btn)
        self._on_field_changed()

    def _update_toggle_style(self, btn: QPushButton):
        # style visuel: vert pour ON, rouge pour OFF
        if btn.isChecked():
            btn.setText("Oui")
            btn.setStyleSheet("background-color: #27ae60; color: white; border-radius:6px; padding:4px 8px;")
        else:
            btn.setText("Non")
            btn.setStyleSheet("background-color: #c0392b; color: white; border-radius:6px; padding:4px 8px;")

    def _enter_view_mode(self):
        # Revenir à l'état par défaut (aucune modification en cours)
        self._dirty = False
        self.btn_save.hide()
        self.btn_cancel.hide()
        self.btn_close.show()

    def _on_cancel(self):
        # Remettre les champs à l'état initial
        for k, v in self._initial_user.items():
            widget = self._fields.get(k)
            # QLineEdit -> restaurer texte
            if isinstance(widget, QLineEdit):
                widget.blockSignals(True)
                widget.setText("" if v is None else str(v))
                widget.blockSignals(False)
            # QPushButton (toggle) -> restaurer état
            elif isinstance(widget, QPushButton) and widget.isCheckable():
                widget.blockSignals(True)
                widget.setChecked(bool(v))
                self._update_toggle_style(widget)
                widget.blockSignals(False)

        self._enter_view_mode()

    def _on_save(self):
        # Sauvegarder modifications vers la base de données
        if not self._initial_user:
            return

        numero_pr = self._initial_user.get("numero_pr") or (self._fields.get("numero_pr").text() if self._fields.get("numero_pr") else None)
        if not numero_pr:
            QMessageBox.warning(self, "Erreur", "Impossible d'identifier l'utilisateur (numero_pr manquant).")
            return

        updates: dict = {}
        for k, widget in self._fields.items():
            if k in ("id", "numero_pr", "matricule"):
                continue

            old_val = self._initial_user.get(k, "")

            # Toggle buttons -> bool
            if isinstance(widget, QPushButton) and widget.isCheckable():
                new_bool = widget.isChecked()
                if bool(old_val) != new_bool:
                    updates[k] = new_bool
                continue

            # QLineEdit -> text
            if isinstance(widget, QLineEdit):
                new_val = widget.text()
                if str(new_val) != str(old_val):
                    updates[k] = new_val
                continue

        if updates:
            try:
                ok = update_premier_repondant(numero_pr, updates)
            except Exception:
                ok = False
            if not ok:
                QMessageBox.warning(self, "Erreur", "Échec de la mise à jour des données.")
                return
            # Mettre à jour l'état initial
            for k, v in updates.items():
                self._initial_user[k] = v
            # Callback externe
            if self.on_saved:
                try:
                    self.on_saved(self._initial_user)
                except Exception:
                    pass

        self._enter_view_mode()

    def clear(self):
        # Réinitialiser les champs par défaut
        for k, widget in self._fields.items():
            if isinstance(widget, QLineEdit):
                widget.blockSignals(True)
                widget.setText("")
                widget.blockSignals(False)

        # Supprimer les champs dynamiques ajoutés
        for key in list(self._dynamic_keys):
            for idx in range(self.form_layout.rowCount() - 1, -1, -1):
                item_label = self.form_layout.itemAt(idx, QFormLayout.ItemRole.LabelRole)
                item_field = self.form_layout.itemAt(idx, QFormLayout.ItemRole.FieldRole)
                removed = False
                if item_field and item_field.widget() is not None:
                    w = item_field.widget()
                    if w.objectName() == key:
                        w.deleteLater()
                        removed = True
                if item_label and item_label.widget() is not None:
                    wl = item_label.widget()
                    if removed or wl.text().startswith(key + ":"):
                        wl.deleteLater()
                if removed:
                    break

        self._dynamic_keys = []

        # remettre le titre
        self.title_label.setText("")
        self._initial_user = {}
        self._enter_view_mode()

    def closeEvent(self, event):
        # When used as a page in a stacked widget, notify the closer
        try:
            if getattr(self, "on_closed", None):
                try:
                    self.on_closed()
                except Exception:
                    pass
        except Exception:
            pass
        super().closeEvent(event)

    def show_user(self, user: dict):
        """Remplit la fenêtre avec les données du dict `user`.

        Les clés seront affichées; les champs connus sont formatés proprement.
        """
        if not isinstance(user, dict):
            return

        self.clear()

        # Mettre le titre avec le nom (si présent)
        nom = user.get("nom") or user.get("prenom") or ""
        self.title_label.setText(f"Information sur \"{nom}\"")

        # Enregistrer l'état initial pour annulation
        self._initial_user = dict(user)

        # Remplir champs par défaut si présents
        for key, _ in self._default_fields:
            widget = self._fields.get(key)
            if key == "actif":
                if isinstance(widget, QPushButton) and widget.isCheckable():
                    widget.blockSignals(True)
                    widget.setChecked(bool(user.get(key, False)))
                    self._update_toggle_style(widget)
                    widget.blockSignals(False)
                elif isinstance(widget, QLineEdit):
                    text = "Oui" if user.get(key) is True else ("Non" if user.get(key) is False else str(user.get(key)))
                    widget.blockSignals(True)
                    widget.setText(text)
                    widget.blockSignals(False)
            else:
                text = "" if user.get(key) is None else str(user.get(key))
                if isinstance(widget, QLineEdit):
                    widget.blockSignals(True)
                    widget.setText(text)
                    widget.blockSignals(False)

        # Afficher les clés supplémentaires non présentes dans les défauts
        known_keys = {k for k, _ in self._default_fields}
        for key, val in user.items():
            if key in known_keys:
                continue

            display_label = key

            # Champ mot de passe -> montrer bouton pour remplacer
            if key.lower() in ("password", "mot_de_passe", "motdepasse", "mdp"):
                btn = QPushButton("Remplacer le mot de passe")
                btn.setObjectName(str(key))

                def _replace_clicked(_checked=False, numero=user.get("numero_pr"), col=key):
                    # Ouvre un dialog simple pour entrer nouveau mot de passe
                    dlg = QDialog(self)
                    dlg.setWindowTitle("Remplacer le mot de passe")
                    dlg_layout = QVBoxLayout()
                    entry = QLineEdit()
                    entry.setEchoMode(QLineEdit.EchoMode.Password)
                    dlg_layout.addWidget(QLabel("Nouveau mot de passe:"))
                    dlg_layout.addWidget(entry)
                    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
                    buttons.accepted.connect(dlg.accept)
                    buttons.rejected.connect(dlg.reject)
                    dlg_layout.addWidget(buttons)
                    dlg.setLayout(dlg_layout)
                    if dlg.exec() == QDialog.DialogCode.Accepted:
                        new_pw = entry.text()
                        if numero and new_pw:
                            try:
                                update_premier_repondant(numero, {col: new_pw})
                            except Exception:
                                QMessageBox.warning(self, "Erreur", "Impossible de mettre à jour le mot de passe.")

                btn.clicked.connect(_replace_clicked)
                btn.setToolTip("Remplacer le mot de passe; le mot de passe actuel n'est pas affiché.")
                btn.setObjectName(str(key))
                self.form_layout.addRow(display_label + ":", btn)
                self._dynamic_keys.append(str(key))
                continue

            # Autres champs -> QLineEdit or toggle if boolean
            if isinstance(val, bool):
                w = QPushButton("Non")
                w.setCheckable(True)
                w.setObjectName(str(key))
                w.toggled.connect(lambda checked, btn=w: self._on_toggle_changed(btn, checked))
                self._update_toggle_style(w)
            else:
                w = QLineEdit("")
            w.setObjectName(str(key))
            if key in ("id", "numero_pr", "matricule"):
                w.setReadOnly(True)
            if isinstance(w, QLineEdit):
                w.setText("" if val is None else str(val))
                w.textChanged.connect(self._on_field_changed)
            else:
                # QPushButton toggle -> set state if boolean
                if isinstance(val, bool):
                    w.setChecked(val)
                    self._update_toggle_style(w)
            self.form_layout.addRow(display_label + ":", w)
            self._fields[key] = w
            self._dynamic_keys.append(str(key))

        # Afficher la fenêtre
        self.show()
