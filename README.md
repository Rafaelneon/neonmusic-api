# Music Distribution API

API profissional para extração e distribuição de músicas, otimizada para integração com bots em Node.js.

## Estrutura do Projeto

- `src/backend`: API FastAPI robusta para busca e download.
- `data/downloads`: Armazenamento local das músicas baixadas (MP3).
- `database`: SQLite para cache de metadados.

## Requisitos

- Python 3.10+
- FFmpeg (essencial para o processamento de áudio)

## Instalação

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

2. Inicie o servidor:
   ```bash
   python -m src.backend.main
   ```

## Endpoints para o Bot (Node.js)

### 1. Extração de Informações (`/fm` ou `/music/info`)
Extrai metadados sem realizar o download. Útil para comandos de "search" no bot.
- **URL**: `GET /api/v1/fm?url=<VIDEO_URL>`
- **Resposta**:
  ```json
  {
    "success": true,
    "data": {
      "id": "...",
      "title": "...",
      "duration": 120,
      "thumbnail": "..."
    }
  }
  ```

### 2. Download e Processamento
Solicita que a API baixe a música. Se já existir localmente, retorna instantaneamente.
- **URL**: `POST /api/v1/music/download`
- **Body**: `{"url": "..."}`
- **Resposta**: Retorna um `stream_url` que o bot Node.js pode usar para dar play.

### 3. Streaming de Áudio
Endpoint que serve o arquivo MP3 final.
- **URL**: `GET /api/v1/music/stream/<track_id>`
