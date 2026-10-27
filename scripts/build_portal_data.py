"""
Script para consolidar a base de conhecimento para o Portal Web.
Lê os arquivos JSON de base-conhecimento/, gera a representação Markdown rica sob demanda
e grava public/data/kb-full.json e public/kb-data.js para visualização instantânea.
"""

import os
import json
import shutil

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_SRC = os.path.join(ROOT_DIR, "base-conhecimento")
PUBLIC_KB = os.path.join(ROOT_DIR, "public", "base-conhecimento")
PUBLIC_DATA = os.path.join(ROOT_DIR, "public", "data")
PUBLIC_JS_DATA = os.path.join(ROOT_DIR, "public", "kb-data.js")

os.makedirs(PUBLIC_KB, exist_ok=True)
os.makedirs(PUBLIC_DATA, exist_ok=True)

def format_title(key: str) -> str:
    key_clean = key.replace("_", " ").replace("-", " ")
    key_clean = key_clean.replace("Informaes", "Informações").replace("informaes", "informações")
    words = key_clean.split()
    capitalized = []
    stopwords = {"de", "da", "do", "das", "dos", "em", "no", "na", "nos", "nas", "e", "ou", "para", "com", "por", "a", "o", "as", "os"}
    for i, w in enumerate(words):
        if i > 0 and w.lower() in stopwords:
            capitalized.append(w.lower())
        else:
            capitalized.append(w.capitalize())
    return " ".join(capitalized)

def dict_to_markdown(d: dict, level=3) -> str:
    md = ""
    prefix = "#" * level
    for k, v in d.items():
        title = format_title(str(k))
        if isinstance(v, dict):
            md += f"{prefix} {title}\n\n" + dict_to_markdown(v, level + 1)
        elif isinstance(v, list):
            md += f"{prefix} {title}\n\n"
            for item in v:
                if isinstance(item, str):
                    md += f"- {item.strip()}\n"
                elif isinstance(item, dict):
                    md += "\n" + dict_to_markdown(item, level + 1)
            md += "\n"
        else:
            md += f"{prefix} {title}\n\n{str(v).strip()}\n\n"
    return md

def json_to_markdown(data: dict) -> str:
    title = data.get("titulo", "Documento Oficial")
    categoria = data.get("categoria", "institucional")
    fonte = data.get("fonte", "Fatec Bebedouro")
    curso = data.get("curso")
    resumo = data.get("resumo", "").strip()

    md = f"# {title}\n\n"
    md += f"> **Categoria:** `{categoria}` | **Fonte Oficial:** {fonte}"
    if curso:
        md += f" | **Curso:** {curso}"
    md += "\n\n"

    if resumo:
        md += "## Resumo Executivo\n\n" + resumo + "\n\n"

    dados = data.get("dados_estruturados")
    if isinstance(dados, dict):
        md += "## Conteúdo e Detalhamento Institucional\n\n" + dict_to_markdown(dados, 3)

    for extra in ["Informações Adicionais", "Informaes Adicionais", "estagio", "total_de_aulas", "fonte_detalhe_eixos"]:
        if extra in data and data[extra]:
            val = data[extra]
            md += f"## {format_title(extra)}\n\n"
            if isinstance(val, dict):
                md += dict_to_markdown(val, 3)
            elif isinstance(val, list):
                for item in val:
                    md += f"- {str(item).strip()}\n"
                md += "\n"
            else:
                md += f"{str(val).strip()}\n\n"

    faqs = data.get("perguntas_frequentes", [])
    if isinstance(faqs, list) and faqs:
        md += "## Perguntas Frequentes (FAQ)\n\n"
        for i, faq in enumerate(faqs, 1):
            p = faq.get("pergunta", "").strip()
            r = faq.get("resposta", "").strip()
            kw = faq.get("palavras_chave")
            md += f"### {i}. ❓ {p}\n\n**Resposta:** {r}\n\n"
            if kw:
                kw_str = ", ".join(kw) if isinstance(kw, list) else str(kw)
                md += f"*Palavras-chave:* {kw_str}\n\n"

    return md

def build_data():
    json_files = [f for f in sorted(os.listdir(KB_SRC)) if f.endswith(".json")]
    print(f"Processando {len(json_files)} documentos JSON para o portal...")

    # Limpar pasta public/base-conhecimento para manter apenas JSON
    for old_f in os.listdir(PUBLIC_KB):
        if old_f.endswith(".md"):
            try: os.remove(os.path.join(PUBLIC_KB, old_f))
            except: pass

    documents = []

    for f_json in json_files:
        base_name = os.path.splitext(f_json)[0]
        src_json_path = os.path.join(KB_SRC, f_json)

        # Copiar JSON para public/base-conhecimento
        shutil.copy2(src_json_path, os.path.join(PUBLIC_KB, f_json))

        with open(src_json_path, "r", encoding="utf-8") as jf:
            parsed_json = json.load(jf)

        md_text = json_to_markdown(parsed_json)

        faqs_count = len(parsed_json.get("perguntas_frequentes", []))
        dados_estruturados = parsed_json.get("dados_estruturados", {})
        secoes_count = len(dados_estruturados) if isinstance(dados_estruturados, dict) else 1

        doc_item = {
            "file": f_json,
            "md_file": f"{base_name}.md",
            "titulo": parsed_json.get("titulo", base_name),
            "categoria": parsed_json.get("categoria", "institucional"),
            "fonte": parsed_json.get("fonte", "Fatec Bebedouro"),
            "curso": parsed_json.get("curso"),
            "resumo": parsed_json.get("resumo", ""),
            "faqs": faqs_count,
            "secoes": secoes_count,
            "json_raw": parsed_json,
            "md_text": md_text
        }
        documents.append(doc_item)

    out_json_path = os.path.join(PUBLIC_DATA, "kb-full.json")
    with open(out_json_path, "w", encoding="utf-8") as out:
        json.dump(documents, out, ensure_ascii=False, indent=2)

    with open(PUBLIC_JS_DATA, "w", encoding="utf-8") as out:
        out.write("// Dados consolidados da Base de Conhecimento RAG da Fatec Bebedouro\n")
        out.write("window.FATEC_KB_FULL = ")
        json.dump(documents, out, ensure_ascii=False)
        out.write(";\n")

    print(f"Sucesso! Gerados public/data/kb-full.json e public/kb-data.js ({len(documents)} documentos).")

if __name__ == "__main__":
    build_data()
