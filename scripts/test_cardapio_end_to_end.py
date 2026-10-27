import json
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

def test_cardapio():
    with open('workflows/subworkflows/Comando _cardapio — Google Sheets.json', 'r', encoding='utf-8') as f:
        cardapio_wf = json.load(f)
    
    with open('workflows/Agente RAG Fatec.json', 'r', encoding='utf-8') as f:
        rag_wf = json.load(f)

    interpret_code = None
    final_resp_code = None
    for n in cardapio_wf['nodes']:
        if n['name'] == 'Interpretar /cardapio':
            interpret_code = n['parameters']['jsCode']
        elif n['name'] == 'Resposta de pedido registrado':
            final_resp_code = n['parameters']['jsCode']

    prep_code = None
    for n in rag_wf['nodes']:
        if 'preparar resposta' in n['name'].lower():
            prep_code = n['parameters']['jsCode']
            break

    # 1. Test Menu rendering
    test_runner_menu = f"""
    const $ = (nodeName) => ({{
        item: {{
            json: {{
                contentText: '/cardapio',
                appSessionKey: 'cardapio:test:1',
                conversationId: '39',
                messageId: '123'
            }}
        }}
    }});
    const $json = {{}};
    function runCardapio() {{ {interpret_code} }}
    const cardapioResult = runCardapio();
    console.log('Action:', cardapioResult.json.action);

    const $input = {{
        first: () => ({{ json: {{ output: cardapioResult.json.output }} }}),
        all: () => [{{ json: {{ output: cardapioResult.json.output }} }}]
    }};
    function runPrep() {{ {prep_code} }}
    const prepResult = runPrep();
    console.log('Menu chunks count:', prepResult.length);
    console.log(prepResult[0].json.output);
    """

    res = subprocess.run(['docker', 'exec', '-i', 'chatbot_n8n-n8n-1', 'node'], input=test_runner_menu.encode('utf-8'), capture_output=True)
    out = res.stdout.decode('utf-8')
    assert "Action: pending" in out
    assert "Menu chunks count: 1" in out
    assert "🎓 *Demonstração Acadêmica — TCC Fatec Bebedouro*" in out
    assert "🍔 *CARDÁPIO DEMONSTRATIVO — Lanchonete Exemplo* 🍟" in out

    # 2. Test Cart creation without name & payment
    test_runner_cart = f"""
    const $ = (nodeName) => ({{
        item: {{
            json: {{
                contentText: 'Quero 1 C1 com Cola Zero',
                appSessionKey: 'cardapio:test:1',
                conversationId: '39',
                messageId: '124',
                phone_number: '+5517991516006'
            }}
        }}
    }});
    const $json = {{
        itens_carrinho: [
            {{ codigo: 'C1', quantidade: 1, bebida_combo: 'Cola Zero', troca_batata_grande: false, adicionais: [], remocoes: [] }}
        ],
        cliente: {{
            nome: null,
            forma_pagamento: null,
            observacoes: null
        }}
    }};
    function runCardapio() {{ {interpret_code} }}
    const res = runCardapio();
    console.log('Cart output:', res.json.output);
    """
    res2 = subprocess.run(['docker', 'exec', '-i', 'chatbot_n8n-n8n-1', 'node'], input=test_runner_cart.encode('utf-8'), capture_output=True)
    out2 = res2.stdout.decode('utf-8')
    assert "seu nome" in out2
    assert "forma de pagamento" in out2

    # 3. Test Invalid Name rejection (e.g. "nenhuma", emojis or numbers)
    test_runner_invalid_name = f"""
    const $ = (nodeName) => ({{
        item: {{
            json: {{
                contentText: 'nenhuma',
                appSessionKey: 'cardapio:test:1',
                conversationId: '39',
                messageId: '125',
                phone_number: '+5517991516006'
            }}
        }}
    }});
    const $json = {{
        itens_carrinho: [
            {{ codigo: 'C1', quantidade: 1, bebida_combo: 'Cola Zero', troca_batata_grande: false, adicionais: [], remocoes: [] }}
        ],
        cliente: {{
            nome: 'nenhuma',
            forma_pagamento: 'Pix',
            observacoes: 'nenhuma'
        }}
    }};
    function runCardapio() {{ {interpret_code} }}
    const res = runCardapio();
    console.log('Invalid name output:', res.json.output);
    """
    res3 = subprocess.run(['docker', 'exec', '-i', 'chatbot_n8n-n8n-1', 'node'], input=test_runner_invalid_name.encode('utf-8'), capture_output=True)
    out3 = res3.stdout.decode('utf-8')
    assert "seu nome" in out3, "Should reject 'nenhuma' as customer name and ask for real name"

    # 4. Test Valid Summary with Gabriel, Pix, and automatic phone +55 (17) 99151-6006
    test_runner_summary = f"""
    const $ = (nodeName) => ({{
        item: {{
            json: {{
                contentText: 'Meu nome e Gabriel e vou pagar no Pix',
                appSessionKey: 'cardapio:test:1',
                conversationId: '39',
                messageId: '126',
                phone_number: '+5517991516006'
            }}
        }}
    }});
    const $json = {{
        itens_carrinho: [
            {{ codigo: 'C1', quantidade: 1, bebida_combo: 'Cola Zero', troca_batata_grande: false, adicionais: [], remocoes: [] }}
        ],
        cliente: {{
            nome: 'Gabriel',
            forma_pagamento: 'Pix',
            observacoes: 'Nenhuma'
        }}
    }};
    function runCardapio() {{ {interpret_code} }}
    const res = runCardapio();
    console.log('SUMMARY OUTPUT:');
    console.log(res.json.output);
    console.log('PENDING STATE:', res.json.pendingState);
    """
    res4 = subprocess.run(['docker', 'exec', '-i', 'chatbot_n8n-n8n-1', 'node'], input=test_runner_summary.encode('utf-8'), capture_output=True)
    out4 = res4.stdout.decode('utf-8')
    assert "👤 *Cliente:* Gabriel" in out4
    assert "📞 *Contato:* +55 (17) 99151-6006" in out4
    assert "💳 *Pagamento:* Pix" in out4
    assert "💰 *TOTAL:* *R$\xa031,90*" in out4 or "31,90" in out4

    # 5. Test Confirmation ("sim") -> triggers Google Sheets + Final TCC explanation
    test_runner_confirm = f"""
    const pendingData = {{
        sessionKey: 'cardapio:test:1',
        summaryAt: Date.now(),
        nome: 'Gabriel',
        contato: '+55 (17) 99151-6006',
        forma_pagamento: 'Pix',
        observacoes: 'Nenhuma',
        summaryItems: '• 1x *C1* Combo Clássico — R$ 31,90',
        totalCents: 3190,
        totalText: 'R$ 31,90'
    }};
    const $ = (nodeName) => {{
        if (nodeName === 'Redis — ler confirmação') {{
            return {{ item: {{ json: {{ pendingState: JSON.stringify(pendingData) }} }} }};
        }}
        if (nodeName === 'Interpretar /cardapio') {{
            return {{
                item: {{
                    json: {{
                        pedido_id: 'cw-39-127',
                        nome: 'Gabriel',
                        contato: '+55 (17) 99151-6006',
                        forma_pagamento: 'Pix',
                        total: 31.90
                    }}
                }}
            }};
        }}
        return {{
            item: {{
                json: {{
                    contentText: 'sim',
                    appSessionKey: 'cardapio:test:1',
                    conversationId: '39',
                    messageId: '127',
                    phone_number: '+5517991516006'
                }}
            }}
        }};
    }};
    const $json = {{}};
    function runCardapio() {{ {interpret_code} }}
    const sheetAction = runCardapio();
    console.log('Confirmation Action:', sheetAction.json.action);
    console.log('Saved to sheet:', sheetAction.json.nome, sheetAction.json.contato, sheetAction.json.forma_pagamento);

    function runFinal() {{ {final_resp_code} }}
    const finalResp = runFinal();
    console.log('FINAL MESSAGE:');
    console.log(finalResp.json.output);
    """
    res5 = subprocess.run(['docker', 'exec', '-i', 'chatbot_n8n-n8n-1', 'node'], input=test_runner_confirm.encode('utf-8'), capture_output=True)
    out5 = res5.stdout.decode('utf-8')
    err5 = res5.stderr.decode('utf-8')
    if err5:
        print("ERR5:", err5)
    print("OUT5:", out5)
    assert "Confirmation Action: sheet" in out5

    assert "Saved to sheet: Gabriel +55 (17) 99151-6006 Pix" in out5
    assert "🎓 *Sobre o Projeto de TCC (Fatec Bebedouro):*" in out5
    assert "nenhum pagamento foi cobrado e não haverá entrega física" in out5
    assert "basta enviar */fatec*" in out5

    sys.stdout.reconfigure(encoding='utf-8')
    print("ALL 5 END-TO-END CARDAPIO SCENARIOS PASSED WITH FLYING COLORS!")

if __name__ == '__main__':
    test_cardapio()
