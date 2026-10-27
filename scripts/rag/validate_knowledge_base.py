#!/usr/bin/env python3
"""
Validador de Estrutura da Base de Conhecimento RAG.
Verifica se todos os arquivos JSON em 'base-conhecimento/' seguem o schema padrão:
- Campos raiz: categoria, titulo, fonte, resumo, dados_estruturados, perguntas_frequentes
- Estrutura de perguntas_frequentes (lista de objetos com pergunta e resposta)
"""

import os
import json
import sys

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    base_dir = os.path.join(root_dir, 'base-conhecimento')

    if not os.path.exists(base_dir):
        print(f"[ERRO] Diretório não encontrado: {base_dir}")
        sys.exit(1)

    files = sorted([f for f in os.listdir(base_dir) if f.endswith('.json')])
    if not files:
        print(f"[AVISO] Nenhum arquivo .json encontrado em {base_dir}")
        sys.exit(0)

    required_fields = ['categoria', 'titulo', 'fonte', 'resumo', 'dados_estruturados', 'perguntas_frequentes']
    issues = []
    total_faqs = 0
    total_sections = 0

    for fname in files:
        fpath = os.path.join(base_dir, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            issues.append(f"{fname}: Erro de sintaxe JSON ({e})")
            continue

        if not isinstance(data, dict):
            issues.append(f"{fname}: Objeto raiz deve ser um dicionário JSON")
            continue

        for req in required_fields:
            if req not in data:
                issues.append(f"{fname}: Campo obrigatório ausente: '{req}'")

        if not isinstance(data.get('dados_estruturados'), dict):
            issues.append(f"{fname}: 'dados_estruturados' deve ser um dicionário/objeto")
        else:
            total_sections += len(data.get('dados_estruturados', {}))

        faqs = data.get('perguntas_frequentes', [])
        if not isinstance(faqs, list):
            issues.append(f"{fname}: 'perguntas_frequentes' deve ser uma lista")
        else:
            total_faqs += len(faqs)
            for idx, faq in enumerate(faqs):
                if not isinstance(faq, dict) or not faq.get('pergunta') or not faq.get('resposta'):
                    issues.append(f"{fname}: FAQ #{idx + 1} incompleto (requer 'pergunta' e 'resposta')")

    print(f"\n========================================================")
    print(f"RELATÓRIO DE VALIDAÇÃO DA BASE DE CONHECIMENTO")
    print(f"Arquivos verificados: {len(files)}")
    print(f"Total de FAQs:        {total_faqs}")
    print(f"Total de Seções:      {total_sections}")
    print(f"========================================================")

    if issues:
        print("\n[FALHA] Problemas encontrados:")
        for issue in issues:
            print(f" - {issue}")
        sys.exit(1)
    else:
        print("\n[SUCESSO] Todos os arquivos JSON estão válidos e em conformidade!")
        sys.exit(0)

if __name__ == '__main__':
    main()
