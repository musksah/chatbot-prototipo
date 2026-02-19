import { useState, useEffect, useRef } from 'react'
import './Conversations.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const now = new Date()
  const diffMs = now - d
  const diffHours = diffMs / (1000 * 60 * 60)

  if (diffHours < 24) {
    return d.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })
  }
  if (diffHours < 48) {
    return 'Ayer ' + d.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })
  }
  return d.toLocaleDateString('es-CO', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
}

function formatPhone(phone) {
  if (!phone) return 'Desconocido'
  if (phone.startsWith('57') && phone.length >= 12) {
    return `+57 ${phone.slice(2, 5)} ${phone.slice(5, 8)} ${phone.slice(8)}`
  }
  return `+${phone}`
}

export default function ConversationsPage({ onBack }) {
  const [sessions, setSessions] = useState([])
  const [selectedSession, setSelectedSession] = useState(null)
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadingMessages, setLoadingMessages] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const messagesEndRef = useRef(null)

  // Fetch sessions
  useEffect(() => {
    fetchSessions()
  }, [page])

  async function fetchSessions() {
    setLoading(true)
    try {
      const params = new URLSearchParams({ page: page.toString(), page_size: '20' })
      if (searchQuery) params.append('search', searchQuery)
      const res = await fetch(`${API_URL}/api/conversations/sessions?${params}`)
      const data = await res.json()
      setSessions(data.sessions || [])
      setTotal(data.total || 0)
    } catch (err) {
      console.error('Error fetching sessions:', err)
    } finally {
      setLoading(false)
    }
  }

  async function fetchMessages(sessionId) {
    setLoadingMessages(true)
    try {
      const res = await fetch(`${API_URL}/api/conversations/sessions/${sessionId}`)
      const data = await res.json()
      setMessages(data.messages || [])
      setSelectedSession({
        session_id: sessionId,
        user_phone: data.user_phone,
        user_name: data.user_name,
        total_messages: data.total_messages,
      })
    } catch (err) {
      console.error('Error fetching messages:', err)
    } finally {
      setLoadingMessages(false)
    }
  }

  useEffect(() => {
    if (messages.length > 0 && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages])

  function handleSearch(e) {
    e.preventDefault()
    setPage(1)
    fetchSessions()
  }

  function handleSessionClick(session) {
    fetchMessages(session.session_id)
  }

  function handleBackToList() {
    setSelectedSession(null)
    setMessages([])
  }

  const totalPages = Math.ceil(total / 20)

  // ─── Message Detail View ─────────────────────────────
  if (selectedSession) {
    return (
      <div className="conv-container">
        <div className="conv-header">
          <button className="conv-back-btn" onClick={handleBackToList}>
            ← Volver
          </button>
          <div className="conv-header-info">
            <div className="conv-header-avatar">
              {(selectedSession.user_name || 'U').charAt(0).toUpperCase()}
            </div>
            <div>
              <div className="conv-header-name">{selectedSession.user_name || 'Usuario'}</div>
              <div className="conv-header-phone">{formatPhone(selectedSession.user_phone)}</div>
            </div>
          </div>
          <div className="conv-header-badge">{selectedSession.total_messages} msgs</div>
        </div>

        <div className="conv-messages">
          {loadingMessages ? (
            <div className="conv-loading">
              <div className="conv-spinner"></div>
              Cargando mensajes...
            </div>
          ) : (
            messages.map((msg) => (
              <div key={msg.id} className={`conv-msg ${msg.role === 'user' ? 'conv-msg-user' : 'conv-msg-bot'}`}>
                <div className="conv-msg-bubble">
                  <p>{msg.message}</p>
                  <span className="conv-msg-time">{formatDate(msg.created_at)}</span>
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>
    )
  }

  // ─── Sessions List View ──────────────────────────────
  return (
    <div className="conv-container">
      <div className="conv-header">
        <button className="conv-back-btn" onClick={onBack}>
          ← Chat
        </button>
        <div className="conv-header-info">
          <div className="conv-header-avatar conv-header-avatar-icon">💬</div>
          <div>
            <div className="conv-header-name">Conversaciones WhatsApp</div>
            <div className="conv-header-phone">{total} sesiones</div>
          </div>
        </div>
      </div>

      {/* Search bar */}
      <form className="conv-search" onSubmit={handleSearch}>
        <input
          type="text"
          placeholder="Buscar en mensajes..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <button type="submit">🔍</button>
      </form>

      {/* Sessions list */}
      <div className="conv-list">
        {loading ? (
          <div className="conv-loading">
            <div className="conv-spinner"></div>
            Cargando sesiones...
          </div>
        ) : sessions.length === 0 ? (
          <div className="conv-empty">
            <span className="conv-empty-icon">📭</span>
            <p>No hay conversaciones</p>
          </div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.session_id}
              className="conv-session-card"
              onClick={() => handleSessionClick(session)}
            >
              <div className="conv-session-avatar">
                {(session.user_name || 'U').charAt(0).toUpperCase()}
              </div>
              <div className="conv-session-content">
                <div className="conv-session-top">
                  <span className="conv-session-name">{session.user_name || formatPhone(session.user_phone)}</span>
                  <span className="conv-session-time">{formatDate(session.last_message_at)}</span>
                </div>
                <div className="conv-session-bottom">
                  <span className="conv-session-preview">{session.last_message_preview}</span>
                  <span className="conv-session-count">{session.message_count}</span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="conv-pagination">
          <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}>‹ Ant</button>
          <span>{page} / {totalPages}</span>
          <button disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Sig ›</button>
        </div>
      )}
    </div>
  )
}
