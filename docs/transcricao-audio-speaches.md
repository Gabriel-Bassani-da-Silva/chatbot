# Transcrição local de áudio com Speaches

O Speaches executa o faster-whisper localmente e oferece uma API compatível com o formato OpenAI para transcrever áudios. O serviço é separado do Ollama: o Speaches transcreve; o modelo de linguagem do agente recebe o texto resultante.

## Ativar o serviço

O serviço Speaches usa CUDA e fica no perfil opcional `audio`. Assim, a stack principal pode iniciar em computadores sem GPU NVIDIA; a transcrição local só fica disponível quando o perfil for ativado em uma máquina com suporte a GPU NVIDIA no Docker.

```bash
# Linux/macOS: inicia a stack incluindo o serviço Speaches
COMPOSE_PROFILES=audio make up
```

No PowerShell:

```powershell
$env:COMPOSE_PROFILES = "audio"
make up
```

Sem o perfil `audio`, o container Speaches não é iniciado. O restante da stack pode ser iniciado normalmente com `make up`. As etapas para criar e preencher o `.env` estão no [README do projeto](https://github.com/Gabriel-Bassani-da-Silva/chatbot/blob/main/README.md).

## Rede, porta e cache

- O n8n acessa o Speaches pela rede Docker dedicada, no endereço `http://speaches:8000`.
- A porta do host é vinculada somente a `127.0.0.1:8000`; ela não é publicada pelo Caddy nem pelo Cloudflare Tunnel.
- Os modelos ficam no volume persistente `speaches_model_cache` e sobrevivem à recriação do container.
- `STT_MODEL_TTL=300` permite descarregar o modelo da VRAM após cinco minutos sem uso; o cache em disco permanece.
- A imagem CUDA configurada está em [`versions.env`](https://github.com/Gabriel-Bassani-da-Silva/chatbot/blob/main/versions.env). A seleção de GPU requer suporte NVIDIA no ambiente Docker.

## Chamada pelo n8n

Configure um HTTP Request para enviar `POST` a `http://speaches:8000/v1/audio/transcriptions` com corpo `multipart/form-data`:

| Campo | Tipo | Exemplo |
|---|---|---|
| `file` | Arquivo binário do n8n | Propriedade binária `data` |
| `model` | Texto | `Systran/faster-whisper-medium` |
| `language` | Texto | `pt` |

A resposta contém o texto transcrito, por exemplo `{"text":"Olá, gostaria de informações sobre os cursos."}`. Use um modelo multilíngue listado no registry do Speaches; modelos com sufixo `.en` são somente para inglês.

O endpoint e as opções de modelo podem mudar entre versões. Consulte a [documentação da API de transcrição](https://speaches.ai/usage/speech-to-text/) e o [guia de descoberta e cache de modelos](https://speaches.ai/usage/model-discovery/).

## Referências

- [Repositório oficial Speaches](https://github.com/speaches-ai/speaches)
- [Instalação oficial](https://speaches.ai/installation/)
- [Configuração oficial](https://speaches.ai/configuration/)
- [Documentação n8n: envio de arquivo binário em HTTP Request](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/)
