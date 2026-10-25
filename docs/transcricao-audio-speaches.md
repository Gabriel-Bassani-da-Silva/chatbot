# Transcrição local de áudio com Speaches

O Speaches executa o faster-whisper localmente e oferece uma API compatível com o formato OpenAI para transcrever áudios. O serviço é separado do Ollama: o Speaches transcreve; o modelo de linguagem do agente recebe o texto resultante.

## Inicialização e GPU

O Speaches inicia junto com a stack padrão usando `make up`; não é mais necessário ativar o perfil `audio`. A imagem usa CUDA, então o host precisa ter GPU NVIDIA e o Docker configurado para disponibilizá-la. Sem esse suporte, o `up` padrão pode falhar. Consulte os pré-requisitos no [README do projeto](https://github.com/Gabriel-Bassani-da-Silva/chatbot/blob/main/README.md).

## Rede, porta e cache

- O n8n acessa o Speaches pela rede Docker dedicada, no endereço `http://speaches:8000`.
- A porta do host é vinculada somente a `127.0.0.1:8000`; ela não é publicada pelo Caddy nem pelo Cloudflare Tunnel.
- Os modelos ficam no volume persistente `speaches_model_cache` e sobrevivem à recriação do container.
- `STT_MODEL_TTL=-1` e `WHISPER__TTL=-1` cobrem os nomes usados no Speaches 0.9+ e 0.8.x, respectivamente. O modelo fica na VRAM depois do primeiro uso; isso não faz preload. O cache em disco permanece se o modelo for descarregado.
- O `healthcheck` consulta `/health` e indica se a API responde; não confirma que um modelo foi carregado nem reinicia sozinho um processo marcado como `unhealthy`.
- Como o modelo permanece na VRAM após o uso, ele compartilha memória da GPU com o Ollama; ajuste o TTL se houver pressão de memória.
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
