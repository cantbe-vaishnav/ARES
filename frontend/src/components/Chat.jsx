import React, { useEffect, useRef, useState } from 'react'
import { api } from '../api'

function Message({ m }) {
  return <div className={`message ${m.role}`}>
    <div className="message-label">{m.role === 'user' ? 'You' : 'ARES'}</div>
    <div className="message-body">{m.content}</div>
  </div>
}

export default function Chat({ chatId, selectedFileIds, refreshChats }) {
  const [messages, setMessages] = useState([])
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const endRef = useRef(null)

  useEffect(() => {
    if (!chatId) { setMessages([]); return }
    api(`/chats/${chatId}/messages`).then(setMessages).catch(err => setError(err.message))
  }, [chatId])

  useEffect(() => endRef.current?.scrollIntoView({ behavior: 'smooth' }), [messages, loading])

  async function send(e) {
    e.preventDefault()
    const text = query.trim()
    if (!text || !chatId || loading) return
    setError('')
    setMessages(prev => [...prev, { role: 'user', content: text }])
    setQuery('')
    setLoading(true)
    try {
      const result = await api(`/chats/${chatId}/query`, { method: 'POST', body: JSON.stringify({ query: text, selected_file_ids: selectedFileIds }) })
      setMessages(prev => [...prev, { role: 'assistant', content: result.answer, sources: result }])
      refreshChats()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (!chatId) return <main className="chat-empty"><div><div className="hero-mark">A</div><h2>Start a new ARES chat</h2><p>Select documents manually or leave Auto-route enabled.</p></div></main>

  return <main className="chat-panel">
    <div className="messages">
      {messages.length === 0 && <div className="welcome"><h2>Ask your documents</h2><p>ARES answers locally using the files indexed on this machine.</p></div>}
      {messages.map((m, i) => <Message key={m.id || i} m={m} />)}
      {loading && <div className="message assistant"><div className="message-label">ARES</div><div className="typing">Searching local documents…</div></div>}
      {error && <div className="error inline">{error}</div>}
      <div ref={endRef} />
    </div>
    <form className="composer" onSubmit={send}>
      <textarea rows="2" value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(e) }
      }} placeholder="Ask ARES…" />
      <button disabled={loading || !query.trim()}>Send</button>
    </form>
  </main>
}
