import requests
from bs4 import BeautifulSoup
import re
from colorama import Fore, Back, Style, init
import os
# UI
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text
#nav web
import webview
#download video 
import yt_dlp
from videodownloader import *
#settings 
import json
import time


# Initialiser Colorama
os.system("clear")
init(autoreset=True)

# Définir les couleurs pour les messages
SuccesMessage = Fore.GREEN
FailMessage = Fore.RED
WarnigMessage = Fore.YELLOW

baseUrl = "https://kibriv.com/"
homeUrl = "https://kibriv.com/g3fco29kz6y/home/kibriv"

def GetHtmlOfUrl(url):   
    """Récupère le contenu HTML de l'URL spécifiée."""
    long_url = url
    
    # Vérifier si l'URL est valide et complète
    if not long_url.startswith("https://"):
        print(f"{FailMessage}URL non valide, merci de réessayer ! {Fore.RESET}")
        return None
    
    try:
        response = requests.get(long_url)  # Utilisation de long_url
        if response.status_code == 200:
            HtmlContent = response.text
            print("Contenu HTML récupéré avec succès!")
            return HtmlContent
        else:
            print(f"{FailMessage}Erreur lors de la requête: {response.status_code}{Fore.RESET}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"{FailMessage}Erreur de requête : {e}")
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
        if clean_text == "" or clean_text.lower() == "</br>":
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

def FindDivWithSpecificClass(DivTag, DivClassToFind, Html):
    """Trouve toutes les occurrences d'un div avec une classe spécifique."""
    Occurences = []
    specific_divs = Html.find_all(DivTag, class_=DivClassToFind)

    for DivsFound in specific_divs:
        clean_div_text = re.sub(r'\s+', ' ', DivsFound.get_text()).strip()
        href = DivsFound.get('href')
        src = DivsFound.get('src')

        if src and src.startswith('/'):
            src = f"{baseUrl}{src[1:]}"
            
        if href and href.startswith('/'):
            href = f"{baseUrl}{href[1:]}"

        if href:
            Occurences.append((clean_div_text, href))
        elif src:
            Occurences.append((clean_div_text, src))
        else:
            Occurences.append((clean_div_text, None))

    if not specific_divs:
        print(f"\nAucune {DivTag} avec la classe '{DivClassToFind}' trouvée.")

    return Occurences, DivClassToFind

def SubmitForm(form_url, data):
    """Soumet un formulaire à l'URL spécifiée avec les données fournies."""
    try:
        response = requests.post(form_url, data=data)
        if response.status_code == 200:
            print(f"{SuccesMessage}Recherche soumise avec succès !")
            with open("response.html", "w", encoding="utf-8") as file:
                file.write(response.text)
            print(f"{SuccesMessage}Le HTML a été sauvegardé dans 'response.html'.")
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

def IsOccurencesListEmpty(ListOfOcurences):
    isEmpty = True
    for elt in ListOfOcurences:
        if elt[1] or elt[0]:
            isEmpty = False
            break
    return isEmpty

def ShowResults(ListOfOcurences, SearchedTag, NameOfSearchedFilm=None):
    """Affiche les résultats trouvés avec le tag spécifié."""
    if IsOccurencesListEmpty(ListOfOcurences):
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

def open_fullscreen_window(url):
    # Crée une fenêtre avec l'URL spécifiée
    webview.create_window("Kibriv Streaming", url, fullscreen=True)
    # Lance la fenêtre
    webview.start()
    
def updateJsonSetting(key, value):
    try:
        # Lire le contenu actuel du fichier
        with open('settings.json', 'r') as file:
            settings = json.load(file)
        
        # Mettre à jour la valeur du paramètre
        settings[key] = value
        
        # Écrire les nouvelles données dans le fichier
        with open('settings.json', 'w') as file:
            json.dump(settings, file, indent=4)
    
    except FileNotFoundError:
        print("Le fichier settings.json n'existe pas. Veuillez d'abord le créer.")
    except json.JSONDecodeError:
        print("Erreur lors de la lecture du fichier JSON. Le format est peut-être incorrect.")
 

           
def Menu():
    time.sleep(7)
    print(f"")
    os.system("clear")
        
    defaultSettings = {"IgnoreReco" : True , "numberOfUse" : 0}
    try:
        with open('settings.json', 'r') as file:
            settings = json.load(file)
            
    except FileNotFoundError:
        with open('settings.json', 'w') as file:
            json.dump(defaultSettings, file, indent=4)  # indent=4 pour une mise en forme lisible
    except json.JSONDecodeError:
        print("Erreur lors de la lecture du fichier JSON. Le format est peut-être incorrect.")
        settings = defaultSettings
    
    console = Console()

    # Créer un menu avec un panneau (Panel)
    menu_title = "Menu Principal"
    menu_options = [
        "1. Cherchez le lien d'un film",
        "2. Trouver le lien du lecteur vidéo (si vous avez le lien complet du film ! )",
        "3. Télécharger le fichier vidéo à partir du lien kibriv.com",
        "4. Quitter",
    ]
    console.print(Panel(Text(menu_title, style="bold green"), expand=True))
    
    # Afficher les options du menu
    for option in menu_options:
        console.print(option)

    # Afficher le titre du menu dans un panneau
    if settings["IgnoreReco"]==False:

        console.print(Panel(Text("Recommandations before using script ! ", style="bold Yellow"),expand=False))
        
        # Liste des recommandations avec des couleurs de fond
        recommandations = [
            f"{Back.LIGHTYELLOW_EX}{Fore.BLACK}Because of the non exactly legal website the script is scrapping (exacting informations of the web page){Fore.RESET}{Back.RESET}",
            f"{Back.RED}The author of the script declines all responsibility if you get into trouble with any laws of any country, you're using my tool at your own risk! {Back.RESET}",
            f"{Back.GREEN}It is strongly recommended to use a VPN {Back.RESET}to hide your IP address from your ISP. {Back.GREEN}I recommend ProtonVPN {Back.RESET}(the only good free VPN nowadays) -> https://protonvpn.com/ ",
            f"{Fore.GREEN}Happy Streaming!{Style.RESET_ALL}"
        ]


        # Affichage des recommandations
        for recommandation in recommandations:
            print(recommandation)
        
        #affichera seulement une fois les avertissement 
        updateJsonSetting("IgnoreReco",True)
       
    
    
    # Obtenir la sélection de l'utilisateur
    choice = Prompt.ask("\nChoisissez une option : ", choices=["1", "2", "3","4"])

    # Traitement en fonction du choix de l'utilisateur
    if choice == "1":
        console.print("Vous avez choisi l'Option 1", style="bold yellow")
        Searchword = Prompt.ask("Entrez le nom du film que vous cherchez")
        ResearchResponse = ResearchFilm(Searchword)
        if ResearchResponse:  # Vérification si la réponse n'est pas None
            occurences, SearchedTag = FindAllOccurencesOfTag("a", ResearchResponse, NameOfSearchedFilm=Searchword)
            ShowResults(occurences, SearchedTag, Searchword)
        else:
            print(f"{FailMessage}Erreur lors de la recherche du film.")
        
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
            
            # Ouvre le lien en plein écran
            
            UrlToOpen = occurences[0][1]  
            open_fullscreen_window(UrlToOpen)
        else:
            print(f"{FailMessage}Erreur lors de la récupération de la page du film.")
            #open the link in a full screen windows
        
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
            
            # Ouvre le lien en plein écran
            
            UrlToDwnld = occurences[0][1]  
            download_video(UrlToDwnld)
            print(f"{SuccesMessage}Vidéo téléchargée dans le répertoire courant du script, Bon film ! {Fore.RESET}")
        else:
            print(f"{FailMessage}Erreur lors de la récupération de la page du film.{Fore.RESET}")
            #open the link in a full screen windows
        
        Menu()
    
    elif choice == "4":
        console.print("Vous avez choisi l'Option 4. Quitter le programme.", style="bold red")
        console.print("")
        console.print("Merci d'avoir utilisé mon logiciel n'hésitez pas à me contacter si vous avez des idées de features ou pour me rapporter des bugs ! ", style="bold yellow")
        console.print()
        console.print("Mail : Galaxy_Shadow_99@proton.me ", style="")
        exit()

####### Main program #######
Menu()
