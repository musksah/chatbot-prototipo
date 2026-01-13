import { useState, useRef, useEffect } from 'react'
import './App.css'
import Login from './Login'

// API URL from environment variable or default to localhost
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Simple markdown to HTML converter
function parseMarkdown(text) {
  let lines = text.split('\n')
  lines = lines.map(line => {
    if (line.startsWith('### ')) {
      return `<h4>${line.substring(4)}</h4>`
    } else if (line.startsWith('## ')) {
      return `<h3>${line.substring(3)}</h3>`
    } else if (line.startsWith('# ')) {
      return `<h2>${line.substring(2)}</h2>`
    }
    return line
  })
  text = lines.join('<br>')
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  text = text.replace(/\*(.*?)\*/g, '<em>$1</em>')
  return text
}

function App() {
  // Check if user is already logged in
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem('chatbot_user')
    return savedUser ? JSON.parse(savedUser) : null
  })

  const [messages, setMessages] = useState([
    {
      type: 'bot',
      content: `¡Hola! 👋 Soy el asistente virtual de <strong>COOTRADECUN</strong>. Estoy aquí para ayudarte con:<br><br>
📋 <strong>Asociación:</strong> Requisitos, auxilios y convenios<br>
💰 <strong>Nóminas:</strong> Desprendibles, pagos y libranzas<br>
🏠 <strong>Vivienda:</strong> Créditos y proyectos de vivienda<br><br>
¿En qué puedo asistirte hoy?`
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  // Get or create thread ID
  const getThreadId = () => {
    let threadId = localStorage.getItem('chat_thread_id')
    if (!threadId) {
      threadId = 'user-' + Math.random().toString(36).substr(2, 9)
      localStorage.setItem('chat_thread_id', threadId)
    }
    return threadId
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    const text = inputValue.trim()
    if (!text || isLoading) return

    // Add user message
    setMessages(prev => [...prev, { type: 'user', content: text }])
    setInputValue('')
    setIsLoading(true)

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: text,
          thread_id: getThreadId()
        })
      })

      if (!response.ok) {
        throw new Error('Network response was not ok')
      }

      const data = await response.json()

      if (data.thread_id) {
        localStorage.setItem('chat_thread_id', data.thread_id)
      }

      if (data.messages && data.messages.length > 0) {
        const newMessages = data.messages.map(msg => ({
          type: 'bot',
          content: msg.content
        }))
        setMessages(prev => [...prev, ...newMessages])
      }

    } catch (error) {
      console.error('Error:', error)
      setMessages(prev => [...prev, {
        type: 'bot',
        content: 'Lo siento, ocurrió un error al conectar con el servidor.'
      }])
    } finally {
      setIsLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSend()
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('chatbot_user')
    localStorage.removeItem('chat_thread_id')
    setUser(null)
    setMessages([{
      type: 'bot',
      content: `¡Hola! 👋 Soy el asistente virtual de <strong>COOTRADECUN</strong>. Estoy aquí para ayudarte con:<br><br>
📋 <strong>Asociación:</strong> Requisitos, auxilios y convenios<br>
💰 <strong>Nóminas:</strong> Desprendibles, pagos y libranzas<br>
🏠 <strong>Vivienda:</strong> Créditos y proyectos de vivienda<br><br>
¿En qué puedo asistirte hoy?`
    }])
  }

  // Show login if not authenticated
  if (!user) {
    return <Login onLogin={setUser} />
  }

  return (
    <div className="chat-container">
      <header className="header">
        <img src="/logo-cootradecun.webp" alt="Logo Cootradecun" />
        <span>Asistente Cootradecun</span>
        <button className="logout-btn" onClick={handleLogout} title="Cerrar sesión">
          Salir
        </button>
      </header>

      <div className="user-banner">
        👤 Bienvenido, <strong>CC {user.cedula}</strong>
      </div>

      <div className="messages">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`message ${msg.type}`}
            dangerouslySetInnerHTML={{
              __html: msg.type === 'bot' ? parseMarkdown(msg.content) : msg.content
            }}
          />
        ))}
        {isLoading && (
          <div className="loading">Escribiendo...</div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-area">
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Escribe tu mensaje..."
          disabled={isLoading}
        />
        <button onClick={handleSend} disabled={isLoading}>
          Enviar
        </button>
      </div>
    </div>
  )
}

export default App

