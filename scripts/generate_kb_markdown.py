"""
Script para gerar arquivos Markdown (.md) a partir dos documentos JSON da base de conhecimento da Fatec Bebedouro.
Garante que todos os textos pré-definidos existam tanto em .json (para ingestão vetorial)
quanto em .md (para documentação, leitura humana e visualização no portal web).
"""

import os
import json
import re

KB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "base-conhecimento")

def format_title(key: str) -> str:
    key_clean = key.replace("_", " ").replace("-", " ")
    # Normalizar acentos corrompidos se houver
    key_clean = key_clean.replace("Informaes", "Informações").replace("informaes", "informações")
    # Capitalização amigável
    words = key_clean.split()
    capitalized = []
    stopwords = {"de", "da", "do", "das", "dos", "em", "no", "na", "nos", "nas", "e", "ou", "para", "com", "por", "a", "o", "as", "os"}
    for i, w in enumerate(words):
        if i > 0 and w.lower() in stopwords:
            capitalized.append(w.lower())
        else:
            capitalized.append(w.capitalize())
    return " ".join(capitalized)

def value_to_markdown(val, level=3) -> str:
    md = ""
    prefix = "#" * level
    if isinstance(val, str):
        md += f"{val.strip()}\n\n"
    elif isinstance(val, list):
        for item in val:
            if isinstance(item, str):
                md += f"- {item.strip()}\n"
            elif isinstance(item, dict):
                md += "\n" + dict_to_markdown(item, level + 1)
        md += "\n"
    elif isinstance(val, dict):
        md += dict_to_markdown(val, level)
    else:
        md += f"{val}\n\n"
    return md

def dict_to_markdown(d: dict, level=3) -> str:
    md = ""
    prefix = "#" * level
    for k, v in d.items():
        title = format_title(str(k))
        if isinstance(v, (dict, list)):
            md += f"{prefix} {title}\n\n"
            md += value_to_markdown(v, level + 1)
        else:
            md += f"{prefix} {title}\n\n{str(v).strip()}\n\n"
    return md

def convert_json_to_md(json_path: str) -> str:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    title = data.get("titulo", "Documento Oficial — Fatec Bebedouro")
    categoria = data.get("categoria", "institucional")
    fonte = data.get("fonte", "Fatec Bebedouro — Jorge Caram Sabbag")
    curso = data.get("curso")
    resumo = data.get("resumo", "").strip()

    md = f"# {title}\n\n"
    md += f"> **Categoria:** `{categoria}` | **Fonte Oficial:** {fonte}"
    if curso:
        md += f" | **Curso:** {curso}"
    md += "\n\n"

    if resumo:
        md += "## Resumo Executivo\n\n"
        md += f"{resumo}\n\n"

    # Dados estruturados
    dados_estruturados = data.get("dados_estruturados")
    if dados_estruturados and isinstance(dados_estruturados, dict):
        md += "## Conteúdo e Detalhamento Institucional\n\n"
        md += dict_to_markdown(dados_estruturados, 3)

    # Outros campos estruturados específicos
    for extra_key in ["Informaes Adicionais", "Informações Adicionais", "estagio", "total_de_aulas", "fonte_detalhe_eixos"]:
        if extra_key in data and data[extra_key]:
            val = data[extra_key]
            md += f"## {format_title(extra_key)}\n\n"
            if isinstance(val, dict):
                md += dict_to_markdown(val, 3)
            elif isinstance(val, list):
                md += value_to_markdown(val, 3)
            else:
                md += f"{str(val).strip()}\n\n"

    # Perguntas Frequentes (FAQ)
    faqs = data.get("perguntas_frequentes", [])
    if faqs and isinstance(faqs, list):
        md += "## Perguntas Frequentes (FAQ)\n\n"
        for i, faq in enumerate(faqs, 1):
            pergunta = faq.get("pergunta", "").strip()
            resposta = faq.get("resposta", "").strip()
            palavras = faq.get("palavras_chave")
            md += f"### {i}. ❓ {pergunta}\n\n"
            md += f"**Resposta:** {resposta}\n\n"
            if palavras:
                if isinstance(palavras, list):
                    md += f"*Palavras-chave:* {', '.join(palavras)}\n\n"
                else:
                    md += f"*Palavras-chave:* {palavras}\n\n"

    return md

def main():
    if not os.path.exists(KB_DIR):
        print(f"Diretório não encontrado: {KB_DIR}")
        return

    json_files = [f for f in sorted(os.listdir(KB_DIR)) if f.endswith(".json")]
    print(f"Encontrados {len(json_files)} arquivos JSON em {KB_DIR} para conversão em Markdown.")

    count = 0
    for file_name in json_files:
        base_name = os.path.splitext(file_name)[0]
        json_path = os.path.join(KB_DIR, file_name)
        md_file_name = f"{base_name}.md"
        md_path = os.path.join(KB_DIR, md_file_name)

        md_content = convert_json_to_md(json_path)
        with open(md_path, "w", encoding="utf-8") as out:
            out.write(md_content)

        print(f" [OK] Gerado {md_file_name} ({len(md_content)} caracteres)")
        count += 1

    print(f"\nConcluído com sucesso! {count} arquivos .md gerados em base-conhecimento/")

if __name__ == "__main__":
    main()
