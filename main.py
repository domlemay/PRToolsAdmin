from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, 
QMessageBox, QVBoxLayout, QHBoxLayout, QStackedWidget, QWidget, 
QTableWidget, QTableWidgetItem)
from pages.accueil import PageAccueil
from pages.user_admin import PageUserAdmin


class MainWindows(QMainWindow):
    def __init__(self):
        super().__init__()

        
        #Parametres de la fenetre de l'application
        container = QWidget()
        self.setCentralWidget(container)
        layout = QHBoxLayout()
        container.setLayout(layout)


        #---Sidebar---
        self.sidebar = QVBoxLayout()
        self.btn_home = QPushButton("Accueil")
        self.btn_user_admin = QPushButton("Administration des utilisateurs")

        for btn in [self.btn_home, self.btn_user_admin]:
            btn.setCheckable(True)
            self.sidebar.addWidget(btn)
        
        self.sidebar.addStretch()

        #---Contenu principal---
        self.stack = QStackedWidget()
        self.page_home = PageAccueil()
        self.page_users = PageUserAdmin()

        self.stack.addWidget(self.page_home) #0
        self.stack.addWidget(self.page_users) #1


        #---Navigation---
        self.btn_home.clicked.connect(lambda: self.switch_page(0, self.btn_home))
        self.btn_user_admin.clicked.connect(lambda: self.switch_page(1, self.btn_user_admin))

        self.switch_page(0, self.btn_home)

        layout.addLayout(self.sidebar, 1)
        layout.addWidget(self.stack, 4)

        self.setWindowTitle("Gestion des Utilisateurs")
        self.resize(1200, 800)
    
    def switch_page(self, index, btnActive):
        self.stack.setCurrentIndex(index)
        for btn in [self.btn_home, self.btn_user_admin]:
            btn.setChecked(False)

        btnActive.setChecked(True)


if __name__ == "__main__":
    app = QApplication([])
    with open("style/style.qss", "r") as f:
        app.setStyleSheet(f.read()) 
    window = MainWindows()
    window.show()
    app.exec()