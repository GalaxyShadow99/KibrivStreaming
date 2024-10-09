import sys
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QComboBox, QStackedWidget, QTableWidget, QTableWidgetItem,QHeaderView,QMessageBox,QProgressBar,QDialog
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect,QSize,QThread, pyqtSignal
import yt_dlp
import requests
#import du backend 
import backend as bk
import re


# Fonction pour supprimer les séquences ANSI (couleurs, etc.)
def remove_ansi_escape_sequences(text):
    ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)

class DownloadThread(QThread):
    progress = pyqtSignal(int)  # Signal pour transmettre le pourcentage de progression

    def __init__(self, video_url, title):
        super().__init__()
        self.video_url = video_url
        self.title = title

    def run(self):
        def progress_hook(d):
            if d['status'] == 'downloading':
                percentage_str = remove_ansi_escape_sequences(d['_percent_str']).strip().replace('%', '')
                try:
                    percentage = float(percentage_str)
                    if 0 <= percentage <= 100:
                        self.progress.emit(percentage)
                except ValueError:
                    pass

        settings = bk.LoadJsonSettings()
        bk.download_video(self.video_url, settings["downloadPath"], self.title, progress_hook)

class DownloadProgressDialog(QDialog):
    def __init__(self):
        super().__init__()
        bk.logger.log_info("DownloadProgressDialog class initialize !")
        self.setWindowTitle("Téléchargement en cours...")
        self.setGeometry(300, 300, 300, 100)

        self.progressBar = QProgressBar(self)
        self.progressBar.setGeometry(30, 40, 250, 25)
        self.progressBar.setMinimum(0)  # Fixer la valeur minimale à 0
        self.progressBar.setMaximum(100)  # Fixer la valeur maximale à 100

    def update_progress(self, value):
        print(f"Progression : {value}%")  # Vérifier que les valeurs sont bien reçues
        self.progressBar.setValue(value)
        QApplication.processEvents()  # Forcer la mise à jour de l'interface

        
        
class MainWindow(QWidget):
    
    def alertPopUp(self,alertIcon : int,alertMessage: str,title:str):
        """ Choisir l'icône de l'alerte (1 : Warning,2 : Information, 3 :  Critical, etc.) """
        # Créer une popup d'alerte
        alert = QMessageBox()
        alert.setWindowTitle(title)
        alert.setText(alertMessage)
        icon = QMessageBox.Warning
        match alertIcon:
            case 1:
                icon = QMessageBox.Warning
            case 2:
                icon = QMessageBox.Information
            case 3:
                icon = QMessageBox.Critical
            case _:
                icon = QMessageBox.Warning
        alert.setIcon(icon) 
        alert.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)  # Ajouter des boutons

        # Afficher la popup
        bk.logger.log_info(f"Popup is curently displayed with this message : {alertMessage} ")
        alert.exec_()
 
    def process_input(self):
        user_input = self.input_field.text()  # Récupérer le texte entré
        print(f"Input reçu : {user_input}")  # Pour test dans la console
        ResearchResponse = bk.ResearchFilm(user_input)
        self.resultTable.clearContents()

        if ResearchResponse:
            occurences, SearchedTag = bk.FindAllOccurencesOfTag("a", ResearchResponse, NameOfSearchedFilm=user_input)
            
            self.resultTable.setRowCount(0)  # Réinitialiser la table avant d'ajouter de nouveaux résultats
            if( occurences == []):
                self.alertPopUp(1,f"Il n'y a pas de contenu correspondant à votre recherche :  {user_input} . Kibriv est ULTRA sensible sur l'orthographe des noms de films : essayez par exemple de juste taper le début du nom ! ","Aucun résultat trouvé")
                bk.logger.log_warning(f"Il n'y a pas de contenu correspondant à votre recherche :  {user_input} . Kibriv est ULTRA sensible sur l'orthographe des noms de films : essayez par exemple de juste taper le début du nom ! ","Aucun résultat trouvé")
                
            else : 
                for elt in occurences:
                    print(elt)
                    title = elt[0]  # Ajuste selon la structure de 'elt'
                    url = elt[1]    # Ajuste selon la structure de 'elt'
                    
                    row = self.resultTable.rowCount()  # Obtenir le nombre actuel de lignes
                    self.resultTable.insertRow(row)     # Insérer une nouvelle ligne
                    
                    # Ajout des éléments à la table
                    self.resultTable.setItem(row, 0, QTableWidgetItem(title))  # Titre dans la colonne 1
                    self.resultTable.setItem(row, 1, QTableWidgetItem(url))    # URL dans la colonne 2
                
                bk.logger.log_info(f"{len(occurences)} items have been added to the data table")
            
            # bk.ShowResults(occurences, SearchedTag, user_input)
        elif ResearchResponse == None:
            print(f"{bk.FailMessage}Kibriv semble down le serveur n'a rien répondu à la request ")
            self.alertPopUp(3,"Le site est potentielement indisponible pour le moment, vous pouvez aller vérifier par vous même si vous pensez que c'est une erreur ! ","Site indisponible actuellement...")
            self.alertPopUp(1,"Les créateurs mettent fréquement un pop up qui bloque le site en échange de dons... En un mot du chantage quoi ! Mais contre toute attente en général après 10/15 minutes les gens ont payés 200€ pour regarder des films illégalement. C'est pas beau ça vous avez juste à attendre un peu qu'ils payent à votre place ","Site indisponible actuellement...")
            bk.logger.log_critical("Kibriv semble down le serveur n'a rien répondu à la request")
        
        self.input_field.clear()  # Effacer le champ après soumission

    def update_progress(self, value):
        self.progressBar.setValue(value)
        if value == 100:
            QMessageBox.information(self, "Téléchargement terminé", "La vidéo a été téléchargée avec succès.")
            self.progressBar.setVisible(False)  # Masquer la barre après le téléchargement
    
    def FullScreenFilm(self):
        print(f"{bk.SuccesMessage} Boutton full screen cliqué ! ")
        html_content = bk.GetHtmlOfUrl(self.selectedUrl)
        if html_content is None:
            self.alertPopUp(3,"Aucune réponse du serveur merci de vérifier que le site est disponible actuellement ","Pas de réponse du serveur")
            self.alertPopUp(1,"Les créateurs mettent fréquement un pop up qui bloque le site en échange de dons... En un mot du chantage quoi ! Mais contre toute attente en général après 10/15 minutes les gens ont tous lacher 1000 € pour regarder des films illégalement.... si c'est pas beau ça vous avez juste à attendre un peu","Site indisponible actuellement...")
            bk.logger.log_critical("Aucune réponse du serveur merci de vérifier que le site est disponible actuellement")

        if html_content :
            soup = BeautifulSoup(html_content, 'html.parser')
            occurences, SearchedTag = bk.FindAllLinksOrSources("iframe", soup)
            if occurences:
                try:
                    UrlToOpen = occurences[0][1]
                    bk.open_fullscreen_window(UrlToOpen)
                    bk.logger.log_info("Video is now open in full screen mode ! ")
                except Exception as e:
                    bk.logger.log_error(f"Erreur lors de l'ouverture de la fenêtre en plein écran : {e}")
                    print(f"Erreur lors de l'ouverture de la fenêtre en plein écran : {e}")
                    self.alertPopUp(3,"Une erreur est survenu lors de l'ouverture en plein écran du site... Toutes mes excuses si ce problème persiste contactez le développeur de cette app","Ouverture en plein écran")

            else:
                # print("Aucun résultat pour le tag : iframe trouvé dans le code de la page.")
                bk.logger.log_warning(f"L'application n'a pas détecter de lecteur de vidéo dans cette page ")
                self.alertPopUp(1,"L'application n'a pas détecter de lecteur de vidéo dans cette page : pas de panique c'ets très fréquent si vous avez sélectionner une page autre que celle d'un film. Par example si vous avez prit la page du genre 'film d'action' vous rencontrerez cette erreur ! Merci donc de prendre simplement la page d'un film précis ! ","Pas de lecteur sur cette page ! ")

        else:
            print(f"{bk.FailMessage}Erreur lors de la récupération de la page du film.")
            bk.logger.log_error("Erreur lors de la récupération de la page du film")
            self.alertPopUp(3,"Impossible de récupérer la page du film , merci de réassayer plus tard !  ","Site indisponible actuellement...")
            self.alertPopUp(1,"Les créateurs mettent fréquement un pop up qui bloque le site en échange de dons... En un mot du chantage quoi ! Mais contre toute attente en général après 10/15 minutes les gens ont tous lacher 1000 € pour regarder des films illégalement.... si c'est pas beau ça vous avez juste à attendre un peu","Site indisponible actuellement...")



    
    def check_selection(self):
        # Récupérer les éléments sélectionnés
        selected_items = self.resultTable.selectedItems()

        # Vérifier si une seule ligne complète est sélectionnée
        if len(selected_items) == self.resultTable.columnCount():
            # Extraire les valeurs des colonnes
            self.selectedTitle = selected_items[0].text()  # Titre du film
            self.selectedUrl = selected_items[1].text()    # URL du film

            # Activer les boutons
            self.fullScreenButton.setEnabled(True)
            self.DownldButton.setEnabled(True)
            self.errorLabel.setText("")  # Effacer les erreurs précédentes
        elif len(selected_items) == 0:
            pass
        else:
            # Désactiver les boutons si plus d'une ligne est sélectionnée ou incomplète
            self.fullScreenButton.setEnabled(False)
            self.DownldButton.setEnabled(False)
            self.errorLabel.setText("Merci de ne sélectionner qu'un seul film pour le téléchargement, le téléchargement simultané n'est pas encore pris en charge...")
      
   ###### faut download l'URL de l'iframe pas de la page du film , ça doit encore être implémenter !!   
    def DownloadVideo(self):
        # Lancer le thread de téléchargement
        self.downloadProgressDialog = DownloadProgressDialog()

        # Télécharger la page HTML via requests
        try:
            response = requests.get(self.selectedUrl)
            if response.status_code == 200:
                html_content = response.text
            else:
                print(f"Erreur : impossible de récupérer la page (statut {response.status_code})")
                
                return
        except Exception as e:
            print(f"Erreur lors de la récupération de la page : {e}")
            bk.logger.log_warning(f"Erreur lors de la récupération de la page : {e}")
            return

        # Passer le contenu HTML à BeautifulSoup pour extraire les iframes
        soup = BeautifulSoup(html_content, 'html.parser')
        occurences, SearchedTag = bk.FindAllLinksOrSources("iframe", soup)

        # Vérifier si un iframe a été trouvé et extraire l'URL
        try:
            UrlToDwnld = occurences[0][1]  # On récupère le lien de la première iframe
            self.IframeUrl = UrlToDwnld
        except IndexError as e:
            print(f"Erreur : aucune iframe trouvée dans la page ({e})")
            bk.logger.log_warning(f"Erreur : aucune iframe trouvée dans la page ({e})")
            return

        # Lancer le thread de téléchargement avec l'URL de l'iframe
        self.download_thread = DownloadThread(self.IframeUrl,SearchedTag)

        # Connecter les signaux de progression à la méthode de mise à jour
        self.download_thread.progress.connect(self.downloadProgressDialog.update_progress)
        self.download_thread.start()

        # Afficher la boîte de dialogue de progression
        self.downloadProgressDialog.exec_()
        
    
    def __init__(self):
        super().__init__()
        ##### LOAD SETTINGS #####
        settings = bk.LoadJsonSettings()
        bk.logger.log_info("UI initialized")
        bk.logger.log_info("Settings initialized")
        
        self.selectedTitle = None  # Attribut pour stocker le titre sélectionné
        self.selectedUrl = None    # Attribut pour stocker l'URL sélectionnée
        self.setWindowTitle("Kibirv Streaming -- PyQt5")
        self.setGeometry(100, 100, 1000, 700)
        
        # Layout principal
        main_layout = QVBoxLayout(self)

        
        profile_button = QPushButton()
        profile_button.setIcon(QIcon('profile_icon.png'))
        profile_button.setStyleSheet("border: none;")
        profile_button.setFixedSize(40, 40)

        # Contenu principal avec sidebar et page stackée
        content_layout = QHBoxLayout()

        # Sidebar de navigation (menu)
        
        sidebar = QVBoxLayout()
        sidebar.setSpacing(10)  # Espacement entre les widgets
        sidebar.setContentsMargins(10, 10, 10, 10)  # Marges du layout

        # Créer une instance de QWidget
        sidebar_widget = QWidget()
        sidebar_widget.setStyleSheet("border: 3px solid #000000; border-radius:5px;")

        # Ajouter les boutons au layout sidebar
        #titre header
        
        header = QLabel("Menu")
        sidebar.addSpacing(10)
        header = QLabel("Tableau de Bord")
        header.setFont(QFont("Arial", 20))
        sidebar.addWidget(header)
        sidebar.addSpacing(50)  # Ajoute un espace de 10 pixels
        
        home_button = QPushButton("Accueil")
        home_button.setIcon(QIcon("home_icon.png"))
        settings_button = QPushButton("Paramètres")
        settings_button.setIcon(QIcon("settings_icon.png"))
        about_button = QPushButton("À propos")
        about_button.setIcon(QIcon("info_icon.png"))


        
        for button in [home_button, settings_button, about_button]:
            button.setFixedHeight(45)
            button.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    border: 1px solid #cccccc;
                    border-radius: 10px;
                    padding-left: 20px;
                    font-size: 15px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #e5e5e5;
                }
            """)
            sidebar.setSpacing(20)
            sidebar.addWidget(button)

        sidebar.addStretch()

        # Associer le layout au QWidget
        sidebar_widget.setLayout(sidebar)

        # Ajouter le sidebar_widget au layout principal
        content_layout.addWidget(sidebar_widget)


        ##########################################
        ########### PAGES PRICIPALES #############
        ##########################################
        
        # Zone de contenu principal (pages stackées)
        self.page_stack = QStackedWidget()

        # Page 1 : Accueil
        home_page = QWidget()
        home_layout = QVBoxLayout(home_page)

        welcome_label = QLabel("Bienvenue sur ma première app PyQt")
        welcome_label.setFont(QFont("Arial", 18))
        home_layout.addWidget(welcome_label, alignment=Qt.AlignCenter)

        welcome_label2 = QLabel("J'vais essayer d'ajouter des widgets au pif en dessous !")
        welcome_label2.setFont(QFont("Arial", 14))
        home_layout.addWidget(welcome_label2, alignment=Qt.AlignCenter)

        # Créer un layout horizontal pour les widgets sur la même ligne
        input_layout = QHBoxLayout()

        # Créer un input (QLineEdit)
        self.input_field = QLineEdit()
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: lightgrey;
                border: 1px solid #cccccc;
                border-radius: 6px;
                font-size: 15px;
                text-align: center;
                color: black;
            }
            QLineEdit::placeholder {
                color: #999999; 
                font-style: italic;  
            }
        """)
        self.input_field.setPlaceholderText("Entrez le nom du film que vous cherchez :")
        input_layout.addWidget(self.input_field)  # Ajouter l'input au layout horizontal

        # Créer un bouton pour déclencher l'action
        submit_button = QPushButton()
        submit_button.setIcon(QIcon("search.png"))
        submit_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;  /* Rendre le fond transparent */
                border: 2px solid #cccccc;
                border-radius: 10px;
                padding: 5px;}
        """)
        input_layout.addWidget(submit_button)  # Ajouter le bouton au layout horizontal

        # Ajouter le layout horizontal à la mise en page principale
        home_layout.addLayout(input_layout)  # Ajouter le layout contenant l'input et le bouton

        # Connecter le bouton à la fonction qui traite l'input
        submit_button.clicked.connect(self.process_input)

        # Connecter l'événement 'returnPressed' de l'input à la même fonction
        self.input_field.returnPressed.connect(self.process_input)

        # Ajout d'un tableau
        numberOfRows = 1
        self.resultTable = QTableWidget(numberOfRows,2)
        # Définir une taille fixe pour la table
        self.resultTable.setStyleSheet("""
            QTableWidget {
                background-color: white;  /* Exemple de couleur de fond */
                border: 4px solid #cccccc;  /* Exemple de bordure */
                border-radius:5px;}
        """)
        self.resultTable.setHorizontalHeaderLabels(["Titre", "Url Kibriv"])
        self.resultTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)  # Ajuste la taille des colonnes à leur contenu
        
        self.resultTable.setItem(0, 0, QTableWidgetItem("Titre du film"))
        self.resultTable.setItem(0, 1, QTableWidgetItem("Saisissez une recherche dans la barre au dessus pour trouver l'URL d'un film en particulier "))
        # table.setItem(0, 0, QTableWidgetItem("Jean"))   garder pour savoir comment intégrer des données dans le tableau ! 
        # table.setItem(0, 1, QTableWidgetItem("30"))
        # table.setItem(0, 2, QTableWidgetItem("Paris"))
        home_layout.addWidget(self.resultTable)
        #créer un layout pour aligner les 2 boutons sur la même ligne !
        
        actionLayout = QHBoxLayout()
        self.fullScreenButton = QPushButton("Full screen")
        self.fullScreenButton.setFixedHeight(45)
        self.fullScreenButton.setFixedWidth(175)  # Limite la largeur du bouton
        self.fullScreenButton.setIcon(QIcon("search.png"))
        self.fullScreenButton.setIconSize(QSize(20, 20))  # Taille de l'icône
        self.fullScreenButton.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 2px solid #cccccc;
                border-radius: 10px;
                padding-left: 30px;  /* Espace entre l'icône et le texte */
                text-align: left;
                min-width: 150px;    /* Taille minimale du bouton */
                min-height: 45px;    /* Hauteur minimale */
                
            }
            QPushButton:hover {
                min-width: 170px;    /* Augmente la largeur du bouton au survol */
                min-height: 55px;    /* Augmente la hauteur du bouton au survol */
                padding-left: 40px;  /* Augmente l'espace entre l'icône et le texte */
                background-color: #e5e5e5;  /* Change la couleur de fond au survol */
                border: 2px solid #aaaaaa;  /* Change la couleur de la bordure au survol */
            }
            QPushButton:pressed {
                background-color: #cccccc;  /* Change la couleur de fond lors du clic */
                color: white;  /* Change la couleur du texte lors du clic */
                border: 2px solid #888888;  /* Change la couleur de la bordure lors du clic */
            }
        """)


        self.DownldButton = QPushButton("Télécharger vidéo")
        self.DownldButton.setFixedHeight(45)
        self.DownldButton.setFixedWidth(175)  # Limite la largeur du bouton
        self.DownldButton.clicked.connect(self.DownloadVideo)
        self.DownldButton.setIcon(QIcon("search.png"))
        self.DownldButton.setIconSize(QSize(20, 20))  # Taille de l'icône
        self.DownldButton.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 2px solid #cccccc;
                border-radius: 10px;
                padding-left: 30px;  /* Espace entre l'icône et le texte */
                text-align: left;
                min-width: 150px;    /* Taille minimale du bouton */
                min-height: 45px;    /* Hauteur minimale */
            }
            QPushButton:hover {
                min-width: 170px;    /* Augmente la largeur du bouton au survol */
                min-height: 55px;    /* Augmente la hauteur du bouton au survol */
                padding-left: 40px;  /* Augmente l'espace entre l'icône et le texte */
                background-color: #e5e5e5;  /* Change la couleur de fond au survol */
                border: 2px solid #aaaaaa;  /* Change la couleur de la bordure au survol */
            }
            QPushButton:pressed {
                background-color: #cccccc;  /* Change la couleur de fond lors du clic */
                color: white;  /* Change la couleur du texte lors du clic */
                border: 2px solid #888888;  /* Change la couleur de la bordure lors du clic */
            }
        """)      
        
        
        ##### barre de chargement lors du download #######
        self.progressBar = QProgressBar(self)
        self.progressBar.setValue(0)
        self.progressBar.setMaximum(100)
        self.progressBar.setVisible(False)  # Masquer la barre au début
        
        main_layout.addWidget(self.progressBar)

        # Créer un label pour afficher les erreurs
        self.errorLabel = QLabel("")
        self.errorLabel.setStyleSheet("color: red;")  # Texte en rouge pour les erreurs
        home_layout.addWidget(self.errorLabel,alignment=Qt.AlignCenter)

        # Connecter le changement de sélection dans la table
        self.resultTable.setSelectionBehavior(QTableWidget.SelectRows)  # Permet de sélectionner des lignes entières
        self.resultTable.itemSelectionChanged.connect(self.check_selection)

### loading bar 
        self.progressBar = QProgressBar(self)
        self.progressBar.setValue(0)
        self.progressBar.setMaximum(100)
        self.progressBar.setVisible(False)  # Masquer la barre au début
        main_layout.addWidget(self.progressBar)

        # Initialiser les boutons désactivés
        self.fullScreenButton.setEnabled(False)
        self.DownldButton.setEnabled(False)
        

        self.DownldButton.clicked.connect(self.DownloadVideo)
        self.fullScreenButton.clicked.connect(self.FullScreenFilm)

        actionLayout.addWidget(self.fullScreenButton)  # Ajouter le bouton au layout horizontal
        actionLayout.addWidget(self.DownldButton)
        # Ajouter le layout horizontal à la mise en page principale
        home_layout.addLayout(actionLayout)  # Ajouter le layout contenant l'input et le bouton


        
        # Page 2 : Paramètres
        settings_page = QWidget()
        settings_layout = QVBoxLayout(settings_page)
        settings_label = QLabel("Paramètres")
        settings_label.setFont(QFont("Arial", 18))
        settings_layout.addWidget(settings_label, alignment=Qt.AlignCenter)

        # Ajout d'un champ de texte et d'un menu déroulant
        input_field = QLineEdit()
        input_field.setPlaceholderText("Entrez votre nom...")
        combo_box = QComboBox()
        combo_box.addItems(["Option 1", "Option 2", "Option 3"])
        settings_layout.addWidget(input_field)
        settings_layout.addWidget(combo_box)

        # Page 3 : À propos
        about_page = QWidget()
        about_layout = QVBoxLayout(about_page)
        about_label = QLabel("À propos de cette application")
        about_label.setFont(QFont("Arial", 18))
        about_layout.addWidget(about_label, alignment=Qt.AlignCenter)

        # Ajout des pages à la stack
        self.page_stack.addWidget(home_page)
        self.page_stack.addWidget(settings_page)
        self.page_stack.addWidget(about_page)

        content_layout.addWidget(self.page_stack)
        main_layout.addLayout(content_layout)

        # Connexion des boutons à la stack de pages
        home_button.clicked.connect(lambda: self.page_stack.setCurrentIndex(0))
        bk.logger.log_info("User is now on home page ")
        settings_button.clicked.connect(lambda: self.page_stack.setCurrentIndex(1))
        bk.logger.log_info("User is now on settings page")
        about_button.clicked.connect(lambda: self.page_stack.setCurrentIndex(2))
        bk.logger.log_info("User is now on description app page")

        # Ajout d'animation (bouton qui change de taille au clic)
        self.init_animation(home_button)

    def init_animation(self, button):
        button.clicked.connect(lambda: self.animate_button(button))

    def animate_button(self, button):
        anim = QPropertyAnimation(button, b"geometry")
        anim.setDuration(300)
        anim.setStartValue(QRect(button.x(), button.y(), button.width(), button.height()))
        anim.setEndValue(QRect(button.x(), button.y(), button.width() + 10, button.height() + 10))
        anim.start()

if __name__ == "__main__":
    
    bk.logger.log_warning("APP IS NOW RUNNIG, PYQT HAS BEEN INITIALIZED !")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
    
