from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox


class PageAccueil(QWidget):


    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        title = QLabel("Bienvenue sur PRToolsAdmin")
        layout.addWidget(title)

        btn_login = QPushButton("Se connecter")
        btn_login.clicked.connect(self._on_login_clicked)
        layout.addWidget(btn_login)

    def _on_login_clicked(self):
        QMessageBox.information(self, "Connexion", "Fonctionnalité de connexion non implémentée.")
