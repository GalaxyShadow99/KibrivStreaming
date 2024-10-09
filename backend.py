import requests
from bs4 import BeautifulSoup
import re
from colorama import Fore, Back, Style, init
# UI
import webview
#download video 
import yt_dlp
import os
import json
##loger imports ##
import io
import atexit
import traceback
import sys
import logging
from datetime import datetime,timedelta
# Initialiser Colorama
init(autoreset=True)
# Définir les couleurs pour les messages
SuccesMessage = Fore.GREEN
FailMessage = Fore.RED
WarnigMessage = Fore.YELLOW

baseUrl = "https://karvaz.com/"
homeUrl = "https://karvaz.com/p1xqygvdx320sq/home/karvaz"

### LOGER ####
class MyLogger:
    def __init__(self, log_dir='--LOGS--'):
        self.log_dir = log_dir
        # Créer le dossier des logs basé sur l'année/mois/jour
        self.create_log_dir()

        # Configurer le logger
        self.logger = logging.getLogger('CustomLogger')
        self.logger.setLevel(logging.DEBUG)  # Enregistrer tous les niveaux de logs

        # Format des logs
        log_format = logging.Formatter('%(asctime)s [%(levelname)s] - %(message)s')

        # Handler pour fichier (logs organisés par date)
        log_file = self.get_log_filename()

        # Créer les répertoires si nécessaire
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        # Configurer le file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(log_format)
        self.logger.addHandler(file_handler)

        # Redirect stdout to a buffer
        self.stdout_buffer = io.StringIO()
        sys.stdout = self.stdout_buffer

        # Register the copy_console_to_log method to be called when the program ends
        atexit.register(self.copy_console_to_log)

        # Nettoyer les anciens logs
        self.eraseOldLogs()
        
    def eraseOldLogs(self):
        """Supprime les fichiers de log et les dossiers vieux de plus d'un mois."""
        one_month_ago = datetime.now() - timedelta(days=1)
        
        for root, dirs, files in os.walk(self.log_dir, topdown=False):
            # Supprimer les fichiers de log vieux de plus de 30 jours
            for file_name in files:
                file_path = os.path.join(root, file_name)
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                if file_time < one_month_ago:
                    print(f"Deleting log file: {file_path}")
                    os.remove(file_path)
            
            # Supprimer les dossiers vides après la suppression des fichiers
            if not os.listdir(root):  # Vérifie si le dossier est vide
                print(f"Deleting empty directory: {root}")
                os.rmdir(root)

    def copy_console_to_log(self):
        # Get the console output from the buffer
        console_output = self.remove_ansi_escape_sequences(self.stdout_buffer.getvalue())

        # Write the console output to the log file
        self.log_critical(console_output)

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """Log unhandled exceptions as critical."""
        if issubclass(exc_type, KeyboardInterrupt):
            # Ignorer les interruptions clavier (Ctrl+C)
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        # Log the unhandled exception as critical
        self.logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
        # Get the exception details as a string
        exception_details = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        # Write the exception details to the log file
        self.log_critical(exception_details)      

    def create_log_dir(self):
        """Créer le dossier racine des logs si nécessaire."""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)
    
    def get_log_filename(self):
        """Générer un nom de fichier basé sur la date et l'heure."""
        time_str = datetime.now().strftime('%Y-%m-%d')
        log_folder = os.path.join(self.log_dir, time_str)
        os.makedirs(log_folder, exist_ok=True)
        log_file = datetime.now().strftime('%H:%M.log')
        return os.path.join(log_folder, log_file)        

    def log_debug(self, message):
        self.logger.debug(message)
    
    def log_info(self, message):
        self.logger.info(message)
    
    def log_warning(self, message):
        self.logger.warning(message)
    
    def log_error(self, message):
        self.logger.error(message)
    
    def log_critical(self, message):
        self.logger.critical(message)

    def remove_ansi_escape_sequences(self, text):
        """Remove ANSI escape sequences (e.g., colors) from the text."""
        import re
        ansi_escape = re.compile(r'(?:\x1B[@-_][0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

       
logger = MyLogger()

def remove_ansi_escape_sequences(text):
    ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)

#### SETTINGS ######

def LoadJsonSettings():
    
    with open('settings.json', 'r') as json_file:
        settings = json.load(json_file)
        dwnldPath = settings["downloadPath"]
        siteBaseUrl = settings["baseUrl"]
        homeUrl = settings["homeUrl"]
    print(f"{SuccesMessage}Paramètres lus avec succès !")
        
    if dwnldPath == "default" and siteBaseUrl == "default" and homeUrl == "default":
        with open('defaultSettings.json', 'r') as json_file:
            defaultSettings = json.load(json_file)
            dwnldPath = os.path.join(os.path.expanduser("~"), "Downloads")
            siteBaseUrl = defaultSettings["baseUrl"]
            homeUrl = defaultSettings["homeUrl"]
        print(f"{SuccesMessage}Paramètres par défaut appliqués  !")
    return {"downloadPath" : dwnldPath,"baseUrl" :  siteBaseUrl,"homeUrl" : homeUrl}
        
def EditJsonSettings(settingName,value):
    with open('settings.json', 'r') as json_file:
        data = json.load(json_file)
    
    data[settingName] = value
    with open('settings.json', 'w') as json_file:
        json.dump(data, json_file, indent=4)

    print(f"{SuccesMessage}Le paramètre {settingName} a été modifié.")

def download_video(video_url, download_dir, title, progress_hook=None):
    # Configuration pour télécharger la vidéo avec yt-dlp
    ydl_opts = {
        'format': 'best',  # Télécharger la meilleure qualité
        'outtmpl': f'{download_dir}/{title}.%(ext)s',  # Modèle de nom de fichier
        'progress_hooks': [progress_hook] if progress_hook else [],  # Hook pour suivre la progression
        'quiet': True,  # Supprimer les messages de débogage
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        print("Téléchargement terminé avec succès.")
    except Exception as e:
        print(f"Erreur lors du téléchargement : {e}")

def GetHtmlOfUrl(url: str, timeout_duration: int = 10):   
    """Récupère le contenu HTML de l'URL spécifiée avec une gestion du timeout."""

    # Vérifier si l'URL est valide et complète
    if not url.startswith("https://"):
        print(f"{FailMessage}URL non valide, merci de réessayer ! {Fore.RESET}")
        
    
    try:
        # Ajouter un délai d'attente pour éviter les requêtes trop longues
        response = requests.get(url, timeout=timeout_duration) 
        if response.status_code == 200:
            HtmlContent = response.text
            return HtmlContent
        else:
            print(f"{FailMessage}Erreur lors de la requête: {response.status_code}{Fore.RESET}")
            return None
    except requests.exceptions.Timeout:
        print(f"{FailMessage}Le site met trop de temps à répondre. Veuillez réessayer plus tard.{Fore.RESET}")
        return "TimeoutError"
    except requests.exceptions.RequestException as e:
        print(f"{FailMessage}Erreur de requête : {e}{Fore.RESET}")
        return None

def FindAllOccurencesOfTag(tag, Html, NameOfSearchedFilm=None):
    """Trouve toutes les occurrences d'un tag spécifique dans le contenu HTML."""
    if Html is None:
        print(f"{FailMessage}Aucun contenu HTML disponible pour la recherche.")
        return [], tag

    Occurences = []
    paragraphs = Html.find_all(tag)
    
    for tags in paragraphs:
        text = tags.get_text()
        clean_text = re.sub(r'\s+', ' ', text).strip()
        if clean_text == "" or clean_text.lower() == "</br>" or clean_text.startswith("$"):
            continue
        
        href = tags.get('href')
        src = tags.get('src')

        # Concaténer l'URL de base si nécessaire
        if src and src.startswith('/'):
            src = f"{baseUrl}{src[1:]}"
            
        if href and href.startswith('/'):
            href = f"{baseUrl}{href[1:]}"


        if NameOfSearchedFilm:
            if NameOfSearchedFilm.lower() in clean_text.lower():
                if href:
                    Occurences.append((clean_text, href))
                elif src:
                    Occurences.append((clean_text, src))
                else:
                    Occurences.append((clean_text, None))
            
        else:
            if href:
                Occurences.append((clean_text, href))
            elif src:
                Occurences.append((clean_text, src))
            else:
                Occurences.append((clean_text, None))

    return Occurences, tag

def SubmitForm(form_url, data):
    """Soumet un formulaire à l'URL spécifiée avec les données fournies."""
    try:
        response = requests.post(form_url, data=data)
        if response.status_code == 200:
            print(f"{SuccesMessage}Recherche soumise avec succès !")
            with open("response.html", "w", encoding="utf-8") as htmlfile:
                htmlfile.write(response.text)
            #print(f"{SuccesMessage}Le HTML a été sauvegardé dans 'response.html', en cas de besoin n'hésite zpas à ouvrir ce fichier dans votre navigateur pour voir la réponse du serveur .")
            return response.text  # Retourne le contenu HTML de la réponse
        else:
            print(f"{FailMessage}Erreur lors de la soumission du formulaire: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"{FailMessage}Exception lors de la soumission du formulaire: {e}")
        return None

def ResearchFilm(SearchWord):
    """Effectue une recherche de film en soumettant un formulaire de recherche."""
    full_url = homeUrl

    html_content = GetHtmlOfUrl(full_url)
    if not html_content:
        print("Erreur lors de la récupération de la page d'accueil.")
        return None
    
    soup = BeautifulSoup(html_content, 'html.parser')
    form = soup.find('form')
    if not form:
        print("Aucun formulaire trouvé à cette URL.")
        return None

    form_action = form.get('action')
    form_method = form.get('method', 'get').lower()
    form_url = form_action if form_action.startswith('http') else f"{baseUrl}{form_action}"

    data = {'searchword': SearchWord}
    if form_method == 'post':
        result_html = SubmitForm(form_url, data)
        if result_html:
            return BeautifulSoup(result_html, 'html.parser')  # Retourne l'objet BeautifulSoup directement
    else:
        print("Seul le POST est pris en charge actuellement.")
        return None

def open_fullscreen_window(url):
    # Crée une fenêtre avec l'URL spécifiée
    webview.create_window("Kibriv Streaming", url, fullscreen=True)
    # Lance la fenêtre
    webview.start()




######## MENU pour voir comment sont appeler les différents scripts #######
def ShowResults(ListOfOcurences, SearchedTag, NameOfSearchedFilm=None):
    """Affiche les résultats trouvés avec le tag spécifié."""
    if (ListOfOcurences == []):
        print(f"\n{FailMessage}Aucun résultat pour le tag : {SearchedTag} trouvé dans le code de la page...{Fore.RESET}")
        print(f"\n{WarnigMessage}Veuillez vérifier l'orthographe de votre recherche : {SearchedTag}, si elle est valide cela signifie certainement que Kibriv ne l'a pas sur son site !")
    else:
        print(f"{SuccesMessage}Résultats récupérés avec succès !")
        print(f"Voici la liste des noms de films contenant votre recherche : {WarnigMessage}{SearchedTag}{Fore.RESET}: ")

        align_column = 60

        for item in ListOfOcurences:
            title = item[0] if item[0] else f"{WarnigMessage}///{Fore.RESET}"
            href = item[1] if item[1] else 'None'
            formatted_title = title.ljust(align_column)
            if NameOfSearchedFilm and NameOfSearchedFilm.lower() in title.lower():
                print(f"[{SuccesMessage}*{Fore.RESET}]{Back.YELLOW}{formatted_title} ===== {href}{Back.RESET}")
            else:
                print(f"[{SuccesMessage}*{Fore.RESET}]{formatted_title} ===== {href}")

def FindAllLinksOrSources(SearchedTag, Html):
    """Trouve toutes les occurrences d'un tag spécifique et leurs liens ou sources."""
    Occurences = []
    specific_tags = Html.find_all(SearchedTag)

    for tag in specific_tags:
        clean_text = re.sub(r'\s+', ' ', tag.get_text()).strip()
        href = tag.get('href')
        src = tag.get('src')

        # Concaténer l'URL de base si nécessaire
        if src and src.startswith('/'):
            src = f"{baseUrl}{src[1:]}"
            
        if href and href.startswith('/'):
            href = f"{baseUrl}{href[1:]}"

        if href:
            Occurences.append((clean_text, href))
        elif src:
            Occurences.append((clean_text, src))
        else:
            Occurences.append((clean_text, None))

    return Occurences, SearchedTag

"""
def Menu():

    console = Console()

    # Créer un menu avec un panneau (Panel)
    menu_title = "Menu Principal"
    menu_options = [
        "1. Cherchez le lien d'un film",
        "2. Trouver le lien du lecteur vidéo (si vous avez le lien complet du film ! )",
        "3. Télécharger le fichier vidéo à partir du lien kibriv.com",
        "4. Quitter",
    ]
    console.print(Panel(Text(menu_title, style="bold green"), expand=False))

    # Afficher les options du menu
    for option in menu_options:
        console.print(option)


    # Obtenir la sélection de l'utilisateur
    choice = Prompt.ask("\nChoisissez une option : ", choices=["1", "2", "3", "4"])

    # Traitement en fonction du choix de l'utilisateur
    if choice == "1":
        console.print("Vous avez choisi l'Option 1", style="bold yellow")
        Searchword = Prompt.ask("Entrez le nom du film que vous cherchez")
        ResearchResponse = ResearchFilm(Searchword)
        if ResearchResponse:
            occurences, SearchedTag = FindAllOccurencesOfTag("a", ResearchResponse, NameOfSearchedFilm=Searchword)
            ShowResults(occurences, SearchedTag, Searchword)
        else:
            print(f"{FailMessage}Erreur lors de la recherche du film.")

        print()
        input(f"{Back.CYAN}Appuyez sur Entrée pour revenir au menu...{Back.RESET}")  # Attend que l'utilisateur appuie sur Entrée
        
        Menu()

    elif choice == "2":
        console.print("Vous avez choisi l'Option 2", style="bold yellow")
        link = Prompt.ask("Entrez le lien complet de la page du film sur Kibriv (utilisez l'option 1 si vous ne l'avez pas encore)")
        html_content = GetHtmlOfUrl(link)

        if html_content is None:
            exit()

        if html_content:
            soup = BeautifulSoup(html_content, 'html.parser')
            occurences, SearchedTag = FindAllLinksOrSources("iframe", soup)
            ShowResults(occurences, SearchedTag)

            if occurences:
                try:
                    UrlToOpen = occurences[0][1]
                    open_fullscreen_window(UrlToOpen)
                except Exception as e:
                    print(f"Erreur lors de l'ouverture de la fenêtre en plein écran : {e}")
            else:
                print("Aucun résultat pour le tag : iframe trouvé dans le code de la page.")
        else:
            print(f"{FailMessage}Erreur lors de la récupération de la page du film.")
        print()
        input(f"{Back.CYAN}Appuyez sur Entrée pour revenir au menu...{Back.RESET}")  # Attend que l'utilisateur appuie sur Entrée
        
        Menu()

    elif choice == "3":
        console.print("Vous avez choisi l'Option 3", style="bold yellow")
        link = Prompt.ask("Entrez le lien complet de la page du film sur Kibriv (utilisez l'option 1 si vous ne l'avez pas encore)")
        html_content = GetHtmlOfUrl(link)

        if html_content is None:
            exit()

        if html_content:
            soup = BeautifulSoup(html_content, 'html.parser')
            occurences, SearchedTag = FindAllLinksOrSources("iframe", soup)
            ShowResults(occurences, SearchedTag)
            try:
                UrlToDwnld = occurences[0][1]
                download_video(UrlToDwnld)
                print(f"{SuccesMessage}Vidéo téléchargée dans le répertoire courant du script. Bon film ! {Fore.RESET}")
            except IndexError as e:  # Remplacez Exception par le type d'erreur spécifique si vous le connaissez
                print(f"Erreur : {e}")

        else:
            print(f"{FailMessage}Erreur lors de la récupération de la page du film.{Fore.RESET}")
        print()
        input(f"{Back.CYAN}Appuyez sur Entrée pour revenir au menu...{Back.RESET}")  # Attend que l'utilisateur appuie sur Entrée
        Menu()

    elif choice == "4":
        console.print("Vous avez choisi l'Option 4. Quitter le programme.", style="bold red")
        console.print("")
        console.print("Merci d'avoir utilisé mon logiciel ! N'hésitez pas à me contacter pour des idées de fonctionnalités ou pour rapporter des bugs !", style="bold yellow")
        console.print("Mail : Galaxy_Shadow_99@proton.me", style="bold")
        exit()
"""