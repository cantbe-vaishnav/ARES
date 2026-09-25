import React from 'react'

export default function Sidebar({ chats, activeChat, onSelectChat, onNewChat, documents, selected, setSelected, user, tab, setTab, onLogout }) {
  function toggle(id) {
    setSelected(selected.includes(id) ? selected.filter(x => x !== id) : [...selected, id])
  }
  return <aside className="sidebar">
    <div className="sidebar-top">
      <div className="brand"><div className="brand-mark small">A</div><div><strong>ARES</strong><span>Local RAG</span></div></div>
      <button className="new-chat" onClick={onNewChat}>＋ New Chat</button>
    </div>

    <section>
      <div className="section-title">Chats</div>
      <div className="chat-list">
        {chats.map(c => <button key={c.id} className={activeChat === c.id ? 'chat-item active' : 'chat-item'} onClick={() => { setTab('chat'); onSelectChat(c.id) }}>{c.title}</button>)}
      </div>
    </section>

    <section className="doc-section">
      <div className="section-title">Documents <span>{selected.length || 'auto'}</span></div>
      <label className="doc-item auto"><input type="checkbox" checked={selected.length === 0} onChange={() => setSelected([])} /> Auto-route</label>
      {documents.map(d => <label key={d.id} className="doc-item"><input type="checkbox" checked={selected.includes(d.id)} onChange={() => toggle(d.id)} /><span title={d.filename}>{d.filename}</span></label>)}
    </section>

    <div className="sidebar-bottom">
      {user?.role === 'admin' && <button className={tab === 'admin' ? 'nav-button active' : 'nav-button'} onClick={() => setTab('admin')}>Admin</button>}
      <div className="user-row"><div><strong>{user?.username}</strong><span>{user?.role}</span></div><button onClick={onLogout}>Logout</button></div>
    </div>
  </aside>
}
