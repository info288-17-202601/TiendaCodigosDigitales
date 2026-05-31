import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { useCart } from '../context/CartContext';

const GameDetail = ({ gameId, onNavigate }) => {
  const [game, setGame] = useState(null);
  const [loading, setLoading] = useState(true);
  const { addToCart } = useCart();

  useEffect(() => {
    const fetchGame = async () => {
      const data = await api.getGameDetails(gameId);
      setGame(data);
      setLoading(false);
    };
    fetchGame();
  }, [gameId]);

  if (loading) return <div style={styles.center}>Loading details...</div>;
  if (!game) return <div style={styles.center}>Game not found.</div>;

  return (
    <div className="animate-fade-in" style={styles.container}>
      <button className="btn-secondary" onClick={() => onNavigate('home')} style={{marginBottom: '2rem'}}>
        &larr; Back to Catalog
      </button>

      <div className="glass-card" style={styles.content}>
        <div style={styles.imagePlaceholder}>
          {game.titulo ? game.titulo[0] : '?'}
        </div>
        
        <div style={styles.info}>
          <h1>{game.titulo}</h1>
          <div style={styles.tags}>
            <span style={styles.tag}>{game.plataforma || 'Unknown Platform'}</span>
            <span style={styles.tag}>{game.region_bloqueo || 'Global'}</span>
          </div>
          
          <p style={styles.description}>
            {game.descripcion || 'No hay una descripción disponible para este juego actualmente.'}
          </p>
          
          <div style={styles.actionArea}>
            <div style={styles.price}>${game.precio_base?.toLocaleString('es-CL') || 0}</div>
            <button 
              className="btn-primary" 
              onClick={() => {
                addToCart(game);
                onNavigate('cart');
              }}
              style={{padding: '1rem 2rem', fontSize: '1.1rem'}}
            >
              Add to Cart
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const styles = {
  container: {
    padding: '2rem 0',
    maxWidth: '1000px',
    margin: '0 auto'
  },
  center: {
    textAlign: 'center',
    padding: '4rem',
    color: 'var(--text-secondary)'
  },
  content: {
    display: 'flex',
    gap: '3rem',
    alignItems: 'flex-start',
    flexWrap: 'wrap'
  },
  imagePlaceholder: {
    flex: '1',
    minWidth: '300px',
    height: '400px',
    background: 'linear-gradient(135deg, var(--bg-secondary), var(--bg-primary))',
    borderRadius: '12px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '8rem',
    fontWeight: 'bold',
    color: 'rgba(255, 255, 255, 0.05)'
  },
  info: {
    flex: '2',
    minWidth: '300px',
    display: 'flex',
    flexDirection: 'column',
    gap: '1.5rem'
  },
  tags: {
    display: 'flex',
    gap: '0.5rem'
  },
  tag: {
    background: 'var(--bg-tertiary)',
    padding: '0.25rem 0.75rem',
    borderRadius: '20px',
    fontSize: '0.85rem',
    color: 'var(--text-secondary)',
    border: '1px solid var(--glass-border)'
  },
  description: {
    fontSize: '1.1rem',
    lineHeight: '1.6',
    color: 'var(--text-secondary)'
  },
  actionArea: {
    marginTop: 'auto',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '1.5rem',
    background: 'rgba(0,0,0,0.2)',
    borderRadius: '12px',
    border: '1px solid rgba(255,255,255,0.05)'
  },
  price: {
    fontSize: '2rem',
    fontWeight: 'bold',
    color: 'var(--success)'
  }
};

export default GameDetail;
