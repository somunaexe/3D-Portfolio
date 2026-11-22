// Talks to the chatbot service (chatbot/src/api.py): POST /chat {chat_id, question} -> {answer, sources, error}

export const MAX_QUESTION_CHARS = 200   // must match MAX_QUESTION_CHARS in the service
export const REQUEST_TIMEOUT_MS = 70000 // the service allows up to two 30s LLM calls per question

// Where the service lives. Set VITE_CHATBOT_URL when building for production. In development it falls back
// to a local server. With no URL in a production build the chat icon is simply not shown, so the site never
// ships a chatbot that can't answer.
export const CHATBOT_URL = (
    import.meta.env.VITE_CHATBOT_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '')
).replace(/\/+$/, '')

export const isChatConfigured = Boolean(CHATBOT_URL)

// The service wants 16-64 characters of letters, digits, _ and -. There is no login, so this random id is
// the only thing separating one visitor's conversation from another's.
export const newChatId = () => {
    if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID()
    const bytes = globalThis.crypto.getRandomValues(new Uint8Array(24))   // randomUUID needs a secure context
    return Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0')).join('')
}

// The model cites the excerpts it used as [1], [2]... Those numbers mean nothing to a visitor (they can't see
// the excerpts), so they are removed for display. The sources are shown separately.
export const cleanAnswer = (text) =>
    text.replace(/\s*\[\d+\]/g, '').replace(/\s+([.,;:!?])/g, '$1').trim()

export class ChatError extends Error {
    constructor(message, retryAfter = null) {
        super(message)
        this.name = 'ChatError'
        this.retryAfter = retryAfter
    }
}

const friendlyMessage = (status, apiError, retryAfter) => {
    if (status === 429) {
        const wait = retryAfter ? `${retryAfter} seconds` : 'a moment'
        return `You're sending messages quickly. Please wait ${wait} and try again.`
    }
    if (status === 422) return `That message couldn't be sent. Please keep it under ${MAX_QUESTION_CHARS} characters.`
    if (status >= 500 && typeof apiError === 'string' && apiError) return apiError   // the service's own generic message
    return 'Something went wrong. Please try again.'
}

export const sendMessage = async ({ chatId, question, signal }) => {
    let response
    try {
        response = await fetch(`${CHATBOT_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chat_id: chatId, question }),
            signal,
        })
    } catch (error) {
        if (error.name === 'AbortError') throw error
        throw new ChatError("I can't reach the chatbot right now. Please try again in a moment.")
    }

    let body = null
    try {
        body = await response.json()
    } catch {
        // not JSON: handled below like any other failure
    }

    if (!response.ok || !body || body.error || typeof body.answer !== 'string') {
        const retryAfter = Number(response.headers.get('Retry-After')) || null
        throw new ChatError(friendlyMessage(response.status, body?.error, retryAfter), retryAfter)
    }
    return {
        answer: cleanAnswer(body.answer),
        sources: Array.isArray(body.sources) ? body.sources.filter((source) => typeof source === 'string') : [],
    }
}
