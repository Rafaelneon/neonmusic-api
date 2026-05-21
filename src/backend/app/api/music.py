from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import uuid
from src.backend.app.models.track import get_db, Track, DownloadTask
from src.backend.app.services.downloader import downloader_service
from pydantic import BaseModel

router = APIRouter(tags=["Music Distribution"])

class MusicRequest(BaseModel):
    url: str
    use_search: bool = False

def process_download(task_id: str, url: str, use_search: bool, db_session_factory):
    db = db_session_factory()
    try:
        task = db.query(DownloadTask).filter(DownloadTask.id == task_id).first()
        if not task:
            return
            
        task.status = "downloading"
        db.commit()

        last_progress_update = 0

        def progress_hook(d):
            nonlocal last_progress_update
            if d['status'] == 'downloading':
                p_str = d.get('_percent_str', '0%').replace('%','').strip()
                try:
                    p = int(float(p_str))
                    # Só atualiza o banco se o progresso subiu pelo menos 5%
                    # Isso reduz drasticamente a carga no SQLite
                    if p >= last_progress_update + 5 or p == 100:
                        task.progress = p
                        db.commit()
                        last_progress_update = p
                except:
                    pass

        # Antes de baixar, tenta obter o ID final para uma última checagem de cache
        # (Especialmente útil para buscas)
        final_info = None
        if use_search:
            # Para busca, precisamos extrair o primeiro resultado sem baixar primeiro
            search_query = f"ytsearch1:{url}" if not url.startswith("http") else url
            # Aqui poderíamos otimizar, mas o downloader_service.download_by_search já faz isso
            result = downloader_service.download_by_search(url, progress_hook=progress_hook)
        else:
            result = downloader_service.download(url, progress_hook=progress_hook)

        # Verificar se por algum motivo já temos esse ID no banco (evita duplicar Track)
        new_track = Track(
            id=result["id"],
            title=result["title"],
            url=result["url"],
            duration=result["duration"],
            thumbnail=result["thumbnail"],
            file_path=result["file_path"]
        )
        db.merge(new_track)
        
        task.status = "completed"
        task.progress = 100
        task.track_id = result["id"]
        db.commit()

    except Exception as e:
        if task:
            task.status = "failed"
            task.error_message = str(e)
            db.commit()
    finally:
        db.close()

@router.get("/fm")
@router.get("/music/info")
def get_music_info(url: str = Query(..., description="The URL or search query to extract info from"), db: Session = Depends(get_db)):
    """
    Retorna os dados em ambos os formatos para garantir compatibilidade com o bot Node.js.
    Se não for uma URL válida, tenta buscar.
    """
    try:
        # Tenta extrair info (funciona para URLs)
        info = downloader_service.get_info(url)
        
        # Estrutura de dados unificada
        result_data = {
            "is_playlist": info.get("is_playlist", False),
            "type": "playlist" if info.get("is_playlist") else "track",
            "title": info.get("title", "Desconhecido"),
            "duration": info.get("duration", 0),
            "thumbnail": info.get("thumbnail"),
            "id": info.get("id"),
            "items": info.get("entries", []) if info.get("is_playlist") else []
        }

        return {
            "success": True,
            **result_data,
            "data": result_data
        }
    except Exception as e:
        # Se falhar (como no caso de DRM ou apenas texto), tratamos como busca se não parecer URL
        if not url.startswith("http"):
            return {
                "success": True,
                "type": "track",
                "title": url,
                "url": url,
                "is_search": True,
                "data": {"type": "track", "title": url, "url": url}
            }
        
        error_data = {
            "success": False,
            "error": str(e),
            "is_playlist": False,
            "type": "error",
            "items": []
        }
        return {
            **error_data,
            "data": error_data
        }

@router.post("/music/download")
def download_music(request: MusicRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        # 1. Verificar se já existe uma tarefa em andamento para esta URL exata
        existing_task = db.query(DownloadTask).filter(
            DownloadTask.url == request.url,
            DownloadTask.status.in_(["pending", "downloading"])
        ).first()
        
        if existing_task:
            return {
                "success": True,
                "status": "processing",
                "task_id": existing_task.id,
                "message": "Download já em andamento"
            }

        # 2. Identificar se é uma plataforma com DRM ou busca por texto
        is_drm_platform = any(domain in request.url for domain in ["spotify.com", "deezer.com", "apple.com"])
        force_search = request.use_search or is_drm_platform or not request.url.startswith("http")

        # 3. Lógica de Cache: Tentar encontrar a música antes de iniciar o download
        try:
            search_url = request.url
            # Se não for uma URL, adicionamos o prefixo de busca
            if not request.url.startswith("http"):
                search_url = f"ytsearch1:{request.url} official audio"
            
            target_info = downloader_service.get_info(search_url)
            
            if target_info.get("is_playlist") and target_info.get("entries"):
                if "search" in target_info.get("source", "") or len(target_info["entries"]) == 1:
                    first_entry = target_info["entries"][0]
                    # Busca por ID ou Título + Duração (tolerância de 10 segundos)
                    track = db.query(Track).filter(
                        (Track.id == first_entry.get("id")) | 
                        (
                            (Track.title == first_entry.get("title")) & 
                            (Track.duration.between(first_entry.get("duration", 0) - 10, first_entry.get("duration", 0) + 10))
                        )
                    ).first()
                else:
                    track = None
            else:
                # Busca rigorosa: ID ou (Título AND Duração similar)
                track = db.query(Track).filter(
                    (Track.id == target_info.get("id")) | 
                    (
                        (Track.title == target_info.get("title")) & 
                        (Track.duration.between(target_info.get("duration", 0) - 10, target_info.get("duration", 0) + 10))
                    )
                ).first()

            if track and os.path.exists(track.file_path):
                return {
                    "success": True, 
                    "status": "ready", 
                    "track": {
                        "id": track.id, 
                        "title": track.title, 
                        "stream_url": f"/api/v1/music/stream/{track.id}"
                    }
                }
        except Exception as e:
            # Se falhar a extração de info, seguimos para o download normal
            pass

        # 4. Criar nova tarefa se nada foi encontrado no cache
        task_id = str(uuid.uuid4())
        new_task = DownloadTask(id=task_id, url=request.url, status="pending")
        db.add(new_task)
        db.commit()

        from src.backend.app.models.track import SessionLocal
        background_tasks.add_task(process_download, task_id, request.url, force_search, SessionLocal)

        return {
            "success": True,
            "status": "processing",
            "task_id": task_id
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/music/status/{task_id}")
def get_task_status(task_id: str, db: Session = Depends(get_db)):
    task = db.query(DownloadTask).filter(DownloadTask.id == task_id).first()
    if not task:
        return {"success": False, "error": "Task not found"}
    
    response = {
        "id": task.id,
        "status": task.status,
        "progress": task.progress,
    }
    
    if task.status == "completed":
        response["track_id"] = task.track_id
        response["stream_url"] = f"/api/v1/music/stream/{task.track_id}"
    elif task.status == "failed":
        response["error"] = task.error_message
        
    return {"success": True, "task": response}

@router.get("/music/tracks")
def list_tracks(offset: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """
    Lista todas as músicas baixadas no banco de dados com paginação.
    """
    tracks = db.query(Track).order_by(Track.created_at.desc()).offset(offset).limit(limit).all()
    total = db.query(Track).count()
    
    return {
        "success": True,
        "total": total,
        "offset": offset,
        "limit": limit,
        "tracks": [
            {
                "id": t.id,
                "title": t.title,
                "duration": t.duration,
                "thumbnail": t.thumbnail,
                "url": t.url,
                "stream_url": f"/api/v1/music/stream/{t.id}",
                "created_at": t.created_at
            } for t in tracks
        ]
    }

@router.get("/music/stream/{track_id}")
def stream_music(track_id: str, db: Session = Depends(get_db)):
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track or not os.path.exists(track.file_path):
        raise HTTPException(status_code=404, detail="Track not found")
    return FileResponse(track.file_path, media_type="audio/mpeg", filename=f"{track.id}.mp3")
