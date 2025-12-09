from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QHBoxLayout,
    QPushButton,
    QCheckBox,
    QMessageBox,
    QDateEdit,
)
from PyQt6.QtCore import pyqtSignal, QDate, Qt
from database import insert_premier_repondant, get_table_columns
try:
    from passlib.hash import bcrypt
except Exception:
    bcrypt = None


class AddUtilisateurWindow(QWidget):
    """Fenêtre pour ajouter un utilisateur.

    Emmet un signal `user_added` avec le dict utilisateur lorsqu'on clique sur
    Ajouter et que les validations sont satisfaites.
    """

    user_added = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Ajouter un utilisateur")
        self.resize(600, 600)

        main_layout = QVBoxLayout()
        # Titre de la page
        self.title_label = QLabel("Ajouter un utilisateur")
        self.title_label.setStyleSheet("font-size:18pt; font-weight:bold; padding:8px 0;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.title_label)

        form = QFormLayout()

        # Tenter de récupérer la liste des colonnes de la table `intervenant_pr`.
        # Si la connexion DB n'est pas disponible, on retombe sur un ensemble
        # de champs minimaux.
        self._fields = {}
        self._required_names = []
        try:
            cols = get_table_columns("intervenant_pr")
        except Exception:
            cols = None

        if not cols:
            # fallback : anciens champs minimaux
            cols = [
                {"column_name": "prenom", "is_nullable": "YES", "data_type": "text", "column_default": None},
                {"column_name": "nom", "is_nullable": "YES", "data_type": "text", "column_default": None},
                {"column_name": "email", "is_nullable": "YES", "data_type": "text", "column_default": None},
                {"column_name": "cellulaire", "is_nullable": "YES", "data_type": "text", "column_default": None},
                {"column_name": "numero_pr", "is_nullable": "YES", "data_type": "text", "column_default": None},
                {"column_name": "mot_de_passe", "is_nullable": "NO", "data_type": "text", "column_default": None},
                {"column_name": "actif", "is_nullable": "YES", "data_type": "boolean", "column_default": None},
                {"column_name": "admin", "is_nullable": "YES", "data_type": "boolean", "column_default": None},
            ]

        # Construire les widgets dynamiquement en excluant la PK auto-incrémentée
        for col in cols:
            name = col.get("column_name")
            default = col.get("column_default")
            dtype = (col.get("data_type") or "").lower()

            # skip auto-increment PKs (nextval in default) and explicit 'id'
            if name == "id" or (default and "nextval" in str(default)):
                continue

            # skip inactivation date field if present (user requested)
            if name and any(x in name.lower() for x in ("inactiv", "inactif", "date_inact", "date_inactive")):
                continue

            # determine if this column is required (NOT NULL and no default)
            is_required = (col.get("is_nullable") or "YES").upper() == "NO" and not col.get("column_default")

            widget = None
            # bool -> checkbox
            if "bool" in dtype:
                widget = QCheckBox(name)
                # actif should default to True
                if name and name.lower() == "actif":
                    widget.setChecked(True)
                else:
                    widget.setChecked(False)
                # prepare container to allow 'REQUIS' after field
                container = QHBoxLayout()
                container.addWidget(widget)
                if is_required:
                    dot = QLabel("")
                    dot.setFixedSize(12, 12)
                    dot.setStyleSheet("border-radius:6px; background-color: #c0392b; margin-left:8px;")
                    container.addWidget(dot)
                    # store indicator
                    self._required_indicators = getattr(self, '_required_indicators', {})
                    self._required_indicators[name] = dot
                form.addRow(name + ":", container)
            else:
                # Password handling
                if name in ("mot_de_passe", "password", "pwd"):
                    # mot de passe avec indicateur rouge/vert (non vide)
                    pwd = QLineEdit()
                    pwd.setEchoMode(QLineEdit.EchoMode.Password)
                    self._pw_dot = QLabel("")
                    self._pw_dot.setFixedSize(12, 12)
                    self._pw_dot.setStyleSheet("border-radius:6px; background-color: #c0392b; margin-left:8px;")
                    pw_container = QHBoxLayout()
                    pw_container.addWidget(pwd)
                    pw_container.addWidget(self._pw_dot)
                    form.addRow("Mot de passe:", pw_container)
                    # add confirm field and indicator for equality
                    self._pw_confirm = QLineEdit()
                    self._pw_confirm.setEchoMode(QLineEdit.EchoMode.Password)
                    self._pw_ok_dot = QLabel("")
                    self._pw_ok_dot.setFixedSize(12, 12)
                    self._pw_ok_dot.setStyleSheet("border-radius:6px; background-color: #c0392b; margin-left:8px;")
                    pw_row = QHBoxLayout()
                    pw_row.addWidget(self._pw_confirm)
                    pw_row.addWidget(self._pw_ok_dot)
                    form.addRow("Confirmer mot de passe:", pw_row)
                    # connect changes
                    self._pw_confirm.textChanged.connect(self._validate)
                    pwd.textChanged.connect(self._validate)
                    # store widgets
                    self._fields[name] = pwd
                    self._fields["__password_confirm__"] = self._pw_confirm
                    # continue to next column
                    continue
                else:
                    # Date-like types -> QDateEdit with calendar popup and default today
                    if any(t in dtype for t in ("date", "timestamp", "time")):
                        ded = QDateEdit()
                        ded.setCalendarPopup(True)
                        ded.setDate(QDate.currentDate())
                        widget = ded
                        container = QHBoxLayout()
                        container.addWidget(widget)
                        if is_required:
                            dot = QLabel("")
                            dot.setFixedSize(12, 12)
                            dot.setStyleSheet("border-radius:6px; background-color: #c0392b; margin-left:8px;")
                            container.addWidget(dot)
                            self._required_indicators = getattr(self, '_required_indicators', {})
                            self._required_indicators[name] = dot
                        form.addRow(name + ":", container)
                    else:
                        widget = QLineEdit()
                        container = QHBoxLayout()
                        container.addWidget(widget)
                        if is_required:
                            dot = QLabel("")
                            dot.setFixedSize(12, 12)
                            dot.setStyleSheet("border-radius:6px; background-color: #c0392b; margin-left:8px;")
                            container.addWidget(dot)
                            self._required_indicators = getattr(self, '_required_indicators', {})
                            self._required_indicators[name] = dot
                        form.addRow(name + ":", container)

            if widget is not None:
                # track changes to revalidate depending on widget type
                if isinstance(widget, QCheckBox):
                    widget.stateChanged.connect(self._validate)
                else:
                    # QLineEdit has textChanged, QDateEdit has dateChanged
                    if hasattr(widget, "textChanged"):
                        widget.textChanged.connect(self._validate)
                    elif isinstance(widget, QDateEdit):
                        widget.dateChanged.connect(self._validate)
                    # otherwise no signal to connect

            if widget is not None:
                self._fields[name] = widget

            # if column is NOT NULL and has no default, require it
            if is_required:
                self._required_names.append(name)

        # (We added 'REQUIS' next to fields during row creation)

        main_layout.addLayout(form)

        # boutons
        btn_row = QHBoxLayout()
        self.btn_add = QPushButton("Ajouter")
        self.btn_cancel = QPushButton("Annuler")
        self.btn_add.setEnabled(False)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_cancel)
        btn_row.addWidget(self.btn_add)
        main_layout.addLayout(btn_row)

        self.setLayout(main_layout)

        # Connexions des boutons
        self.btn_add.clicked.connect(self._on_add)
        self.btn_cancel.clicked.connect(self.close)

        # run initial validation
        # set focus to first input (if any)
        for k, w in self._fields.items():
            try:
                if isinstance(w, QLineEdit):
                    w.setFocus()
                    break
            except Exception:
                pass

        self._validate()

    def _validate(self):
        """Valide l'état du formulaire et active/désactive le bouton Ajouter.

        Les champs obligatoires doivent être non vides et les deux mots de passe identiques.
        Les champs obligatoires vides reçoivent un style rouge.
        """
        all_ok = True

        # vérifier les champs NOT NULL identifiés
        for name in self._required_names:
            widget = self._fields.get(name)
            if widget is None:
                all_ok = False
                break
            # check checkbox differently
            if isinstance(widget, QCheckBox):
                # checkbox always has a value; consider it filled
                continue
            # otherwise require non-empty text or valid date
            if isinstance(widget, QDateEdit):
                if not widget.date().isValid():
                    all_ok = False
                    break
            else:
                try:
                    if not widget.text().strip():
                        all_ok = False
                        break
                except Exception:
                    all_ok = False
                    break

        # si champ password présent, vérifier qu'il y a une confirmation identique
        pwd_widget = self._fields.get("mot_de_passe") or self._fields.get("password")
        if pwd_widget is not None:
            confirm = self._fields.get("__password_confirm__")
            pwd_text = ""
            confirm_text = ""
            try:
                pwd_text = pwd_widget.text().strip()
            except Exception:
                pwd_text = ""
            try:
                confirm_text = confirm.text().strip() if confirm is not None else ""
            except Exception:
                confirm_text = ""

            # password dot: green when non-empty
            if getattr(self, "_pw_dot", None):
                if pwd_text:
                    self._pw_dot.setStyleSheet("border-radius:6px; background-color: #27ae60; margin-left:8px;")
                else:
                    self._pw_dot.setStyleSheet("border-radius:6px; background-color: #c0392b; margin-left:8px;")

            # confirmation dot: green when equal to password and non-empty
            if getattr(self, "_pw_ok_dot", None):
                if pwd_text and confirm_text and pwd_text == confirm_text:
                    self._pw_ok_dot.setStyleSheet("border-radius:6px; background-color: #27ae60; margin-left:8px;")
                else:
                    self._pw_ok_dot.setStyleSheet("border-radius:6px; background-color: #c0392b; margin-left:8px;")

            if not (pwd_text and confirm_text and pwd_text == confirm_text):
                all_ok = False

        # update required field indicators (red -> green)
        indicators = getattr(self, '_required_indicators', {})
        for name, dot in indicators.items():
            widget = self._fields.get(name)
            ok = False
            if widget is None:
                ok = False
            elif isinstance(widget, QCheckBox):
                ok = True
            elif isinstance(widget, QDateEdit):
                ok = bool(widget.date().isValid())
            else:
                try:
                    ok = bool(widget.text().strip())
                except Exception:
                    ok = False

            if ok:
                dot.setStyleSheet("border-radius:6px; background-color: #27ae60; margin-left:8px;")
            else:
                dot.setStyleSheet("border-radius:6px; background-color: #c0392b; margin-left:8px;")

        # Enable add only if tout est ok
        self.btn_add.setEnabled(all_ok)

    def _on_add(self):
        # Build user dict using same keys que la BD/page
        # Construire le dict d'insertion depuis les widgets dynamiques
        user = {}
        for name, widget in self._fields.items():
            if name == "__password_confirm__":
                continue
            if isinstance(widget, QCheckBox):
                user[name] = bool(widget.isChecked())
            elif isinstance(widget, QDateEdit):
                # export ISO date string
                try:
                    user[name] = widget.date().toString(Qt.DateFormat.ISODate)
                except Exception:
                    user[name] = ""
            else:
                # QLineEdit or others
                try:
                    user[name] = widget.text().strip()
                except Exception:
                    user[name] = ""

        # Avant insertion : hacher le mot de passe si présent
        try:
            cols_info = get_table_columns("intervenant_pr")
            existing_cols = {c['column_name'] for c in cols_info}
        except Exception:
            existing_cols = set()

        for candidate in ("mot_de_passe", "password", "pwd"):
            if candidate in user and user.get(candidate) is not None:
                raw_pwd = user.pop(candidate)
                # choisir la colonne cible existante
                if 'mot_de_passe' in existing_cols:
                    target_col = 'mot_de_passe'
                elif candidate in existing_cols:
                    target_col = candidate
                else:
                    # fallback
                    target_col = candidate

                if raw_pwd is None:
                    hashed = None
                else:
                    try:
                        if bcrypt is not None:
                            hashed = bcrypt.hash(raw_pwd)
                        else:
                            # fallback simple (moins sécurisé) si passlib absent
                            import hashlib

                            hashed = hashlib.sha256(raw_pwd.encode('utf-8')).hexdigest()
                            # Prefix to indicate fallback method
                            hashed = f"sha256${hashed}"
                    except Exception as e:
                        print("Erreur lors du hachage du mot de passe:", e)
                        hashed = raw_pwd

                user[target_col] = hashed
                break

        # Tenter d'insérer en base de données
        ok = False
        err_msg = None
        try:
            res = insert_premier_repondant(user)
            # function now returns (bool, Optional[str])
            if isinstance(res, tuple):
                ok, err_msg = res
            else:
                ok = bool(res)
        except Exception as e:
            ok = False
            err_msg = str(e)
            print("Erreur insertion BD :", err_msg)

        if not ok:
            # Show more diagnostic information when available
            details = f"\n({err_msg})" if err_msg else ""
            QMessageBox.warning(self, "Erreur", f"Impossible d'ajouter l'utilisateur en base de données." + details)
            return

        # émettre signal pour que le caller ajoute en table UI / autres callbacks
        try:
            self.user_added.emit(user)
        except Exception:
            pass

        # fermer la fenêtre
        self.close()

    def closeEvent(self, event):
        # call external on_closed handler if provided
        try:
            if getattr(self, "on_closed", None):
                try:
                    self.on_closed()
                except Exception:
                    pass
        except Exception:
            pass
        super().closeEvent(event)

