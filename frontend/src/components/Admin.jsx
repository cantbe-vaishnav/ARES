import React, { useEffect, useState } from 'react'
import { api } from '../api'

export default function Admin({ documents, refreshDocuments }) {
  const [users, setUsers] = useState([])
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('user')
  const [status, setStatus] = useState('')
  const [busy, setBusy] = useState(false)

  function refreshUsers() { api('/admin/users').then(setUsers).catch(err => setStatus(err.message)) }
  useEffect(refreshUsers, [])

  async function upload(e) {
    const file = e.target.files?.[0]
    if (!file) return
    setBusy(true); setStatus(`Indexing ${file.name}…`)
    try {
      const form = new FormData(); form.append('file', file)
      const result = await api('/documents/upload', { method: 'POST', body: form })
      setStatus(`Indexed ${result.filename} (${result.chunk_count} chunks).`)
      refreshDocuments()
    } catch (err) { setStatus(err.message) }
    finally { setBusy(false); e.target.value = '' }
  }

  async function removeDoc(id) {
    if (!confirm('Delete this document and its vector index?')) return
    await api(`/documents/${id}`, { method: 'DELETE' })
    refreshDocuments()
  }

  async function createUser(e) {
    e.preventDefault(); setStatus('')
    try {
      await api('/admin/users', { method: 'POST', body: JSON.stringify({ username, password, role }) })
      setUsername(''); setPassword(''); setRole('user'); refreshUsers()
    } catch (err) { setStatus(err.message) }
  }

  async function setUserRole(id, newRole) {
    try { await api(`/admin/users/${id}/role`, { method: 'PATCH', body: JSON.stringify({ role: newRole }) }); refreshUsers() }
    catch (err) { setStatus(err.message) }
  }

  async function deleteUser(id) {
    if (!confirm('Delete this user and their chats?')) return
    try { await api(`/admin/users/${id}`, { method: 'DELETE' }); refreshUsers() }
    catch (err) { setStatus(err.message) }
  }

  return <main className="admin-panel">
    <div className="admin-header"><h1>Admin</h1><p>Manage local knowledge and ARES accounts.</p></div>
    {status && <div className="status">{status}</div>}
    <div className="admin-grid">
      <section className="card">
        <div className="card-title"><div><h3>Knowledge Base</h3><p>PDF, CSV, XLSX or XLS</p></div><label className={busy ? 'upload disabled' : 'upload'}>{busy ? 'Indexing…' : 'Upload'}<input disabled={busy} type="file" accept=".pdf,.csv,.xlsx,.xls" onChange={upload} /></label></div>
        <div className="table-list">
          {documents.map(d => <div className="table-row" key={d.id}><div><strong>{d.filename}</strong><span>{d.chunk_count} chunks · {d.file_type.toUpperCase()}</span></div><button className="danger" onClick={() => removeDoc(d.id)}>Delete</button></div>)}
          {!documents.length && <p className="muted">No documents indexed.</p>}
        </div>
      </section>
      <section className="card">
        <div className="card-title"><div><h3>Users</h3><p>Admin and chat-only accounts</p></div></div>
        <form className="user-form" onSubmit={createUser}>
          <input placeholder="Username" value={username} onChange={e => setUsername(e.target.value)} required />
          <input placeholder="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} required minLength="6" />
          <select value={role} onChange={e => setRole(e.target.value)}><option value="user">User</option><option value="admin">Admin</option></select>
          <button>Create</button>
        </form>
        <div className="table-list">
          {users.map(u => <div className="table-row" key={u.id}><div><strong>{u.username}</strong><span>{u.role}</span></div><div className="row-actions"><select value={u.role} onChange={e => setUserRole(u.id, e.target.value)}><option value="user">user</option><option value="admin">admin</option></select><button className="danger" onClick={() => deleteUser(u.id)}>Delete</button></div></div>)}
        </div>
      </section>
    </div>
  </main>
}
