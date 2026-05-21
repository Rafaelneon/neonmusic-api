# Documentação de Melhorias: Sistema de De-duplicação e Cache de Música

Esta documentação detalha as atualizações implementadas na API para otimizar o processo de download, evitar redundância de dados e melhorar a performance do banco de dados.

## 1. Estratégia de De-duplicação (Pre-download)

Foi implementada uma lógica de "Short-circuit" no endpoint `/music/download` para evitar processamento desnecessário.

### 1.1 Verificação de Tarefas Ativas
Antes de qualquer ação, a API verifica se a URL solicitada já possui uma tarefa com status `pending` ou `downloading`.
- **Benefício:** Evita múltiplos processos de download para o mesmo recurso simultaneamente, economizando banda e CPU.

### 1.2 Cache por Identificador e Metadados
O sistema agora realiza uma extração rápida de metadados antes de iniciar o download:
- **Busca por ID:** Verifica se o ID único da plataforma (ex: YouTube ID) já existe no banco.
- **Busca por Título:** Se for um link de DRM (Spotify/Deezer) ou busca por texto, o sistema resolve a busca e compara o título resultante com as músicas já baixadas.
- **Validação Física:** O cache só é retornado se o registro existir no banco **e** o arquivo `.mp3` estiver presente no disco.

## 2. Otimização de Performance do Banco de Dados

### 2.1 Throttling de Progresso
Anteriormente, cada atualização de progresso do `yt-dlp` gerava uma escrita no SQLite. Em conexões rápidas, isso causava concorrência excessiva.
- **Mudança:** O progresso agora só é persistido no banco de dados se houver um incremento de no mínimo **5%** em relação à última atualização ou se o download atingir 100%.
- **Resultado:** Redução de até 90% nas operações de escrita durante o download.

### 2.2 Modo WAL (Write-Ahead Logging)
Confirmada a configuração do SQLite para modo WAL, permitindo que leituras não sejam bloqueadas por escritas, essencial para uma API assíncrona.

## 3. Resiliência do Downloader (`yt-dlp`)

Foram adicionadas flags de segurança ao serviço de download:
- `nooverwrites: True`: Impede que o sistema sobrescreva arquivos caso haja colisão de nomes não detectada pelo banco.
- `continuedl: True`: Permite retomar downloads interrompidos em caso de falha na conexão ou reinicialização do servidor.

## 4. Fluxo de Decisão (Diagrama Lógico)

1. **Requisição Recebida**
2. **Tarefa em andamento para esta URL?**
   - Sim: Retorna `task_id` existente.
3. **Extrair metadados (ID/Título)**
4. **Música já existe no Banco + Disco?**
   - Sim: Retorna `stream_url` imediatamente (`status: ready`).
5. **Novo Download iniciado em Background**
   - Atualização de progresso otimizada (Step: 5%).
   - Finalização: Merge de metadados no banco.

---
*Documentação gerada em 21 de Maio de 2026.*
