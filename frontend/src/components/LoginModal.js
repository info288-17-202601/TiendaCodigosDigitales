import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api';

const LoginModal = () => {
  const { setShowLoginModal, login } = useAuth();
  const [isLoginTab, setIsLoginTab] = useState(true);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Registro fields
  const [usuario, setUsuario] = useState('');
  const [region, setRegion] = useState('LATAM');

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
    } catch (err) {
      setError(err.message || 'Error al iniciar sesión');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await api.registrar({
        usuario,
        email,
        contrasena: password,
        region
      });
      // After register, you could auto-login, but since password might be handled differently, let's just switch tab
      setIsLoginTab(true);
      setError('Registro exitoso, por favor inicia sesión'); // Used as success message here
    } catch (err) {
      setError(err.message || 'Error al registrarse');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.modalOverlay}>
      <div className="glass-card animate-fade-in" style={styles.modalContent}>
        <button onClick={() => setShowLoginModal(false)} style={styles.closeBtn}>×</button>

        <div style={styles.tabs}>
          <button
            style={isLoginTab ? styles.activeTab : styles.tab}
            onClick={() => { setIsLoginTab(true); setError(''); }}
          >
            Iniciar Sesión
          </button>
          <button
            style={isLoginTab ? styles.tab : styles.activeTab}
            onClick={() => { setIsLoginTab(false); setError(''); }}
          >
            Registrarse
          </button>
        </div>

        {error && <div style={{ color: error.includes('exitoso') ? 'var(--success)' : 'var(--danger)', marginBottom: '1rem' }}>{error}</div>}

        {isLoginTab ? (
          <form onSubmit={handleLogin} style={styles.form}>
            <input
              type="email"
              placeholder="Email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={styles.input}
            />
            <input
              type="password"
              placeholder="Contraseña"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={styles.input}
            />
            <button className="btn-primary" type="submit" disabled={loading} style={styles.submitBtn}>
              {loading ? 'Cargando...' : 'Iniciar Sesión'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleRegister} style={styles.form}>
            <input
              type="text"
              placeholder="Nombre de Usuario"
              required
              value={usuario}
              onChange={(e) => setUsuario(e.target.value)}
              style={styles.input}
            />
            <input
              type="email"
              placeholder="Email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={styles.input}
            />
            <input
              type="password"
              placeholder="Contraseña"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={styles.input}
            />
            <select
              value={region}
              onChange={(e) => setRegion(e.target.value)}
              style={styles.input}
            >
              <option value="LATAM">LATAM</option>
              <option value="EU">EU</option>
              <option value="US">US</option>
              <option value="ASIA">ASIA</option>
            </select>
            <button className="btn-primary" type="submit" disabled={loading} style={styles.submitBtn}>
              {loading ? 'Cargando...' : 'Registrarse'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
};

const styles = {
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    backdropFilter: 'blur(5px)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 2000,
    padding: '20px'
  },
  modalContent: {
    maxWidth: '400px',
    width: '100%',
    padding: '2rem',
    textAlign: 'center',
    display: 'flex',
    flexDirection: 'column',
    position: 'relative',
    border: '1px solid rgba(255, 255, 255, 0.1)'
  },
  closeBtn: {
    position: 'absolute',
    top: '10px',
    right: '15px',
    background: 'transparent',
    border: 'none',
    color: 'white',
    fontSize: '1.5rem',
    cursor: 'pointer'
  },
  tabs: {
    display: 'flex',
    marginBottom: '1.5rem',
    borderBottom: '1px solid rgba(255,255,255,0.2)'
  },
  tab: {
    flex: 1,
    padding: '0.5rem',
    background: 'transparent',
    border: 'none',
    color: 'var(--text-secondary)',
    cursor: 'pointer',
    fontSize: '1.1rem'
  },
  activeTab: {
    flex: 1,
    padding: '0.5rem',
    background: 'transparent',
    border: 'none',
    borderBottom: '2px solid var(--accent)',
    color: 'var(--accent)',
    cursor: 'pointer',
    fontSize: '1.1rem',
    fontWeight: 'bold'
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem'
  },
  input: {
    padding: '0.75rem',
    borderRadius: '8px',
    border: '1px solid var(--glass-border)',
    background: 'rgba(255, 255, 255, 0.05)',
    color: 'white',
    fontSize: '1rem',
    outline: 'none'
  },
  submitBtn: {
    marginTop: '1rem',
    padding: '0.75rem'
  }
};

export default LoginModal;
