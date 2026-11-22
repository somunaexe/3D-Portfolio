import { useEffect, useRef, useState } from 'react'
import {
    ChatError,
    MAX_QUESTION_CHARS,
    newChatId,
    REQUEST_TIMEOUT_MS,
    sendMessage,
} from '../lib/chatClient.js'

const ID_KEY = 'portfolio:chat:id'
const MESSAGES_KEY = 'portfolio:chat:messages'
const MAX_STORED_MESSAGES = 50

const GREETING = "Hi! I can answer questions about Somuna's experience, projects and skills."
const NOTICE = "Answers are written by an AI from Somuna's CV, so they can be imperfect."
const SUGGESTIONS = ['What did Somuna do at Entain?', 'Which projects use AI or machine learning?', 'How can I contact Somuna?']

// sessionStorage keeps the conversation across a page reload but not across visits.
// Every read and write is guarded: storage can be blocked or full, and the chat must still work.
const readStored = (key) => {
    try {
        return window.sessionStorage.getItem(key)
    } catch {
        return null
    }
}
const writeStored = (key, value) => {
    try {
        window.sessionStorage.setItem(key, value)
    } catch {
        // ignore: the conversation just won't survive a reload
    }
}
const loadMessages = () => {
    try {
        const stored = JSON.parse(readStored(MESSAGES_KEY) || '[]')
        return Array.isArray(stored) ? stored : []
    } catch {
        return []
    }
}

const ChatIcon = () => (
    <svg viewBox="0 0 24 24" className="w-7 h-7" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M21 11.5a8.4 8.4 0 0 1-9 8.4 8.6 8.6 0 0 1-3.7-.8L3 21l1.9-5.1A8.4 8.4 0 1 1 21 11.5z" />
    </svg>
)

const CloseIcon = () => (
    <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
        <path d="M6 6l12 12M18 6L6 18" />
    </svg>
)

const SendIcon = () => (
    <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
    </svg>
)

// The widget sits above the 3D scene's loading indicator, which drei draws at z-index 16777271.
const ChatWidget = () => {
    const [open, setOpen] = useState(false)
    const [messages, setMessages] = useState(loadMessages)
    const [draft, setDraft] = useState('')
    const [loading, setLoading] = useState(false)
    const [chatId] = useState(() => readStored(ID_KEY) || newChatId())   // created once per visit
    const abortRef = useRef(null)
    const buttonRef = useRef(null)
    const inputRef = useRef(null)
    const endRef = useRef(null)

    useEffect(() => {
        writeStored(ID_KEY, chatId)
    }, [chatId])

    useEffect(() => {
        writeStored(MESSAGES_KEY, JSON.stringify(messages.slice(-MAX_STORED_MESSAGES)))
    }, [messages])

    useEffect(() => {
        if (open) inputRef.current?.focus()
    }, [open])

    useEffect(() => {
        endRef.current?.scrollIntoView({ block: 'end' })
    }, [messages, loading, open])

    useEffect(() => () => abortRef.current?.abort(), [])   // stop waiting if the page unmounts

    const close = () => {
        setOpen(false)
        buttonRef.current?.focus()
    }

    const ask = async (text) => {
        const question = text.trim()
        if (!question || loading) return
        setMessages((current) => [...current, { role: 'user', text: question }])
        setDraft('')
        setLoading(true)

        const controller = new AbortController()
        abortRef.current = controller
        const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)
        try {
            const { answer, sources } = await sendMessage({ chatId, question, signal: controller.signal })
            setMessages((current) => [...current, { role: 'bot', text: answer, sources }])
        } catch (error) {
            const text = error instanceof ChatError
                ? error.message
                : error.name === 'AbortError'
                    ? 'That took too long. Please try again.'
                    : 'Something went wrong. Please try again.'
            setMessages((current) => [...current, { role: 'bot', text, isError: true }])
        } finally {
            clearTimeout(timer)
            setLoading(false)
        }
    }

    const onSubmit = (event) => {
        event.preventDefault()
        ask(draft)
    }

    const onKeyDown = (event) => {
        if (event.key === 'Escape') close()
    }

    return (
        <div className="fixed bottom-5 right-5 z-[20000000]" onKeyDown={onKeyDown}>
            {open && (
                <section
                    id="chat-panel"
                    role="dialog"
                    aria-label="Chat with the portfolio assistant"
                    className="chat-panel absolute bottom-[4.5rem] right-0 flex flex-col w-[calc(100vw-2.5rem)] sm:w-96 h-[min(32rem,calc(100dvh-8rem))] rounded-2xl border border-black-500 bg-black-200 shadow-2xl shadow-black-100 overflow-hidden"
                >
                    <header className="flex items-start justify-between gap-3 px-4 py-3 border-b border-black-500 bg-black-300">
                        <div>
                            <h2 className="text-white-900 font-semibold">Ask me about Somuna</h2>
                            <p className="text-xs text-white-600">{NOTICE}</p>
                        </div>
                        <button type="button" onClick={close} aria-label="Close chat" className="shrink-0 rounded-md p-1 text-white-600 hover:text-white-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent">
                            <CloseIcon />
                        </button>
                    </header>

                    <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3" aria-live="polite">
                        <p className="mr-auto max-w-[90%] rounded-2xl rounded-bl-md bg-black-300 px-3 py-2 text-sm text-white-900">{GREETING}</p>

                        {messages.length === 0 && (
                            <div className="flex flex-wrap gap-2">
                                {SUGGESTIONS.map((suggestion) => (
                                    <button
                                        key={suggestion}
                                        type="button"
                                        onClick={() => ask(suggestion)}
                                        className="rounded-full border border-black-500 bg-black-100 px-3 py-1 text-xs text-white-700 hover:text-white-900 hover:border-accent"
                                    >
                                        {suggestion}
                                    </button>
                                ))}
                            </div>
                        )}

                        {messages.map((message, index) =>
                            message.role === 'user' ? (
                                <p key={index} className="ml-auto max-w-[85%] whitespace-pre-wrap break-words rounded-2xl rounded-br-md bg-accent px-3 py-2 text-sm text-on-accent">
                                    {message.text}
                                </p>
                            ) : (
                                <div key={index} className="mr-auto max-w-[90%]">
                                    <p className={`whitespace-pre-wrap break-words rounded-2xl rounded-bl-md px-3 py-2 text-sm ${message.isError ? 'border border-red-500 bg-black-100 text-white-800' : 'bg-black-300 text-white-900'}`}>
                                        {message.text}
                                    </p>
                                    {message.sources?.length > 0 && (
                                        <p className="mt-1 px-1 text-xs text-white-600">
                                            Sources: {message.sources.join(' · ')}
                                        </p>
                                    )}
                                </div>
                            ),
                        )}

                        {loading && (
                            <p className="mr-auto rounded-2xl rounded-bl-md bg-black-300 px-3 py-2 text-sm text-white-600" role="status">
                                Thinking<span className="chat-dots" aria-hidden="true">...</span>
                            </p>
                        )}
                        <div ref={endRef} />
                    </div>

                    <form onSubmit={onSubmit} className="flex items-center gap-2 border-t border-black-500 bg-black-300 p-3">
                        <label htmlFor="chat-input" className="sr-only">Your question</label>
                        <input
                            id="chat-input"
                            ref={inputRef}
                            type="text"
                            value={draft}
                            onChange={(event) => setDraft(event.target.value)}
                            maxLength={MAX_QUESTION_CHARS}
                            placeholder="Ask a question..."
                            autoComplete="off"
                            enterKeyHint="send"
                            className="min-w-0 flex-1 rounded-lg border border-black-500 bg-black-200 px-3 py-2 text-sm text-white-900 placeholder:text-white-500 focus:outline-none focus:ring-2 focus:ring-accent"
                        />
                        <button
                            type="submit"
                            disabled={loading || !draft.trim()}
                            aria-label="Send question"
                            className="shrink-0 rounded-lg bg-accent p-2 text-on-accent disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                            <SendIcon />
                        </button>
                    </form>
                    {draft.length >= MAX_QUESTION_CHARS - 40 && (
                        <p className="bg-black-300 px-3 pb-2 text-right text-xs text-white-600">{draft.length}/{MAX_QUESTION_CHARS}</p>
                    )}
                </section>
            )}

            <div className="group relative">
                {!open && (
                    <span
                        role="tooltip"
                        id="chat-tooltip"
                        className="pointer-events-none absolute right-full top-1/2 mr-3 -translate-y-1/2 whitespace-nowrap rounded-lg border border-black-500 bg-black-300 px-3 py-2 text-sm text-white-900 shadow-lg opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100"
                    >
                        Ask me about Somuna.
                    </span>
                )}
                <button
                    ref={buttonRef}
                    type="button"
                    onClick={() => (open ? close() : setOpen(true))}
                    aria-label={open ? 'Close chat' : 'Ask me about Somuna'}
                    aria-expanded={open}
                    aria-controls="chat-panel"
                    aria-describedby={open ? undefined : 'chat-tooltip'}
                    className="flex h-14 w-14 items-center justify-center rounded-full bg-accent text-on-accent shadow-lg shadow-black-100 transition-transform hover:scale-105 motion-reduce:transition-none focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
                >
                    {open ? <CloseIcon /> : <ChatIcon />}
                </button>
            </div>
        </div>
    )
}

export default ChatWidget
