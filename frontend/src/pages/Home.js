import React, { useEffect, useState } from 'react';
import { api } from '../api';

const Home = ({ onNavigate }) => {
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('*:*');
  const [searchInput, setSearchInput] = useState('');

  useEffect(() => {
    const fetchGames = async () => {
      setLoading(true);
      const data = await api.searchGames(query);
      const gamesResult = data.resultados || [];

      const gamesWithStock = await Promise.all(
        gamesResult.map(async (game) => {
          const stockData = await api.getStock(game.id, 'LATAM');
          return { ...game, stock: stockData?.stock_disponible || 0 };
        })
      );

      setGames(gamesWithStock);
      setLoading(false);
    };
    fetchGames();
  }, [query]);

  const handleSearch = (e) => {
    e.preventDefault();
    setQuery(searchInput.trim() || '*:*');
  };

  return (
    <div className="animate-fade-in">
      <div style={styles.hero}>
        <h1>Encuentra tu próxima aventura</h1>
        <p>Explora nuestro catálogo de claves digitales disponibles para entrega inmediata.</p>

        <form onSubmit={handleSearch} style={styles.searchForm}>
          <input
            type="text"
            placeholder="Busca juegos... (ej. mario)"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            style={styles.searchInput}
            className="glass"
          />
          <button type="submit" className="btn-primary">Buscar</button>
        </form>
      </div>

      <div style={styles.grid}>
        {loading ? (
          <div style={styles.loading}>Cargando juegos...</div>
        ) : games.length === 0 ? (
          <div style={styles.loading}>No se encontraron juegos.</div>
        ) : (
          games.map(game => {
            const isAvailable = !game.region_bloqueo || game.region_bloqueo === 'LATAM' || game.region_bloqueo === 'Global';

            return (
              <div key={game.id} className="glass-card" style={styles.card} onClick={() => onNavigate('detail', game.id)}>
                <img
                  src={`/${game.id}.png`}
                  alt={game.titulo}
                  style={{ ...styles.cardImagePlaceholder, objectFit: 'cover', width: '100%' }}
                  onError={(e) => {
                    if (!e.target.dataset.triedJpg) {
                      e.target.dataset.triedJpg = 'true';
                      e.target.src = `/${game.id}.jpg`;
                    } else {
                      e.target.onerror = null;
                      e.target.src = 'https://via.placeholder.com/300x180?text=No+Image';
                    }
                  }}
                />
                <div style={styles.cardContent}>
                  <h3>{game.titulo}</h3>
                  <p style={styles.price}>${game.precio_base?.toLocaleString('es-CL') || 0}</p>
                  <p style={{ color: 'var(--text-secondary)', margin: 0 }}>{game.stock ? '' : 'Agotado'}</p>
                  {!isAvailable && (
                    <p style={{ color: 'var(--danger)', fontWeight: 'bold', margin: 0, marginTop: '0.5rem' }}>
                      No disponible en tu país
                    </p>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

const styles = {
  hero: {
    textAlign: 'center',
    padding: '4rem 0',
    marginBottom: '2rem'
  },
  searchForm: {
    display: 'flex',
    justifyContent: 'center',
    gap: '1rem',
    marginTop: '2rem',
    maxWidth: '600px',
    margin: '2rem auto 0 auto'
  },
  searchInput: {
    flex: 1,
    padding: '0.75rem 1.5rem',
    borderRadius: '12px',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    color: 'white',
    fontSize: '1rem',
    outline: 'none',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
    gap: '2rem',
    paddingBottom: '4rem'
  },
  card: {
    cursor: 'pointer',
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
  },
  cardImagePlaceholder: {
    height: '360px',
    background: 'linear-gradient(135deg, var(--bg-secondary), var(--bg-primary))',
    borderRadius: '8px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '2rem',
    fontWeight: 'bold',
    color: 'rgba(255, 255, 255, 0.1)',
  },
  cardContent: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem'
  },
  price: {
    color: 'var(--success)',
    fontWeight: 'bold',
    fontSize: '1.25rem',
    margin: 0
  },
  loading: {
    gridColumn: '1 / -1',
    textAlign: 'center',
    padding: '4rem',
    color: 'var(--text-secondary)'
  }
};

export default Home;
