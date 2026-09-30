/**
 * Normalizador de entrada multimodal
 *
 * Este nó recebe dados vindos de:
 * - Chat Trigger do n8n
 * - Webhook
 * - WhatsApp, Telegram ou outro integrador
 *
 * Saída padronizada:
 * - text
 * - mime_type
 * - input_type
 * - has_caption
 *
 * Importante:
 * Como o nó está em "Run Once for Each Item",
 * o retorno deve ser um objeto único, e não uma lista.
 */

// -----------------------------------------------------------------------------
// 1. Identifica a origem dos dados
// -----------------------------------------------------------------------------

// No Webhook, os dados normalmente ficam em $json.body.
// No Chat Trigger, os dados chegam diretamente em $json.
const body = $json.body ?? $json;


// -----------------------------------------------------------------------------
// 2. Extrai o texto ou legenda da mensagem
// -----------------------------------------------------------------------------

// Chat Trigger usa chatInput.
// Outros canais podem usar text ou message.
const text =
    $json.chatInput ??
    body.text ??
    body.message ??
    '';


// -----------------------------------------------------------------------------
// 3. Identifica o tipo MIME do arquivo
// -----------------------------------------------------------------------------

// O MIME pode vir no JSON ou nos metadados do arquivo binário.
const mime =
    body.mime_type ??
    body.mimeType ??
    $json.mime_type ??
    ($binary?.data?.mimeType ?? '');


// -----------------------------------------------------------------------------
// 4. Verifica se existe um arquivo binário
// -----------------------------------------------------------------------------

const hasBinary = !!$binary?.data;


// -----------------------------------------------------------------------------
// 5. Define flags para cada tipo de conteúdo
// -----------------------------------------------------------------------------

const hasText = !!(
    text &&
    String(text).trim()
);

const isImage =
    String(mime).startsWith('image/') ||
    (
        hasBinary &&
        String($binary?.data?.mimeType ?? '').startsWith('image/')
    );

const isAudio =
    String(mime).startsWith('audio/') ||
    (
        hasBinary &&
        String($binary?.data?.mimeType ?? '').startsWith('audio/')
    );

const isDocument =
    String(mime).includes('pdf') ||
    String(mime).includes('document') ||
    String(mime).startsWith('text/');


// -----------------------------------------------------------------------------
// 6. Classifica a entrada
// -----------------------------------------------------------------------------

let inputType = 'unknown';

if (isImage) {
    inputType = 'image';
} else if (isAudio) {
    inputType = 'audio';
} else if (isDocument) {
    inputType = 'document';
} else if (hasText) {
    inputType = 'text';
}


// -----------------------------------------------------------------------------
// 7. Cria a saída padronizada
// -----------------------------------------------------------------------------

const output = {
    json: {
        // Preserva os dados originais recebidos
        ...body,

        // Texto ou legenda normalizada
        text: String(text || ''),

        // Tipo MIME do arquivo
        mime_type: String(mime || ''),

        // Tipo usado pelo Switch
        // Valores possíveis:
        // text, image, audio, document ou unknown
        input_type: inputType,

        // Indica se uma imagem ou documento veio acompanhado de texto
        has_caption: (isImage || isDocument) && hasText
    }
};


// -----------------------------------------------------------------------------
// 8. Preserva o arquivo binário, quando existir
// -----------------------------------------------------------------------------

if (hasBinary) {
    output.binary = $binary;
}


// -----------------------------------------------------------------------------
// 9. Retorna um único item
// -----------------------------------------------------------------------------

// Não use return [output] neste modo.
// O modo "Run Once for Each Item" exige return output.
return output;
