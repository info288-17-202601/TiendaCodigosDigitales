import React, { useEffect, useState } from 'react';
import { api } from '../api';

const Home = ({ onNavigate }) => {
  const [rawGames, setRawGames] = useState([]);
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('*:*');
  const [searchInput, setSearchInput] = useState('');
  const [searchRegion, setSearchRegion] = useState('LATAM');

  const regions = [
    { id: 'US', label: '🇺🇸 US' },
    { id: 'LATAM', label: '🌎 LATAM' },
    { id: 'EU', label: '🇪🇺 EU' },
    { id: 'ASIA', label: 'ASIA' },
    { id: 'Global', label: '🌐 GLOBAL' }
  ];

  useEffect(() => {
    const fetchGames = async () => {
      setLoading(true);
      const data = await api.searchGames(query);
      const gamesResult = data.resultados || [];

      setRawGames(gamesResult);
      setLoading(false);
    };
    fetchGames();
  }, [query]);

  useEffect(() => {
    // Mapear el stock según la región seleccionada
    const mappedGames = rawGames.map(game => {
      let disp = {};
      let isArrayFormat = false;
      try {
        if (game.disponibilidad_regional && game.disponibilidad_regional.length > 0) {
          if (game.disponibilidad_regional.length >= 3 && typeof game.disponibilidad_regional[0] === 'boolean') {
            isArrayFormat = true;
          } else if (game.disponibilidad_regional.length >= 3 && (game.disponibilidad_regional[0] === 'true' || game.disponibilidad_regional[0] === 'false')) {
            isArrayFormat = true;
          } else {
            const val = game.disponibilidad_regional[0];
            disp = typeof val === 'string' ? JSON.parse(val) : val;
          }
        }
      } catch (e) {
        console.error(e);
      }

      const checkStock = (region) => {
        if (isArrayFormat) {
          const idx = { 'EU': 0, 'US': 1, 'LATAM': 2 }[region];
          const val = game.disponibilidad_regional[idx];
          return val === true || val === 'true';
        }
        return disp && disp[region] === true;
      };

      let hasStock = false;
      if (searchRegion === 'Global') {
        hasStock = checkStock('EU') && checkStock('US') && checkStock('LATAM');
      } else {
        hasStock = checkStock(searchRegion);
      }

      return { ...game, stock: hasStock };
    });

    setGames(mappedGames);
  }, [rawGames, searchRegion]);

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

        <div style={styles.regionFilters}>
          {regions.map(r => (
            <button
              key={r.id}
              onClick={() => setSearchRegion(r.id)}
              className={searchRegion === r.id ? 'btn-primary' : 'btn-secondary'}
              style={styles.regionBtn}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      <div style={styles.grid}>
        {loading ? (
          <div style={styles.loading}>Cargando juegos...</div>
        ) : games.length === 0 ? (
          <div style={styles.loading}>No se encontraron juegos.</div>
        ) : (
          games.map(game => {
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
                  <p style={{ color: 'var(--text-secondary)', margin: 0 }}>{game.stock ? '' : 'Agotado :('}</p>
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
  regionFilters: {
    display: 'flex',
    justifyContent: 'center',
    gap: '1rem',
    marginTop: '1.5rem',
    flexWrap: 'wrap'
  },
  regionBtn: {
    padding: '0.5rem 1rem',
    fontSize: '0.95rem'
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
