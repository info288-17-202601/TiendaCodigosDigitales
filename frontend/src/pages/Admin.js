import React, { useState, useEffect } from 'react';
import { api } from '../api';

const Admin = () => {
  const [games, setGames] = useState([]);
  const [selectedGameId, setSelectedGameId] = useState('');
  const [region, setRegion] = useState('LATAM');
  const [codigos, setCodigos] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    const fetchGames = async () => {
      const data = await api.searchGames('*:*');
      setGames(data.resultados || []);
    };
    fetchGames();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedGameId || !region || !codigos.trim()) {
      setMessage('Por favor completa todos los campos.');
      return;
    }

    const codigosArray = codigos.split('\n').map(c => c.trim()).filter(c => c !== '');
    if (codigosArray.length === 0) {
      setMessage('Debes ingresar al menos un código.');
      return;
    }

    setLoading(true);
    setMessage('');
    try {
      const res = await api.addStock({
        juego_id: selectedGameId,
        region: region,
        codigos: codigosArray
      });

      if (res && res.error) {
        setMessage(`Error: ${res.error}`);
      } else {
        setMessage(`¡Stock agregado exitosamente! (${codigosArray.length} códigos)`);
        setCodigos(''); // Limpiar códigos
      }
    } catch (err) {
      setMessage('Hubo un error al agregar el stock.');
    }
    setLoading(false);
  };

  return (
    <div className="animate-fade-in" style={styles.container}>
      <div className="glass-card" style={styles.card}>
        <h2>Modo Administrador: Añadir Stock</h2>
        <p>Selecciona un juego, la región e ingresa los códigos digitales (uno por línea).</p>

        <form onSubmit={handleSubmit} style={styles.form}>
          <div style={styles.formGroup}>
            <label style={styles.label}>Juego:</label>
            <select
              value={selectedGameId}
              onChange={(e) => setSelectedGameId(e.target.value)}
              style={styles.input}
              className="glass"
            >
              <option value="">-- Selecciona un juego --</option>
              {games.map(game => {
                 const id = game.id_juego || game.id;
                 return (
                   <option key={id} value={id}>
                     {game.titulo} ({id})
                   </option>
                 );
              })}
            </select>
          </div>

          <div style={styles.formGroup}>
            <label style={styles.label}>Región:</label>
            <select
              value={region}
              onChange={(e) => setRegion(e.target.value)}
              style={styles.input}
              className="glass"
            >
              <option value="LATAM">LATAM</option>
              <option value="US">US</option>
              <option value="EU">EU</option>
              <option value="Global">Global</option>
              <option value="ASIA">ASIA</option>
            </select>
          </div>

          <div style={styles.formGroup}>
            <label style={styles.label}>Códigos (uno por línea):</label>
            <textarea
              value={codigos}
              onChange={(e) => setCodigos(e.target.value)}
              rows="6"
              style={{ ...styles.input, resize: 'vertical' }}
              className="glass"
              placeholder="ABCD-1234-EFGH&#10;XYZ-9876-QWE"
            />
          </div>

          {message && (
            <div style={{ ...styles.message, color: message.includes('Error') ? 'var(--danger)' : 'var(--success)' }}>
              {message}
            </div>
          )}

          <button
            type="submit"
            className="btn-primary"
            style={styles.submitBtn}
            disabled={loading}
          >
            {loading ? 'Agregando...' : 'Agregar Stock'}
          </button>
        </form>
      </div>
    </div>
  );
};

const styles = {
  container: {
    padding: '2rem 0',
    maxWidth: '600px',
    margin: '0 auto'
  },
  card: {
    padding: '2rem',
    display: 'flex',
    flexDirection: 'column',
    gap: '1.5rem'
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1.5rem'
  },
  formGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem'
  },
  label: {
    fontWeight: 'bold',
    color: 'var(--text-primary)'
  },
  input: {
    padding: '0.75rem',
    borderRadius: '8px',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    color: 'white',
    fontSize: '1rem',
    outline: 'none',
    backgroundColor: 'rgba(0, 0, 0, 0.2)'
  },
  submitBtn: {
    padding: '1rem',
    fontSize: '1.1rem',
    marginTop: '1rem'
  },
  message: {
    padding: '1rem',
    borderRadius: '8px',
    backgroundColor: 'rgba(0,0,0,0.3)',
    textAlign: 'center',
    fontWeight: 'bold'
  }
};

export default Admin;
