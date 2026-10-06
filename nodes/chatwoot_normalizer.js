/**
 * Normalizador de entrada do Chatwoot para o n8n.
 *
 * Este arquivo é a fonte organizada do código usado pelo node
 * "Chatwoot - Normalizar" no workflow "Subworkflow - Chatwoot Entrada".
 * O conteúdo é um snippet compatível com o Code node do n8n em
 * "Run Once for Each Item"; não é um módulo Node.js para importação.
 *
 * Regras:
 * - aceita somente eventos message_created;
 * - aceita somente mensagens incoming;
 * - ignora mensagens privadas;
 * - devolve process=false para o IF seguinte encerrar o fluxo sem erro;
 * - preserva conversation_id e message_id para sessão, histórico e deduplicação.
 */

const body = $json.body ?? $json;
const message = body.message ?? body;
const conversation = body.conversation ?? message.conversation ?? {};
const event = String(body.event ?? '');
const messageType = String(message.message_type ?? body.message_type ?? '');
const content = String(message.content ?? body.content ?? '');
const conversationId = String(conversation.id ?? body.conversation_id ?? message.conversation_id ?? '');
const messageId = String(message.id ?? body.id ?? '');
const sender = message.sender ?? body.sender ?? {};
const senderId = String(sender.id ?? '');
const isPrivate = Boolean(message.private ?? body.private ?? false);

const valid =
    event === 'message_created' &&
    messageType === 'incoming' &&
    !isPrivate &&
    content.trim() &&
    conversationId &&
    messageId;

if (!valid) {
    return {
        json: {
            process: false,
            chatwoot_event: event,
            message_id: messageId
        }
    };
}

return {
    json: {
        process: true,
        source: 'chatwoot',
        channel: 'chatwoot',
        chatInput: content,
        text: content,
        caption: content,
        input_type: 'text',
        session_id: 'chatwoot:' + conversationId,
        conversation_id: conversationId,
        user_id: senderId || 'conversation:' + conversationId,
        message_id: messageId,
        chatwoot_message_id: messageId,
        chatwoot_conversation_id: conversationId,
        chatwoot_event: event,
        from_me: false
    }
};
