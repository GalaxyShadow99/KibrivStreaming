import yt_dlp

def download_video(video_url):
    # Configuration pour télécharger la vidéo avec yt-dlp
    ydl_opts = {
        'format': 'best',  # Télécharge la meilleure qualité disponible
        'outtmpl': '%(title)s.%(ext)s',  # Modèle de nom de fichier
        'quiet': False,  # Affiche les messages de téléchargement
        'noplaylist': True,  # Ne télécharge pas les playlists, seulement les vidéos individuelles
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        print("Téléchargement terminé avec succès.")
    except Exception as e:
        print(f"Erreur lors du téléchargement : {e}")

