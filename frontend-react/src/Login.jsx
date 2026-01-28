import { useState } from 'react'
import './Login.css'

function Login({ onLogin }) {
    const [cedula, setCedula] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const [isLoading, setIsLoading] = useState(false)

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')

        if (!cedula.trim() || !password.trim()) {
            setError('Por favor ingresa tu cédula y contraseña')
            return
        }

        setIsLoading(true)

        // Simulated login - in production, validate against backend
        // Password: "123" in development, "cootradecun2025$" in production
        const validPassword = import.meta.env.DEV ? '123' : 'cootradecun2025$'
        setTimeout(() => {
            if (password === validPassword) {
                const user = {
                    cedula: cedula,
                    name: 'Asociado COOTRADECUN',
                    loginTime: new Date().toISOString()
                }
                localStorage.setItem('chatbot_user', JSON.stringify(user))
                onLogin(user)
            } else {
                setError('Credenciales incorrectas. Intenta de nuevo.')
            }
            setIsLoading(false)
        }, 1000)
    }

    return (
        <div className="login-container">
            <div className="login-card">
                <div className="login-header">
                    <img src="/logo-cootradecun.webp" alt="Logo Cootradecun" className="login-logo" />
                    <h1>Asistente Virtual</h1>
                    <p>COOTRADECUN</p>
                </div>

                <form onSubmit={handleSubmit} className="login-form">
                    <div className="form-group">
                        <label htmlFor="cedula">Número de Cédula</label>
                        <input
                            type="text"
                            id="cedula"
                            value={cedula}
                            onChange={(e) => setCedula(e.target.value)}
                            placeholder="Ingresa tu cédula"
                            disabled={isLoading}
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="password">Contraseña</label>
                        <input
                            type="password"
                            id="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Ingresa tu contraseña"
                            disabled={isLoading}
                        />
                    </div>

                    {error && <div className="error-message">{error}</div>}

                    <button type="submit" className="login-button" disabled={isLoading}>
                        {isLoading ? 'Ingresando...' : 'Ingresar'}
                    </button>
                </form>

                <div className="login-footer">
                    <p>¿No tienes cuenta? <a href="#">Regístrate aquí</a></p>
                    <p><a href="#">¿Olvidaste tu contraseña?</a></p>
                </div>
            </div>
        </div>
    )
}

export default Login
