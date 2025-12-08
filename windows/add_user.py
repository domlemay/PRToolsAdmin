from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QComboBox, QSpinBox, QPushButton
from PyQt6.QtCore import pyqtSignal

class AddUtilisateurWindow(QWidget):

    utilisateursAdded = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        
        layout = QVBoxLayout()
        nom_label = QLabel("Nom:")
        self.nom_input = QLineEdit()
        self.nom_input.setPlaceholderText("Entrez le nom")
        programme_label = QLabel("Programme:")
        self.programme_input = QComboBox()
        self.programme_input.addItems(["Informatique", "Mathématiques", "Physique", "Chimie"])
        age_label = QLabel("Âge:")
        self.age_input = QSpinBox()
        self.age_input.setRange(5, 80)

        self.btn_ajouter = QPushButton("Ajouter")
        self.btn_ajouter.clicked.connect(self.valider_ajout)

        layout.addWidget(nom_label)
        layout.addWidget(self.nom_input)
        layout.addWidget(programme_label)
        layout.addWidget(self.programme_input)
        layout.addWidget(age_label)
        layout.addWidget(self.age_input)
        layout.addWidget(self.btn_ajouter)
        self.setLayout(layout)
    
        self.setWindowTitle("Ajouter un Étudiant")

    def valider_ajout(self):
        etudiants = {
            "nom": self.nom_input.text(),
            "programme": self.programme_input.currentText(),
            "age": self.age_input.value()
        }
        self.etudiantsAdded.emit(etudiants)
        self.close()

