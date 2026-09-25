import React, { useEffect, useState } from 'react'
import { api, getToken, setToken } from './api'
import Login from './components/Login'
import Sidebar from './components/Sidebar'
import Chat from './components/Chat'
import Admin from './components/Admin'

export default function App() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(Boolean(getToken()))
  const [chats, setChats] = useState([])
  const [documents, setDocuments] = useState([])
  const [activeChat, setActiveChat] = useState(null)
  const [selected, setSelected] = useState([])
  const [tab, setTab] = useState('chat')

  useEffect(() => {
    if (!getToken()) return
    api('/auth/me').then(u => { setUser(u); setLoading(false) }).catch(() => { setToken(''); setLoading(false) })
  }, [])

  useEffect(() => {
    if (user) { refreshChats(); refreshDocuments() }
  }, [user])

  async function refreshChats() {
    const data = await api('/chats')
    setChats(data)
    if (!activeChat && data.length) setActiveChat(data[0].id)
  }

  async function refreshDocuments() {
    setDocuments(await api('/documents'))
  }

  async function newChat() {
    const chat = await api('/chats', { method: 'POST', body: JSON.stringify({ title: 'New Chat' }) })
    setChats(prev => [chat, ...prev])
    setActiveChat(chat.id)
    setTab('chat')
  }

  function logout() {
    setToken(''); setUser(null); setChats([]); setDocuments([]); setActiveChat(null)
  }

  if (loading) return <div className="boot">Loading ARES…</div>
  if (!user) return <Login onLogin={setUser} />

  return <div className="app-shell">
    <Sidebar chats={chats} activeChat={activeChat} onSelectChat={setActiveChat} onNewChat={newChat} documents={documents} selected={selected} setSelected={setSelected} user={user} tab={tab} setTab={setTab} onLogout={logout} />
    {tab === 'admin' && user.role === 'admin'
      ? <Admin documents={documents} refreshDocuments={refreshDocuments} />
      : <Chat chatId={activeChat} selectedFileIds={selected} refreshChats={refreshChats} />}
  </div>
}
