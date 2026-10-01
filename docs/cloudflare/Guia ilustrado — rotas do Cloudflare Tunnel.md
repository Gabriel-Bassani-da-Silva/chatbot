# Guia ilustrado — rotas do Cloudflare Tunnel

**Projeto:** n8n self-hosted em Docker Compose  
**Domínio público:** `${DOMAIN}`
**Nome do Tunnel:** `${TUNNEL_NAME}`
**Origem no Tunnel:** `http://caddy:80`  
**Revisado:** 29/09/2026

> **Sobre os prints:** as imagens abaixo são quadros da demonstração oficial da interface atual do Cloudflare, publicada em 2026. Elas mostram uma conta e domínios de exemplo — **não são capturas da sua conta**. Este guia descreve um template. Confira no painel real o nome, o estado e as rotas do Tunnel antes de alterar uma instalação.

## O que esta rota faz

O Tunnel leva o tráfego público até o Caddy na rede Docker. O Caddy continua responsável por reconhecer o hostname e encaminhar a requisição ao serviço correto. Para o Chatwoot, o caminho é:

`navegador → Cloudflare → Tunnel ${TUNNEL_NAME} → http://caddy:80 → regra do Caddy → Chatwoot`

> Adicionar uma rota no Cloudflare não cria uma regra no `Caddyfile`, não inicia containers e não altera o Docker Compose. Para um hostname novo, confirme separadamente que o Caddy e o serviço de destino já estão preparados.

## 1. Abra a lista de Tunnels

1. Entre no [Cloudflare Dashboard](https://dash.cloudflare.com/).
2. No menu lateral, abra **Networking → Tunnels**. Use o painel principal da Cloudflare; a navegação antiga por **Zero Trust → Networks** pode aparecer em outras áreas, mas não é o caminho usado neste guia.
3. Localize `${TUNNEL_NAME}` e confira o estado **Healthy** antes de continuar. Não crie outro Tunnel para adicionar somente um hostname.

![Lista de Tunnels na interface atual do Cloudflare](https://private-us-east-1.manuscdn.com/sessionFile/kMMuWAxPT65hqrCvqj80aB/sandbox/Shbmk0qifHLcOUOf7RXCAO-images_1790700113801_na1fn_L2hvbWUvdWJ1bnR1L3Byb2plY3RzL244bi03MjAyNjU1Mi9jbG91ZGZsYXJlLXR1bm5lbC1hc3NldHMvMDEtdHVubmVscy1saXN0LW9mZmljaWFsLXJlZmVyZW5jZQ.png?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9wcml2YXRlLXVzLWVhc3QtMS5tYW51c2Nkbi5jb20vc2Vzc2lvbkZpbGUva01NdVdBeFBUNjVocXJDdnFqODBhQi9zYW5kYm94L1NoYm1rMHFpZkhMY09VT2Y3UlhDQU8taW1hZ2VzXzE3OTA3MDAxMTM4MDFfbmExZm5fTDJodmJXVXZkV0oxYm5SMUwzQnliMnBsWTNSekwyNDRiaTAzTWpBeU5qVTFNaTlqYkc5MVpHWnNZWEpsTFhSMWJtNWxiQzFoYzNObGRITXZNREV0ZEhWdWJtVnNjeTFzYVhOMExXOW1abWxqYVdGc0xYSmxabVZ5Wlc1alpRLnBuZyIsIkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTc5MjAyMjQwMH19fV19&Key-Pair-Id=K2QY5QTL8JSY6C&Signature=MEUCIQCOiytPwBVd50E4j9reA63dygvNc3GNALQMC4GGkZ0sZQIgWx1RfTmxC-GWbMLlBFJ7sRt4pKrOnUfBf-4z6lkX-Jo_)

> **Print 1 — Lista de Tunnels (demonstração oficial).** Na sua conta, procure a linha `${TUNNEL_NAME}` e confirme o estado Healthy. Os nomes exibidos na captura são exemplos.

## 2. Abra o Tunnel e confira as rotas existentes

1. Clique no nome `${TUNNEL_NAME}`.
2. Na página do Tunnel, abra a aba **Routes**.
3. Para o template, use o mapa abaixo. Substitua `${DOMAIN}` pelo valor definido no `.env` da instalação:

| Ordem | Hostname público | Tipo | Serviço |
|---:|---|---|---|
| 1 | `${DOMAIN}` | Published application | `http://caddy:80` |
| 2 | `n8n.${DOMAIN}` | Published application | `http://caddy:80` |
| 3 | `chatwoot.${DOMAIN}` | Published application | `http://caddy:80` |

No template, `${DOMAIN}` serve o portal, `n8n.${DOMAIN}` serve o editor e os webhooks, e `chatwoot.${DOMAIN}` serve o Chatwoot. As três rotas apontam para `http://caddy:80`; o Caddy escolhe o serviço pelo hostname. O repositório é um exemplo, não confirma a configuração do Tunnel real.

![Visão geral do Tunnel com estado e mapa de rotas](https://private-us-east-1.manuscdn.com/sessionFile/kMMuWAxPT65hqrCvqj80aB/sandbox/Shbmk0qifHLcOUOf7RXCAO-images_1790700113801_na1fn_L2hvbWUvdWJ1bnR1L3Byb2plY3RzL244bi03MjAyNjU1Mi9jbG91ZGZsYXJlLXR1bm5lbC1hc3NldHMvMDItdHVubmVsLW92ZXJ2aWV3LW9mZmljaWFsLXJlZmVyZW5jZQ.png?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9wcml2YXRlLXVzLWVhc3QtMS5tYW51c2Nkbi5jb20vc2Vzc2lvbkZpbGUva01NdVdBeFBUNjVocXJDdnFqODBhQi9zYW5kYm94L1NoYm1rMHFpZkhMY09VT2Y3UlhDQU8taW1hZ2VzXzE3OTA3MDAxMTM4MDFfbmExZm5fTDJodmJXVXZkV0oxYm5SMUwzQnliMnBsWTNSekwyNDRiaTAzTWpBeU5qVTFNaTlqYkc5MVpHWnNZWEpsTFhSMWJtNWxiQzFoYzNObGRITXZNREl0ZEhWdWJtVnNMVzkyWlhKMmFXVjNMVzltWm1samFXRnNMWEpsWm1WeVpXNWpaUS5wbmciLCJDb25kaXRpb24iOnsiRGF0ZUxlc3NUaGFuIjp7IkFXUzpFcG9jaFRpbWUiOjE3OTIwMjI0MDB9fX1dfQ__&Key-Pair-Id=K2QY5QTL8JSY6C&Signature=MEQCICmTKic9crRcSBXEGCbB4ul-NAFotETAq7t5YRQhP9pBAiALPZIJONxGlmuQgcw26qeboJbuF5mtYl2qW3XUtI8PbQ__)

> **Print 2 — Visão geral do Tunnel (demonstração oficial).** A tela mostra o estado do Tunnel e as abas **Overview** e **Routes**. Os dados da captura pertencem à demonstração; use os valores da tabela deste guia.

## 3. Inicie a criação de uma rota pública

1. Na aba **Routes**, clique em **Add route**. A interface também pode oferecer esse botão dentro do mapa visual de rotas.
2. Selecione **Published application** — não escolha uma rota de rede privada.

![Mapa de rotas e botão Add route](https://private-us-east-1.manuscdn.com/sessionFile/kMMuWAxPT65hqrCvqj80aB/sandbox/Shbmk0qifHLcOUOf7RXCAO-images_1790700113801_na1fn_L2hvbWUvdWJ1bnR1L3Byb2plY3RzL244bi03MjAyNjU1Mi9jbG91ZGZsYXJlLXR1bm5lbC1hc3NldHMvMDMtcm91dGUtbWFwLWFkZC1yb3V0ZS1vZmZpY2lhbC1yZWZlcmVuY2U.png?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9wcml2YXRlLXVzLWVhc3QtMS5tYW51c2Nkbi5jb20vc2Vzc2lvbkZpbGUva01NdVdBeFBUNjVocXJDdnFqODBhQi9zYW5kYm94L1NoYm1rMHFpZkhMY09VT2Y3UlhDQU8taW1hZ2VzXzE3OTA3MDAxMTM4MDFfbmExZm5fTDJodmJXVXZkV0oxYm5SMUwzQnliMnBsWTNSekwyNDRiaTAzTWpBeU5qVTFNaTlqYkc5MVpHWnNZWEpsTFhSMWJtNWxiQzFoYzNObGRITXZNRE10Y205MWRHVXRiV0Z3TFdGa1pDMXliM1YwWlMxdlptWnBZMmxoYkMxeVpXWmxjbVZ1WTJVLnBuZyIsIkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTc5MjAyMjQwMH19fV19&Key-Pair-Id=K2QY5QTL8JSY6C&Signature=MEQCIHxLEdq3DLuC9WQGmq1SBEh7IPKu3F9WX1o94myvzCVYAiAbSt3K3Hxu96xLSTG7b-G7TmvlU8JxZVFYtdIV2LsxTA__)

> **Print 3 — Botão Add route (demonstração oficial).** Na conta do projeto, o botão fica na página de rotas do Tunnel ativo.

## 4. Preencha o hostname e o destino

No template, configure a rota do Chatwoot assim:

| Campo no Cloudflare | Valor do template |
|---|---|
| **Subdomain** | `chatwoot` |
| **Domain** | `${DOMAIN}` — selecione o domínio no menu |
| **Hostname completo** | Deve aparecer `chatwoot.${DOMAIN}` |
| **Path** | Deixe em branco para encaminhar o site todo |
| **Service URL** | `http://caddy:80` |

Na interface atual, **Service URL** é um único campo: inclua `http://` e a porta. Se a sua tela mostrar os campos separados **Type** e **URL**, escolha `HTTP` e informe `caddy:80` no endereço.

Não ative **No TLS Verify** para esta origem: o trecho entre `cloudflared` e Caddy é HTTP puro, sem certificado TLS para validar. Deixe as demais configurações adicionais nos valores padrão.

![Formulário oficial Add published application](https://private-us-east-1.manuscdn.com/sessionFile/kMMuWAxPT65hqrCvqj80aB/sandbox/Shbmk0qifHLcOUOf7RXCAO-images_1790700113801_na1fn_L2hvbWUvdWJ1bnR1L3Byb2plY3RzL244bi03MjAyNjU1Mi9jbG91ZGZsYXJlLXR1bm5lbC1hc3NldHMvMDQtYWRkLXB1Ymxpc2hlZC1hcHBsaWNhdGlvbi1vZmZpY2lhbC1yZWZlcmVuY2U.png?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9wcml2YXRlLXVzLWVhc3QtMS5tYW51c2Nkbi5jb20vc2Vzc2lvbkZpbGUva01NdVdBeFBUNjVocXJDdnFqODBhQi9zYW5kYm94L1NoYm1rMHFpZkhMY09VT2Y3UlhDQU8taW1hZ2VzXzE3OTA3MDAxMTM4MDFfbmExZm5fTDJodmJXVXZkV0oxYm5SMUwzQnliMnBsWTNSekwyNDRiaTAzTWpBeU5qVTFNaTlqYkc5MVpHWnNZWEpsTFhSMWJtNWxiQzFoYzNObGRITXZNRFF0WVdSa0xYQjFZbXhwYzJobFpDMWhjSEJzYVdOaGRHbHZiaTF2Wm1acFkybGhiQzF5WldabGNtVnVZMlUucG5nIiwiQ29uZGl0aW9uIjp7IkRhdGVMZXNzVGhhbiI6eyJBV1M6RXBvY2hUaW1lIjoxNzkyMDIyNDAwfX19XX0_&Key-Pair-Id=K2QY5QTL8JSY6C&Signature=MEUCIHYQLP2lfeijJKHhEAC7Ex2qBC3S~OFV9or7OPZOrPzWAiEAz5JgX-fXeYyPMsVGeEi6WLDBqN2f07s3p825E1QTasQ_)

> **Print 4 — Formulário (demonstração oficial).** Os valores visíveis são exemplos. Preencha com a tabela acima e confira o hostname completo antes de salvar.

## 5. Salve e confira o resultado

1. Revise mais uma vez `chatwoot.${DOMAIN}` e `http://caddy:80`.
2. Clique em **Add route**.
3. Aguarde a confirmação do Cloudflare e volte à tabela de rotas. A criação de uma Published application pelo painel configura automaticamente o registro DNS para o Tunnel; não crie um segundo registro manual sem necessidade.
4. Confira as três rotas esperadas no template:

| Hostname público | Serviço |
|---|---|
| `${DOMAIN}` | `http://caddy:80` |
| `n8n.${DOMAIN}` | `http://caddy:80` |
| `chatwoot.${DOMAIN}` | `http://caddy:80` |

![Confirmação de rota adicionada no painel Cloudflare](https://private-us-east-1.manuscdn.com/sessionFile/kMMuWAxPT65hqrCvqj80aB/sandbox/Shbmk0qifHLcOUOf7RXCAO-images_1790700113801_na1fn_L2hvbWUvdWJ1bnR1L3Byb2plY3RzL244bi03MjAyNjU1Mi9jbG91ZGZsYXJlLXR1bm5lbC1hc3NldHMvMDUtcm91dGUtc3VjY2Vzcy1vZmZpY2lhbC1yZWZlcmVuY2U.png?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9wcml2YXRlLXVzLWVhc3QtMS5tYW51c2Nkbi5jb20vc2Vzc2lvbkZpbGUva01NdVdBeFBUNjVocXJDdnFqODBhQi9zYW5kYm94L1NoYm1rMHFpZkhMY09VT2Y3UlhDQU8taW1hZ2VzXzE3OTA3MDAxMTM4MDFfbmExZm5fTDJodmJXVXZkV0oxYm5SMUwzQnliMnBsWTNSekwyNDRiaTAzTWpBeU5qVTFNaTlqYkc5MVpHWnNZWEpsTFhSMWJtNWxiQzFoYzNObGRITXZNRFV0Y205MWRHVXRjM1ZqWTJWemN5MXZabVpwWTJsaGJDMXlaV1psY21WdVkyVS5wbmciLCJDb25kaXRpb24iOnsiRGF0ZUxlc3NUaGFuIjp7IkFXUzpFcG9jaFRpbWUiOjE3OTIwMjI0MDB9fX1dfQ__&Key-Pair-Id=K2QY5QTL8JSY6C&Signature=MEYCIQCQ13uUFksCJrN2c7h0L7B7jMqQUDvVSuLdaqoWqBe-pwIhAO~9lpMVaRZ109-45zx3o1sIr6YEzhaHpWhKBqnvFsqD)

> **Print 5 — Confirmação de sucesso (demonstração oficial).** O exemplo mostra a confirmação e a criação automática de DNS. O hostname e o CNAME da demonstração não são valores do template; use a tabela acima.

### O que o template representa

O Caddy do template roteia `${DOMAIN}` para o portal, `n8n.${DOMAIN}` para o n8n e `chatwoot.${DOMAIN}` para o Chatwoot. A documentação do repositório não confirma que o Tunnel real esteja configurado nem que os serviços estejam ativos; valide esses pontos no ambiente correspondente.

## 6. Editar uma rota existente

1. Acesse **Networking → Tunnels → ${TUNNEL_NAME} → Routes**.
2. Na linha do hostname correto, abra o menu de ações **(•••)**.
3. Selecione **Edit route**.
4. Altere somente o campo necessário. Para este projeto, o destino deve continuar `http://caddy:80`.
5. Salve e confira a linha na tabela. Não edite a rota raiz só para ajustar o backend do Chatwoot: o Caddy faz essa seleção pelo hostname.

Se o objetivo for trocar o container que recebe o tráfego, isso normalmente é uma alteração separada no `Caddyfile`, não no destino do Tunnel.

## 7. Reordenar rotas

Na tabela de rotas, o menu **(•••)** oferece **Move up** e **Move down**. O Cloudflare informa que as rotas são avaliadas de cima para baixo e a primeira correspondência é usada. Reordene somente quando regras puderem coincidir — por exemplo, hostnames ou caminhos sobrepostos. Os três hostnames do template são distintos; reordená-los não muda o destino, salvo se existirem regras sobrepostas na instalação real.

## 8. Remover uma rota

A remoção pode tornar o hostname inacessível. Faça isso apenas quando tiver certeza de que a rota não é usada:

1. Abra o menu **(•••)** na linha exata.
2. Confira o hostname completo antes de selecionar **Delete route**.
3. Antes de remover uma rota, confirme seu uso. No template, `${DOMAIN}` atende o portal e `n8n.${DOMAIN}` atende o editor/webhooks; a instalação real pode ter diferenças.
4. Depois, confirme que as outras rotas continuam na lista e verifique se não ficou um registro DNS antigo sem uso. DNS e configuração do Tunnel são componentes distintos; não apague outros registros por tentativa.

Se não souber a finalidade de uma rota, não a remova: investigue antes.

## 9. Testes e diagnóstico

Teste separadamente `${DOMAIN}`, `n8n.${DOMAIN}` e `chatwoot.${DOMAIN}` somente após confirmar a configuração do Tunnel e dos serviços desta instalação. Interprete a resposta antes de mudar qualquer configuração:

| Resultado | O que verificar primeiro |
|---|---|
| Chatwoot abre ou mostra a tela de login/configuração | O caminho Cloudflare → Tunnel → Caddy → aplicação está respondendo. |
| **502/503** | Estado do container, rede Docker, destino `caddy:80` e logs do Caddy/Cloudflared. |
| **404** | Se o Caddy tem uma regra para o hostname exato. |
| Erro de acesso/autenticação | Se a resposta vem da aplicação ou de uma política Cloudflare; não altere a rota sem identificar a origem. |

A criação de uma rota, por si só, não prova que o serviço esteja saudável. Durante o diagnóstico, não remova nem altere hostnames sem confirmar suas dependências.

## Checklist antes de encerrar

- [ ] Tunnel correto: `${TUNNEL_NAME}`, estado Healthy.
- [ ] Hostnames: `${DOMAIN}`, `n8n.${DOMAIN}` e `chatwoot.${DOMAIN}`.
- [ ] Destino: `http://caddy:80`.
- [ ] As três rotas esperadas apontam para `http://caddy:80`; a configuração real foi conferida.
- [ ] Caminho em branco, salvo se houver uma regra específica por caminho.
- [ ] Regra do hostname existe no `Caddyfile` e o serviço correspondente está ativo.
- [ ] Teste público de cada hostname realizado e resultado interpretado.
- [ ] Nenhum token, arquivo `.env`, credencial ou volume foi incluído em exports/commits.

## Fontes e observação de interface

- [Cloudflare — Create a tunnel (dashboard)](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/get-started/create-remote-tunnel/): sequência atual para adicionar uma Published application.
- [Cloudflare — Routing](https://developers.cloudflare.com/tunnel/concepts/routing/): funcionamento das rotas e do DNS.
- [Cloudflare — changelog da nova tela de Tunnels](https://developers.cloudflare.com/changelog/post/2026-02-20-tunnel-core-dashboard/): origem dos prints oficiais usados neste guia.

Este procedimento cobre somente as rotas públicas do Cloudflare Tunnel. Mudanças em Compose, Caddyfile, PostgreSQL, WAHA, Cloudflare Tunnel, Redis, sandbox ou serviços são alterações operacionais separadas e devem preservar a arquitetura documentada do projeto.
