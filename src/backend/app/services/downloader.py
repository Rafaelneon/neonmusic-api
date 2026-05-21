import yt_dlp
import os
from src.backend.app.core.config import settings
from src.backend.app.services.vpn import vpn_service
from pytubefix import YouTube, Playlist

class DownloaderService:
    def __init__(self):
        # Função de filtro para validar a música
        def music_filter(info_dict, *, incomplete):
            duration = info_dict.get('duration')
            if duration:
                if duration < 30:
                    return 'Vídeo muito curto (provavelmente não é música)'
                if duration > 1200:
                    return 'Vídeo muito longo (provavelmente podcast/live)'
            return None

        self.base_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(settings.DOWNLOAD_DIR, '%(id)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320', # Qualidade máxima de MP3
            }],
            'quiet': True,
            'no_warnings': True,
            'nooverwrites': True,
            'continuedl': True,
            'match_filter': music_filter,
            # Melhorias para qualidade e compatibilidade
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'addmetadata': True, # Tenta adicionar metadados ao arquivo final
        }

    def _get_opts(self, progress_hook=None):
        opts = self.base_opts.copy()
        if progress_hook:
            opts['progress_hooks'] = [progress_hook]
        return opts

    def get_info(self, url: str):
        """
        Extrai informações detalhadas de metadados. 
        Suporta Playlists e Álbuns de Spotify, Deezer, SoundCloud, YouTube, etc.
        """
        # Configuração para extração rápida de metadados (sem download)
        extract_opts = {
            'quiet': True,
            'extract_flat': True, # Crucial para playlists: não extrai info de cada vídeo individualmente
            'force_generic_extractor': False,
        }

        try:
            with yt_dlp.YoutubeDL(extract_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Caso 1: É uma Playlist ou Álbum
                if 'entries' in info or info.get('_type') == 'playlist':
                    entries = []
                    for entry in info.get('entries', []):
                        if not entry: continue
                        
                        title = entry.get('title') or entry.get('name')
                        artist = entry.get('artist') or entry.get('uploader')
                        clean_title = f"{artist} - {title}" if artist and title and artist not in title else title
                        
                        entries.append({
                            "id": entry.get("id"),
                            "title": clean_title,
                            "url": entry.get("url") or entry.get("webpage_url"),
                            "duration": entry.get("duration"),
                            "thumbnail": entry.get("thumbnail")
                        })
                    
                    return {
                        "is_playlist": True,
                        "title": info.get("title") or info.get("name") or "Playlist Desconhecida",
                        "entries": entries,
                        "source": info.get("extractor")
                    }
                
                # Caso 2: É uma música/vídeo único
                title = info.get('title')
                artist = info.get('artist') or info.get('uploader')
                clean_title = f"{artist} - {title}" if artist and title and artist not in title else title

                return {
                    "is_playlist": False,
                    "id": info.get("id"),
                    "title": clean_title,
                    "url": url,
                    "duration": info.get("duration"),
                    "thumbnail": info.get("thumbnail"),
                    "source": info.get("extractor")
                }

        except Exception as e:
            if "youtube.com" in url or "youtu.be" in url:
                try:
                    if "list=" in url:
                        pl = Playlist(url)
                        return {
                            "is_playlist": True,
                            "title": pl.title,
                            "entries": [{"id": v.video_id, "title": v.title, "url": v.watch_url, "duration": v.length} for v in pl.videos],
                            "source": "pytubefix_playlist"
                        }
                    else:
                        yt = YouTube(url)
                        return {
                            "is_playlist": False,
                            "id": yt.video_id,
                            "title": yt.title,
                            "url": url,
                            "duration": yt.length,
                            "thumbnail": yt.thumbnail_url,
                            "source": "pytubefix"
                        }
                except:
                    pass
            raise Exception(f"Não foi possível extrair informações desta fonte: {str(e)}")

    def download_by_search(self, query: str, progress_hook=None):
        vpn_service.ensure_connected()
        search_opts = self._get_opts(progress_hook)
        
        # Se for uma URL (ex: Spotify), o yt-dlp já tenta resolver. 
        # Se for texto, adicionamos termos para melhorar a precisão.
        if not query.startswith("http"):
            # A busca agora foca no YouTube Music se possível e adiciona filtros restritivos
            # "topic" ajuda a pegar canais de artistas gerados automaticamente pelo YT
            search_query = f"ytsearch1:{query} official audio"
            # Adicionamos uma preferência por vídeos que tenham "Music" no título ou categoria
            # O yt-dlp não tem um 'prefer-category', então refinamos a query
            search_query += " topic" 
        else:
            search_url = query
            # Se for link do YouTube, tentamos garantir que não seja uma live ou vídeo muito longo
            search_query = query

        with yt_dlp.YoutubeDL(search_opts) as ydl:
            info = ydl.extract_info(search_query, download=True)
            if 'entries' in info:
                info = info['entries'][0]
            
            file_path = ydl.prepare_filename(info)
            file_path = os.path.splitext(file_path)[0] + ".mp3"
            
            return {
                "id": info.get("id"),
                "title": info.get("title"),
                "url": info.get("webpage_url") or query,
                "duration": info.get("duration"),
                "thumbnail": info.get("thumbnail"),
                "file_path": file_path
            }

    def download(self, url: str, progress_hook=None):
        vpn_service.ensure_connected()
        with yt_dlp.YoutubeDL(self._get_opts(progress_hook)) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            file_path = os.path.splitext(file_path)[0] + ".mp3"
            return {
                "id": info.get("id"),
                "title": info.get("title"),
                "url": url,
                "duration": info.get("duration"),
                "thumbnail": info.get("thumbnail"),
                "file_path": file_path
            }

downloader_service = DownloaderService()
