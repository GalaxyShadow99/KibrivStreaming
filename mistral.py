import sys
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QComboBox, QStackedWidget, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QProgressBar,QFrame
from PyQt5.QtGui import QFont, QIcon,QPixmap,QMovie
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QSize, QThread, pyqtSignal, QTimer, QElapsedTimer
import requests
import backend as bk #backend script avec toutes les fonctions !
import threading

bk.logger.log_debug("Script launched ! ")

class DownloadThread(QThread):
    progress = pyqtSignal(int)

    def __init__(self, video_url, title):
        super().__init__()
        self.video_url = video_url
        self.title = title
        self.percentProgress = 0
        self.file_size = 0
        bk.logger.log_info("DownloadThread Initialized with success!")

        # Create a timer to periodically update the progress bar
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(100)  # Update the progress bar every 100ms

    def run(self):
        def progress_hook(d):
            if d['status'] == 'downloading':
                percentage_str = bk.remove_ansi_escape_sequences(d['_percent_str']).strip().replace('%', '')
                try:
                    percentage = float(percentage_str)
                    if 0 <= percentage <= 100:
                        self.percentProgress = percentage
                        self.file_size = d.get('total_bytes', d.get('total_bytes_estimate', 0))
                except ValueError:
                    bk.logger.log_info(f"{percentage_str} % : ValueError percentage isn't between 0 and 100")

        settings = bk.LoadJsonSettings()
        bk.logger.log_info(f"Settings loaded with success")
        bk.download_video(self.video_url, settings["downloadPath"], self.title, progress_hook)
        bk.logger.log_critical(f"Download started!")

    def get_progress(self):
        return self.percentProgress

    def update_progress(self):
        # Emit the progress signal
        self.progress.emit((self.percentProgress))
    
class MainWindow(QWidget):
    
    #### QT signal pour remplir le tableau de données !    
    update_table_signal = pyqtSignal(list)
    show_alert_signal = pyqtSignal(str, str, int)
    clear_input_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        ##### LOAD SETTINGS #####
        self.searchedFilm = None
        self.update_table_signal.connect(self.update_table)
        self.show_alert_signal.connect(self.alertPopUp)
        self.clear_input_signal.connect(self.clear_input_field)
        
        self.elapsedTimer = QElapsedTimer()   
                                                             
        settings = bk.LoadJsonSettings()                                                           
        bk.logger.log_info("UI initialized")
        bk.logger.log_info("Settings initialized")
        
        self.selectedTitle = None  # Attribut pour stocker le titre sélectionné
        self.selectedUrl = None    # Attribut pour stocker l'URL sélectionnée
        self.setWindowTitle("Kibirv Streaming -- PyQt5")
        self.setGeometry(100, 100, 1200, 600)
        
        # Layout principal
        main_layout = QVBoxLayout(self)

        
        profile_button = QPushButton()
        profile_button.setIcon(QIcon('icons/profile_icon.png'))
        profile_button.setStyleSheet("border: none;")
        profile_button.setFixedSize(40, 40)

        # Contenu principal avec sidebar et page stackée
        content_layout = QHBoxLayout()

        # Sidebar de navigation (menu)
        
        sidebar = QVBoxLayout()
        sidebar.setSpacing(10)  # Espacement entre les widgets
        sidebar.setContentsMargins(10, 0, 10, 10)  # Reduce the top margin to 0
        # Créer une instance de QWidget
        sidebar_widget = QWidget()
        sidebar_widget.setStyleSheet("border: 2px solid black; border-radius:5px;")
        
        header = QLabel("Menu")
        sidebar.addSpacing(10)
        header = QLabel("Tableau de Bord")
        header.setFont(QFont("Arial", 20))
        sidebar.addWidget(header)
        sidebar.addSpacing(50) 
        
        home_button = QPushButton("Accueil")
        home_button.setIcon(QIcon("icons/home_icon.png"))
        settings_button = QPushButton("Paramètres")
        settings_button.setIcon(QIcon("icons/settings_icon.png"))
        about_button = QPushButton("À propos")
        about_button.setIcon(QIcon("icons/info_icon.png"))


        
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
        submit_button.setIcon(QIcon("icons/search.png"))
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
        submit_button.clicked.connect(self.start_process_input)

        # Connecter l'événement 'returnPressed' de l'input à la même fonction
        self.input_field.returnPressed.connect(self.start_process_input)
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
        
        
        # Create a frame to hold the progress bar and labels
        progress_frame = QFrame()
        progress_frame.setFrameShape(QFrame.StyledPanel)
        progress_frame.setLineWidth(1)
        progress_frame.setMidLineWidth(0)
        progress_frame.setStyleSheet("border-radius: 8px;")


        # Create the progress bar
        self.progressBar = QProgressBar(self)
        self.progressBar.setValue(0)
        self.progressBar.setMaximum(100)
        self.progressBar.setVisible(False)
        self.progressBar.setAlignment(Qt.AlignCenter)
        self.progressBar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
                margin : ;
            }
            QProgressBar::chunk {
                background-color: #05B8CC;
                width: 10px;
                margin: 0.5px;
            }
        """)

        # Create the percentage label
        self.percentageLabel = QLabel("0%")
        self.percentageLabel.setVisible(False)
        self.percentageLabel.setAlignment(Qt.AlignCenter)
        self.percentageLabel.setStyleSheet("font-weight: bold;")

        # Create the estimated time label
        self.estimatedTimeLabel = QLabel("Estimated time: Calculating...")
        self.estimatedTimeLabel.setAlignment(Qt.AlignCenter)

        
        home_layout.addWidget(self.progressBar)
        home_layout.addWidget(self.percentageLabel)

    ## ce widget est tellement utilisé par différentes méthodes que ça en devient chiant de l'enlever donc go juste ne plus l'afficher ;)
###        home_layout.addWidget(self.estimatedTimeLabel)

        # Add the frame to the main layout
        main_layout.addWidget(progress_frame)

        #créer un layout pour aligner les 2 boutons sur la même ligne !
        
        actionLayout = QHBoxLayout()
        self.fullScreenButton = QPushButton("Full screen")
        self.fullScreenButton.setFixedHeight(45)
        self.fullScreenButton.setFixedWidth(175)  # Limite la largeur du bouton
        self.fullScreenButton.setIcon(QIcon("icons/search.png"))
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
        self.DownldButton.setIcon(QIcon("icons/search.png"))
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
        
        

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress_bar)

        # Créer un label pour afficher les erreurs
        self.errorLabel = QLabel("")
        self.errorLabel.setStyleSheet("color: red;")  # Texte en rouge pour les erreurs
        home_layout.addWidget(self.errorLabel,alignment=Qt.AlignCenter)

        # Connecter le changement de sélection dans la table
        self.resultTable.setSelectionBehavior(QTableWidget.SelectRows)  # Permet de sélectionner des lignes entières
        self.resultTable.itemSelectionChanged.connect(self.check_selection)

        # Initialiser les boutons désactivés
        self.fullScreenButton.setEnabled(False)
        self.DownldButton.setEnabled(False)
        

        self.DownldButton.clicked.connect(self.DownloadVideo)
        self.fullScreenButton.clicked.connect(self.FullScreenFilm)
        ##### barre de chargement lors du download #######

        actionLayout.addWidget(self.fullScreenButton)  # Ajouter le bouton au layout horizontal
        actionLayout.addWidget(self.DownldButton)
        # Ajouter le layout horizontal à la mise en page principale
        home_layout.addLayout(actionLayout)  # Ajouter le layout contenant l'input et le bouton
        
        
        # Charger les paramètres JSON
        settings_data = bk.LoadJsonSettings()

        def save_settings():
            bk.EditJsonSettings("downloadPath",input_download_path.text())
            bk.EditJsonSettings("baseUrl",input_base_url.text())
            bk.EditJsonSettings("homeUrl",input_home_url.text())
            print("Json Updated ! ")
            bk.logger.log_info("Settings Updated !")

        def reset_to_defaults():
            settings_data["downloadPath"] = "/Users/macminithomasconstantin/Desktop/projets_perso/PyQtApp/films"
            settings_data["baseUrl"] = "default"
            settings_data["homeUrl"] = "default"
            update_ui_fields()

        def update_ui_fields():
            input_download_path.setText(settings_data["downloadPath"])
            input_base_url.setText(settings_data["baseUrl"])
            input_home_url.setText(settings_data["homeUrl"])

        # Créer la page des paramètres
        settings_page = QWidget()
        settings_layout = QVBoxLayout(settings_page)

        # Ajouter le label "Paramètres" en haut, centré
        settings_label = QLabel("Paramètres")
        settings_label.setFont(QFont("Arial", 18))
        settings_layout.addWidget(settings_label, alignment=Qt.AlignTop | Qt.AlignHCenter)

        # Créer les labels et champs de saisie pour chaque paramètre
        label_download_path = QLabel("Chemin de téléchargement :")
        label_download_path.setFont(QFont("Arial", 12))
        input_download_path = QLineEdit()
        input_download_path.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #A9A9A9;
                border-radius: 10px;
                font-size: 16px;
                background-color: #F0F0F0;
            }
            QLineEdit:focus {
                border: 2px solid #4682B4;
                background-color: #FFFFFF;
            }
        """)
        input_download_path.setPlaceholderText("Chemin de téléchargement")
        input_download_path.setText(settings_data["downloadPath"])

        label_base_url = QLabel("Base de l'URL :")
        label_base_url.setFont(QFont("Arial", 12))
        input_base_url = QLineEdit()
        input_base_url.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #A9A9A9;
                border-radius: 10px;
                font-size: 16px;
                background-color: #F0F0F0;
            }
            QLineEdit:focus {
                border: 2px solid #4682B4;
                background-color: #FFFFFF;
            }
        """)
        input_base_url.setPlaceholderText("Entrez la base de l'URL")
        input_base_url.setText(settings_data["baseUrl"])

        label_home_url = QLabel("URL d'accueil :")
        label_home_url.setFont(QFont("Arial", 12))
        input_home_url = QLineEdit()
        input_home_url.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #A9A9A9;
                border-radius: 10px;
                font-size: 16px;
                background-color: #F0F0F0;
            }
            QLineEdit:focus {
                border: 2px solid #4682B4;
                background-color: #FFFFFF;
            }
        """)
        input_home_url.setPlaceholderText("Entrez l'URL d'accueil")
        input_home_url.setText(settings_data["homeUrl"])

        # Layout pour les labels et champs de saisie
        input_layout = QVBoxLayout()
        input_layout.addWidget(label_download_path)
        input_layout.addWidget(input_download_path, alignment=Qt.AlignTop)
        input_layout.addWidget(label_base_url)
        input_layout.addWidget(input_base_url, alignment=Qt.AlignTop)
        input_layout.addWidget(label_home_url)
        input_layout.addWidget(input_home_url, alignment=Qt.AlignTop)

        settings_layout.addLayout(input_layout)

        # Créer les boutons pour sauvegarder et réinitialiser
        applyChangesLayout = QHBoxLayout()

        save_button = QPushButton("")
        save_button.setIcon(QIcon("icons/check.png"))
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #8DE14E;
                padding: 10px;
                border: 2px solid #A9A9A9;
                border-radius: 10px;
                font-size: 16px;
            }
            QPushButton:hover {
                border: 2px solid #4682B4;
                background-color: #FFFFFF;
            }
        """)
        save_button.clicked.connect(lambda: save_settings())
        reset_button = QPushButton("")
        reset_button.setIcon(QIcon("icons/cross.png"))
        reset_button.setStyleSheet("""
            QPushButton {
                background-color: #FF6F61;
                padding: 10px;
                border: 2px solid #A9A9A9;
                border-radius: 10px;
                font-size: 16px;
            }
            QPushButton:hover {
                border: 2px solid #4682B4;
                background-color: #FFFFFF;
            }
        """)
        reset_button.clicked.connect(lambda: reset_to_defaults())

        # Ajouter les boutons au layout
        applyChangesLayout.addWidget(reset_button, alignment=Qt.AlignHCenter)
        applyChangesLayout.addWidget(save_button, alignment=Qt.AlignHCenter)

        # Ajouter le layout des boutons à la page
        settings_layout.addLayout(applyChangesLayout)

        # Mettre à jour les champs pour refléter les valeurs actuelles
        update_ui_fields()
        # Page 3 : À propos
        simple_page = QWidget()
        simple_layout = QVBoxLayout(simple_page)

        # Ajouter le titre
        title_label = QLabel("App pour mes STI préférés, qui vous permettra de regarder ttranquillement vos films ")
        title_label.setFont(QFont("Arial", 18))
        title_label.setAlignment(Qt.AlignCenter)
        simple_layout.addWidget(title_label, alignment=Qt.AlignTop | Qt.AlignHCenter)
        title_label2 = QLabel("Hésitez pas à regarder le code ça vous donnera des idées de comment Python peut vous servir même pour matter des films...")
        title_label2.setFont(QFont("Arial", 16))
        title_label2.setAlignment(Qt.AlignCenter)
        simple_layout.addWidget(title_label2, alignment=Qt.AlignTop | Qt.AlignHCenter)

        
        # Ajout des pages à la stack
        self.page_stack.addWidget(home_page)
        self.page_stack.addWidget(settings_page)
        self.page_stack.addWidget(simple_page)

        content_layout.addWidget(self.page_stack)
        main_layout.addLayout(content_layout)

        # Connexion des boutons à la stack de pages
        home_button.clicked.connect(lambda: self.page_stack.setCurrentIndex(0) )
        settings_button.clicked.connect(lambda: self.page_stack.setCurrentIndex(1) )
        about_button.clicked.connect(lambda: self.page_stack.setCurrentIndex(2) )
        
        # Ajout d'animation (bouton qui change de taille au clic)
        self.init_animation(home_button)

    
    
    
    def alertPopUp(self, level, message, title):
        # Créer une boîte de dialogue pour l'alerte
        alert = QMessageBox()
        
        # Définir le titre de la fenêtre d'alerte
        alert.setWindowTitle(str(title))  # Assurez-vous que le titre est une chaîne de caractères
        
        # Définir le message
        alert.setText(message)
        
        # Configurer les boutons en fonction du niveau
        if level == 1:
            alert.setIcon(QMessageBox.Warning)
            alert.addButton(QMessageBox.Ok)
        elif level == 3:
            alert.setIcon(QMessageBox.Critical)
            alert.addButton(QMessageBox.Ok)
        
        # Afficher la boîte de dialogue
        alert.exec_()
    
    #### cette méthode lance juste process_input dans un thread pour ne pas plater l'UI pendant les requètes web...
    def start_process_input(self): 
        threading.Thread(target=self.process_input).start()
        # self.process_input()

    def process_input(self):
        user_input = self.input_field.text().strip()  # Récupérer le texte entré et enlever les espaces

        if not user_input:  # Vérifie si user_input est vide ou rempli d'espaces
            self.show_alert_signal.emit(
                "Entrée invalide",
                "Veuillez entrer un nom de film valide, pas d'espaces...",
                1
            )
            return  # Sortir de la fonction si l'entrée est invalide

        ResearchResponse = bk.ResearchFilm(user_input)
        
######
#####
#le return TimeoutError de la fonction GetHtmlOfUrl() du backend ne marche pas, bon c'est pas dramatique....
######
######
        if ResearchResponse:
            print(ResearchResponse)
            if(ResearchResponse == "TimeoutError"):
                self.show_alert_signal.emit(
                    "Le site a mit trop de temps à répondre, merci de vérifier que Kibriv est bien en ligne ou que votre connexion est stable ",
                    "TimeOut Error",3)
                bk.logger.log_critical(f"Timeout Error, kibriv may be down...")
                self.update_table_signal.emit([])
            
            self.resultTable.clearContents()
            
            occurences, SearchedTag = bk.FindAllOccurencesOfTag("a", ResearchResponse, NameOfSearchedFilm=user_input)

            self.resultTable.setRowCount(0)  # Réinitialiser la table avant d'ajouter de nouveaux résultats
            if not occurences:     
                self.clear_input_signal.emit() #clear l'input field ! 
                self.show_alert_signal.emit(
                    "Pas de contenu correspondant à la recherche. Kibriv est ULTRA sensible sur l'orthographe des noms de films : essayez par exemple de juste taper le début du nom !",
                    "Aucun résultat trouvé",
                    1)
                bk.logger.log_warning(f"Il n'y a pas de contenu correspondant à votre recherche : {user_input}")
            else:
                # Envoyer les résultats pour la mise à jour du tableau via un signal
                self.update_table_signal.emit(occurences)
                bk.logger.log_info(f"{len(occurences)} items have been added to the data table")
        elif ResearchResponse is None:
            print(f"{bk.FailMessage}Kibriv semble down le serveur n'a rien répondu à la request ")
            self.show_alert_signal.emit(
                "Le site est potentiellement indisponible pour le moment, vous pouvez aller vérifier par vous-même si vous pensez que c'est une erreur !",
                "Site indisponible actuellement...",
                3
            )
            bk.logger.log_critical("Kibriv semble down le serveur n'a rien répondu à la request")
            # Envoyer un signal vide pour effacer la table
            self.update_table_signal.emit([])
        
        self.clear_input_signal.emit() #clear l'input field ! 
        
    def clear_input_field(self):
        self.input_field.clear() #clear l'input field ! 
    def update_table(self, occurences):
        self.resultTable.setRowCount(0)
        if occurences:
            for elt in occurences:
                title = elt[0]
                url = elt[1]
                row = self.resultTable.rowCount()
                self.resultTable.insertRow(row)
                self.resultTable.setItem(row, 0, QTableWidgetItem(title))
                self.resultTable.setItem(row, 1, QTableWidgetItem(url))
        else:
            row = self.resultTable.rowCount()
            self.resultTable.insertRow(row)
            self.resultTable.setItem(0, 0, QTableWidgetItem("Titre du film"))
            self.resultTable.setItem(0, 1, QTableWidgetItem("Saisissez une recherche dans la barre au-dessus pour trouver l'URL d'un film en particulier"))

    def FullScreenFilm(self):
        print(f"{bk.SuccesMessage} Boutton full screen cliqué ! ")
        html_content = bk.GetHtmlOfUrl(self.selectedUrl)
        if html_content is None:
            self.alertPopUp(3,"Aucune réponse du serveur merci de vérifier que le site est disponible actuellement ","Pas de réponse du serveur")
            self.alertPopUp(1,"Les créateurs mettent fréquement un pop up qui bloque le site en échange de dons... Contre toute attente en général après 15/20 minutes les gens ont payé pour regarder des films illégalement. A moins de vouloir payer, merci de revenir d'ici quelques temps","")
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
                bk.logger.log_warning(f"L'application n'a pas détectée de lecteur de vidéo dans cette page ")
                self.alertPopUp(1,"L'application n'a pas détectée de lecteur de vidéo dans cette page : pas de panique c'est très fréquent si vous avez sélectionner une page autre que celle d'un film. Par example si vous avez prit la page du genre 'film d'action' vous rencontrerez cette erreur ! Merci donc de prendre simplement la page d'un film précis ! ","Pas de lecteur sur cette page ! ")

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
            print(self.selectedTitle)
            self.selectedUrl = selected_items[1].text()    # URL du film

            # Activer les boutons
            self.fullScreenButton.setEnabled(True)
            self.DownldButton.setEnabled(True)
            self.errorLabel.setText("")  # Effacer les erreurs précédentes
        elif len(selected_items) == 0:
            selected_items = None
            self.fullScreenButton.setEnabled(False)
            self.DownldButton.setEnabled(False)

        else:
            # Désactiver les boutons si plus d'une ligne est sélectionnée ou incomplète
            self.fullScreenButton.setEnabled(False)
            self.DownldButton.setEnabled(False)
            self.errorLabel.setText("Merci de ne sélectionner qu'un seul film pour le téléchargement, le téléchargement simultané n'est pas encore pris en charge...")
      
   ###### faut download l'URL de l'iframe pas de la page du film , ça doit encore être implémenter !!   
    
    def DownloadVideo(self):
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
            print(UrlToDwnld)
            self.IframeUrl = UrlToDwnld
        except IndexError as e:
            bk.logger.log_warning(f"Erreur : aucune iframe trouvée dans la page ({e})")
            return
        self.check_selection()
        
        self.download_thread = DownloadThread(self.IframeUrl, self.selectedTitle.replace(" ","-"))
        self.download_thread.progress.connect(self.update_progress_bar)
        self.download_thread.finished.connect(self.hide_progress_bar)
        self.download_thread.start()

        # Show the progress bar and labels
        self.progressBar.setVisible(True)
        self.percentageLabel.setVisible(True)
        #self.estimatedTimeLabel.setVisible(True)

    def hide_progress_bar(self):
        # Hide the progress bar and labels
        self.progressBar.setVisible(False)
        self.percentageLabel.setVisible(False)
        #self.estimatedTimeLabel.setVisible(False)


    def init_animation(self, button):
        button.clicked.connect(lambda: self.animate_button(button))
    """
    def update_progress_bar(self):
        if self.download_thread and self.download_thread.isRunning():
            progress = int(round(self.download_thread.get_progress()))
            self.progressBar.setValue(progress)
     """       
    def animate_button(self, button):
        anim = QPropertyAnimation(button, b"geometry")
        anim.setDuration(300)
        anim.setStartValue(QRect(button.x(), button.y(), button.width(), button.height()))
        anim.setEndValue(QRect(button.x(), button.y(), button.width() + 10, button.height() + 10))
        anim.start()

##################################### problèmes dans le calcul du temps restant ça doit ve,ir du fait de la formule ou alors le script ne cherche pas la bonne valeur dans le hook 
    def update_progress_bar(self):
        if self.download_thread and self.download_thread.isRunning():
            progress = int(round(self.download_thread.get_progress()))
            
            self.progressBar.setValue(progress)
            self.percentageLabel.setText(f"{progress}%")

            # Calculate the estimated time
            elapsed_time = self.elapsedTimer.elapsed() / 1000  # Convert to seconds
            download_speed = progress / elapsed_time if elapsed_time > 0 else 0  # Bytes per second
            remaining_size = (100 - progress) / 100 * self.download_thread.file_size  # Remaining bytes
            estimated_time = remaining_size / download_speed if download_speed > 0 else 0  # Remaining seconds

            # Format the estimated time as a string
            if estimated_time < 60:
                estimated_time_str = f"{estimated_time:.1f} seconds"
            elif estimated_time < 3600:
                estimated_time_str = f"{estimated_time / 60:.1f} minutes"
            else:
                estimated_time_str = f"{estimated_time / 3600:.1f} hours"

            self.estimatedTimeLabel.setText(f"Estimated time: {estimated_time_str}")
        else:
            self.progressBar.setVisible(False)
    def update_progress(self, value):
        self.progressBar.setValue(value)
        if value == 100:
            QMessageBox.information(self, "Téléchargement terminé", "La vidéo a été téléchargée avec succès.")
            self.progressBar.setVisible(False)
            self.percentageLabel.setVisible(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())
