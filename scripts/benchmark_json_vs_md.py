"""
Benchmark Comparativo: RAG com Documentos em JSON vs Documentos em Markdown (.md)
Fatec Bebedouro — Assistente Virtual Multimodal
Autor: Gabriel Bassani da Silva (TCC Big Data no Agronegócio)

Avalia:
1. Granularidade e contagem de Chunks gerados
2. Similaridade de Cosseno (Top-1 e Top-3) em 10 perguntas reais
3. Acurácia de Recuperação (se o trecho recuperado contém a resposta correta)
4. Desempenho e Coerência na geração de respostas via Llama 3.1 8B (Ollama)
5. Tempo de resposta / Latência
"""

import os
import json
import time
import math
import urllib.request
import urllib.error

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_DIR = os.path.join(ROOT_DIR, "base-conhecimento")
OLLAMA_URL = "http://localhost:11434"
EMBED_MODEL = "qwen3-embedding:0.6b"
LLM_MODEL = "llama3.1:latest"

def get_embedding(text: str) -> list:
    url = f"{OLLAMA_URL}/api/embeddings"
    payload = json.dumps({"model": EMBED_MODEL, "prompt": text}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as res:
        data = json.loads(res.read().decode("utf-8"))
        return data.get("embedding", [])

def generate_llm_response(prompt: str, context: str) -> dict:
    url = f"{OLLAMA_URL}/api/generate"
    system_msg = (
        "Você é o ASSISTENTE VIRTUAL da Secretaria Acadêmica da Fatec Bebedouro. "
        "Responda a dúvida do aluno com base estrita no contexto recuperado. "
        "Seja direto, cordial, conciso e use português do Brasil. Não invente informações."
    )
    full_prompt = f"CONTEXTO RECUPERADO:\n{context}\n\nPERGUNTA DO USUÁRIO:\n{prompt}\n\nRESPOSTA DO ASSISTENTE:"
    
    payload = json.dumps({
        "model": LLM_MODEL,
        "prompt": full_prompt,
        "system": system_msg,
        "stream": False,
        "options": {"temperature": 0.2, "top_p": 0.9}
    }).encode("utf-8")
    
    start_t = time.time()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as res:
        data = json.loads(res.read().decode("utf-8"))
        duration = time.time() - start_t
        return {
            "response": data.get("response", "").strip(),
            "duration": duration,
            "eval_count": data.get("eval_count", 0)
        }

def cosine_similarity(v1, v2) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)

# =========================================================================
# 1. CHUNKING DE ARQUIVOS JSON (Algoritmo Oficial do n8n)
# =========================================================================
def to_natural_text(val, indent=0):
    prefix = "  " * indent
    if isinstance(val, str):
        return prefix + val.strip()
    if isinstance(val, (int, float, bool)):
        return prefix + str(val)
    if isinstance(val, dict):
        lines = []
        if "description" in val:
            lines.append(prefix + str(val["description"]).strip())
        for k, v in val.items():
            if k.lower() in ["description", "type", "$schema"]:
                continue
            k_clean = k.replace("_", " ").title()
            if isinstance(v, (str, int, float, bool)):
                lines.append(f"{prefix}• {k_clean}: {v}")
            else:
                lines.append(f"{prefix}• {k_clean}:")
                sub = to_natural_text(v, indent + 1)
                if sub:
                    lines.append(sub)
        return "\n".join(lines)
    if isinstance(val, list):
        lines = []
        for item in val:
            if isinstance(item, (str, int, float, bool)):
                lines.append(f"{prefix}• {item}")
            else:
                sub = to_natural_text(item, indent + 1)
                if sub:
                    lines.append(f"{prefix}•\n{sub}")
        return "\n".join(lines)
    return ""

def load_json_chunks():
    chunks = []
    json_files = [f for f in sorted(os.listdir(KB_DIR)) if f.endswith(".json")]
    for fname in json_files:
        fpath = os.path.join(KB_DIR, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        titulo = data.get("titulo", fname)
        categoria = data.get("categoria", "geral")
        fonte = data.get("fonte", "Fatec Bebedouro")
        resumo = data.get("resumo", "")
        
        # Chunk Resumo
        if resumo:
            text = f"DOCUMENTO: {titulo}\nCATEGORIA: {categoria}\nFONTE: {fonte}\n\nRESUMO INSTITUCIONAL:\n{resumo}"
            chunks.append({
                "source_file": fname,
                "type": "resumo",
                "titulo": titulo,
                "text": text
            })
        
        # Chunks de Dados Estruturados
        dados = data.get("dados_estruturados")
        if isinstance(dados, dict):
            for sec_name, sec_val in dados.items():
                sec_txt = to_natural_text(sec_val)
                if sec_txt:
                    text = f"DOCUMENTO: {titulo}\nTÓPICO / SEÇÃO: {sec_name}\nFONTE: {fonte}\n\nINFORMAÇÕES OFICIAIS:\n{sec_txt}"
                    chunks.append({
                        "source_file": fname,
                        "type": f"secao_{sec_name}",
                        "titulo": titulo,
                        "text": text
                    })
        
        # Chunks de FAQs
        faqs = data.get("perguntas_frequentes", [])
        if isinstance(faqs, list):
            for faq in faqs:
                p = faq.get("pergunta", "")
                r = faq.get("resposta", "")
                kw = ", ".join(faq.get("palavras_chave", [])) if isinstance(faq.get("palavras_chave"), list) else ""
                text = f"DOCUMENTO: {titulo}\nCATEGORIA: {categoria}\nPERGUNTA FREQUENTE: {p}\nRESPOSTA OFICIAL: {r}"
                if kw:
                    text += f"\nPALAVRAS-CHAVE: {kw}"
                chunks.append({
                    "source_file": fname,
                    "type": "faq",
                    "titulo": titulo,
                    "pergunta": p,
                    "text": text
                })
    return chunks

# =========================================================================
# 2. CHUNKING DE ARQUIVOS MARKDOWN (.md) (Divisão por Cabeçalhos e Seções)
# =========================================================================
def load_md_chunks():
    chunks = []
    md_files = [f for f in sorted(os.listdir(KB_DIR)) if f.endswith(".md")]
    for fname in md_files:
        fpath = os.path.join(KB_DIR, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Estratégia padrão de Markdown RAG: divisão por seções (## ou ###)
        sections = content.split("\n## ")
        doc_header = sections[0].strip()
        first_line = doc_header.split("\n")[0] if doc_header else fname
        doc_title = first_line.replace("#", "").strip()

        for sec in sections[1:]:
            lines = sec.strip().split("\n")
            sec_title = lines[0].strip()
            sec_body = "\n".join(lines[1:]).strip()
            
            # Se for FAQ, podemos manter como uma grande seção ou dividir perguntas
            if "perguntas frequentes" in sec_title.lower() or "faq" in sec_title.lower():
                faq_items = sec_body.split("\n### ")
                for item in faq_items:
                    if not item.strip():
                        continue
                    item_lines = item.strip().split("\n")
                    q_title = item_lines[0].replace("###", "").strip()
                    q_body = "\n".join(item_lines[1:]).strip()
                    chunk_text = f"# {doc_title}\n## FAQ: {q_title}\n{q_body}"
                    chunks.append({
                        "source_file": fname,
                        "type": "md_faq",
                        "titulo": doc_title,
                        "text": chunk_text
                    })
            else:
                chunk_text = f"# {doc_title}\n## {sec_title}\n{sec_body}"
                chunks.append({
                    "source_file": fname,
                    "type": "md_secao",
                    "titulo": doc_title,
                    "text": chunk_text
                })
    return chunks

# =========================================================================
# 3. PERGUNTAS DE TESTE (CENÁRIOS REAIS DE ATENDIMENTO NA FATEC)
# =========================================================================
TEST_QUERIES = [
    {
        "id": 1,
        "query": "Como posso convalidar meu estágio no curso de Big Data no Agronegócio?",
        "expected_terms": ["convalidação", "equivalência", "carteira de trabalho", "estágio"],
        "target_file": "convalidacao-big-data-no-agronegocio"
    },
    {
        "id": 2,
        "query": "Quem é o coordenador de estágio de Logística e qual o e-mail de contato?",
        "expected_terms": ["marcos", "estagio", "fatec.sp.gov.br"],
        "target_file": "coordenacao-estagio-logistica"
    },
    {
        "id": 3,
        "query": "Como funciona o TCC do Gabriel Bassani da Silva e quais tecnologias foram usadas?",
        "expected_terms": ["gabriel", "waha", "speaches", "cuda", "ollama", "pgvector"],
        "target_file": "tcc-gabriel-bassani"
    },
    {
        "id": 4,
        "query": "O assistente virtual funciona de final de semana ou tem horário de atendimento?",
        "expected_terms": ["24", "7", "ininterrupto", "sempre disponível"],
        "target_file": "tcc-gabriel-bassani"
    },
    {
        "id": 5,
        "query": "Quais são os documentos necessários para iniciar o estágio obrigatório em Big Data?",
        "expected_terms": ["termo de compromisso", "plano de atividades", "apólice"],
        "target_file": "estagio-big-data-no-agronegocio"
    },
    {
        "id": 6,
        "query": "O que é a CPA (Comissão Própria de Avaliação) e para que serve?",
        "expected_terms": ["autoavaliação", "melhoria", "cps", "participação"],
        "target_file": "comissao-propria-de-avaliacao-cpa"
    },
    {
        "id": 7,
        "query": "Qual o e-mail oficial da Secretaria Acadêmica da Fatec Bebedouro?",
        "expected_terms": ["secretaria", "f280acad@cps.sp.gov.br", "fatec.sp.gov.br"],
        "target_file": "diretoria-academica"
    },
    {
        "id": 8,
        "query": "Como acessar o acervo digital e livros da Biblioteca Central via BiblioCPS?",
        "expected_terms": ["bibliocps", "acervo", "empréstimo", "digital"],
        "target_file": "biblioteca-links-oficiais"
    },
    {
        "id": 9,
        "query": "Quais as disciplinas da grade curricular de Big Data no Agronegócio?",
        "expected_terms": ["algoritmos", "dados", "estatística", "agronegócio"],
        "target_file": "grade-big-data-no-agronegocio"
    },
    {
        "id": 10,
        "query": "Como solicitar trancamento de matrícula ou atestado de matrícula?",
        "expected_terms": ["siga", "secretaria", "requerimento", "prazo"],
        "target_file": "area-do-aluno"
    }
]

def run_benchmark():
    print("=" * 75)
    print("INICIANDO BENCHMARK: RAG EM JSON vs RAG EM MARKDOWN (.md)")
    print(f"Modelo Embeddings: {EMBED_MODEL} | Modelo LLM: {LLM_MODEL}")
    print("=" * 75)

    print("\n[1/4] Carregando e fatiando documentos...")
    json_chunks = load_json_chunks()
    md_chunks = load_md_chunks()
    print(f" -> Chunks gerados a partir do JSON : {len(json_chunks)} chunks")
    print(f" -> Chunks gerados a partir do MD   : {len(md_chunks)} chunks")

    print("\n[2/4] Gerando embeddings para os chunks (cache vetorial em memória)...")
    # Gerar embeddings para JSON
    start_emb_json = time.time()
    for i, c in enumerate(json_chunks):
        c["emb"] = get_embedding(c["text"])
        if (i + 1) % 50 == 0 or (i + 1) == len(json_chunks):
            print(f"   [JSON] Vetorizados {i+1}/{len(json_chunks)}...")
    t_emb_json = time.time() - start_emb_json

    # Gerar embeddings para MD
    start_emb_md = time.time()
    for i, c in enumerate(md_chunks):
        c["emb"] = get_embedding(c["text"])
        if (i + 1) % 50 == 0 or (i + 1) == len(md_chunks):
            print(f"   [MD] Vetorizados {i+1}/{len(md_chunks)}...")
    t_emb_md = time.time() - start_emb_md

    print(f"\nTempo de indexação: JSON = {t_emb_json:.2f}s | MD = {t_emb_md:.2f}s")

    print("\n[3/4] Executando 10 testes de busca semântica e geração com Llama 3.1...")
    results = []

    for q in TEST_QUERIES:
        qid = q["id"]
        query_text = q["query"]
        target = q["target_file"]
        expected = q["expected_terms"]

        q_emb = get_embedding(query_text)

        # 1. Ranking JSON
        scored_json = []
        for c in json_chunks:
            sim = cosine_similarity(q_emb, c["emb"])
            scored_json.append((sim, c))
        scored_json.sort(key=lambda x: x[0], reverse=True)
        top_json = scored_json[:3]

        # 2. Ranking MD
        scored_md = []
        for c in md_chunks:
            sim = cosine_similarity(q_emb, c["emb"])
            scored_md.append((sim, c))
        scored_md.sort(key=lambda x: x[0], reverse=True)
        top_md = scored_md[:3]

        # Validação de acerto no Top-1 e Top-3
        json_top1_hit = target in top_json[0][1]["source_file"]
        md_top1_hit = target in top_md[0][1]["source_file"]

        json_top3_hit = any(target in x[1]["source_file"] for x in top_json)
        md_top3_hit = any(target in x[1]["source_file"] for x in top_md)

        # Contexto montado para o LLM
        json_context = "\n---\n".join([x[1]["text"] for x in top_json])
        md_context = "\n---\n".join([x[1]["text"] for x in top_md])

        # Geração LLM com JSON
        llm_json = generate_llm_response(query_text, json_context)
        # Geração LLM com MD
        llm_md = generate_llm_response(query_text, md_context)

        # Checagem de termos esperados na resposta do LLM
        json_ans = llm_json["response"].lower()
        md_ans = llm_md["response"].lower()
        json_terms_found = sum(1 for t in expected if t in json_ans)
        md_terms_found = sum(1 for t in expected if t in md_ans)

        res_entry = {
            "id": qid,
            "query": query_text,
            "target": target,
            "json": {
                "top1_sim": top_json[0][0],
                "top3_avg_sim": sum(x[0] for x in top_json) / 3,
                "top1_hit": json_top1_hit,
                "top3_hit": json_top3_hit,
                "top1_file": top_json[0][1]["source_file"],
                "terms_found": f"{json_terms_found}/{len(expected)}",
                "llm_time": llm_json["duration"],
                "eval_count": llm_json["eval_count"],
                "response": llm_json["response"]
            },
            "md": {
                "top1_sim": top_md[0][0],
                "top3_avg_sim": sum(x[0] for x in top_md) / 3,
                "top1_hit": md_top1_hit,
                "top3_hit": md_top3_hit,
                "top1_file": top_md[0][1]["source_file"],
                "terms_found": f"{md_terms_found}/{len(expected)}",
                "llm_time": llm_md["duration"],
                "eval_count": llm_md["eval_count"],
                "response": llm_md["response"]
            }
        }
        results.append(res_entry)
        print(f" -> Q{qid:02d} processada: Top1 Sim (JSON={top_json[0][0]:.3f} vs MD={top_md[0][0]:.3f})")

    # =========================================================================
    # 4. CONSOLIDAÇÃO ESTATÍSTICA
    # =========================================================================
    print("\n" + "=" * 75)
    print("RELATÓRIO COMPARATIVO FINAL: JSON vs MARKDOWN")
    print("=" * 75)

    avg_sim_json = sum(r["json"]["top1_sim"] for r in results) / len(results)
    avg_sim_md = sum(r["md"]["top1_sim"] for r in results) / len(results)

    top1_acc_json = sum(1 for r in results if r["json"]["top1_hit"]) / len(results) * 100
    top1_acc_md = sum(1 for r in results if r["md"]["top1_hit"]) / len(results) * 100

    top3_acc_json = sum(1 for r in results if r["json"]["top3_hit"]) / len(results) * 100
    top3_acc_md = sum(1 for r in results if r["md"]["top3_hit"]) / len(results) * 100

    avg_llm_time_json = sum(r["json"]["llm_time"] for r in results) / len(results)
    avg_llm_time_md = sum(r["md"]["llm_time"] for r in results) / len(results)

    avg_tokens_json = sum(r["json"]["eval_count"] for r in results) / len(results)
    avg_tokens_md = sum(r["md"]["eval_count"] for r in results) / len(results)

    print(f"{'Métrica':<35} | {'Base JSON':<18} | {'Base Markdown (.md)':<18}")
    print("-" * 75)
    print(f"{'Total de Chunks Criados':<35} | {len(json_chunks):<18} | {len(md_chunks):<18}")
    print(f"{'Similaridade Média Top-1 (Cosseno)':<35} | {avg_sim_json:.4f}{'':<12} | {avg_sim_md:.4f}{'':<12}")
    print(f"{'Precisão de Recuperação Top-1':<35} | {top1_acc_json:.1f}%{'':<13} | {top1_acc_md:.1f}%{'':<13}")
    print(f"{'Recall de Recuperação Top-3':<35} | {top3_acc_json:.1f}%{'':<13} | {top3_acc_md:.1f}%{'':<13}")
    print(f"{'Tempo Médio de Resposta LLM':<35} | {avg_llm_time_json:.2f}s{'':<13} | {avg_llm_time_md:.2f}s{'':<13}")
    print(f"{'Tokens Médios Gerados':<35} | {avg_tokens_json:.1f}{'':<14} | {avg_tokens_md:.1f}{'':<14}")
    print("-" * 75)

    # Gravar em arquivo scratch/benchmark_results.json
    os.makedirs(os.path.join(ROOT_DIR, "scratch"), exist_ok=True)
    report_file = os.path.join(ROOT_DIR, "scratch", "benchmark_results.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump({
            "metrics": {
                "json_chunks": len(json_chunks),
                "md_chunks": len(md_chunks),
                "avg_sim_top1_json": avg_sim_json,
                "avg_sim_top1_md": avg_sim_md,
                "top1_acc_json": top1_acc_json,
                "top1_acc_md": top1_acc_md,
                "top3_acc_json": top3_acc_json,
                "top3_acc_md": top3_acc_md,
                "avg_llm_time_json": avg_llm_time_json,
                "avg_llm_time_md": avg_llm_time_md
            },
            "queries": results
        }, f, ensure_ascii=False, indent=2)

    print(f"\nResultados detalhados gravados em: {report_file}")

if __name__ == "__main__":
    run_benchmark()
