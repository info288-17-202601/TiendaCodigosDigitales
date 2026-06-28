import React, { useEffect, useState, useRef } from 'react';
import { api } from '../api';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';

const GameDetail = ({ gameId, onNavigate }) => {
  const [game, setGame] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showNoStockModal, setShowNoStockModal] = useState(false);
  const [showAddToCartModal, setShowAddToCartModal] = useState(false);
  const { addToCart, cart } = useCart();
  const { user, setShowLoginModal } = useAuth();
  const [selectedRegion, setSelectedRegion] = useState('LATAM');

  const regions = [
    { id: 'US', label: '🇺🇸 US' },
    { id: 'LATAM', label: '🌎 LATAM' },
    { id: 'EU', label: '🇪🇺 EU' },
    { id: 'Global', label: '🌐 GLOBAL' },
    { id: 'ASIA', label: 'ASIA' }
  ];



  useEffect(() => {
    const fetchGame = async () => {
      setLoading(true);
      const data = await api.getGameDetails(gameId);
      if (data) {
        const stockData = await api.getStock(gameId, selectedRegion);
        data.stock = stockData?.stock_disponible || 0;
      }
      setGame(data);
      setLoading(false);
    };
    fetchGame();
  }, [gameId, selectedRegion]);

  if (loading) return <div style={styles.center}>Cargando detalles...</div>;
  if (!game) return <div style={styles.center}>No se encontró el juego.</div>;

  return (
    <div className="animate-fade-in" style={styles.container}>
      {showAddToCartModal && (
        <div style={styles.modalOverlay}>
          <div className="glass-card animate-fade-in" style={styles.modalContent}>
            <div style={styles.modalIcon}>⚠️</div>
            <h3>¿Seguro que quieres agregar {game.titulo} al carrito?</h3>
            <p>Esta acción agregará {game.titulo} al carrito de compras.</p>
            <div style={styles.modalActions}>
              <button
                className="btn-secondary"
                onClick={() => setShowAddToCartModal(false)}
                style={styles.modalBtn}
              >
                Cancelar
              </button>
              <button
                className="btn-danger"
                onClick={() => addToCart(game)}
                style={styles.modalBtn}
              >
                Sí, agregar al carrito
              </button>
            </div>
          </div>
        </div>
      )}
      {showNoStockModal && (
        <div style={styles.modalOverlay}>
          <div className="glass-card animate-fade-in" style={styles.modalContent}>
            <div style={styles.modalIcon}>⚠️</div>
            <h3>¡Sin stock disponible!</h3>
            <p>Lo sentimos, no hay stock de este juego actualmente.</p>

            <div style={styles.modalActions}>
              <button
                className="btn-primary"
                onClick={() => setShowNoStockModal(false)}
                style={styles.modalBtn}
              >
                Entendido
              </button>
            </div>
          </div>
        </div>
      )}

      <button className="btn-secondary" onClick={() => onNavigate('home')} style={{ marginBottom: '2rem' }}>
        &larr; Volver al catálogo
      </button>

      {(() => {
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
            return val;
          }
          return disp && disp[region] === true;
        };

        let hasStock = false;
        if (selectedRegion === 'Global') {
          hasStock = checkStock('EU') && checkStock('US') && checkStock('LATAM');
        } else {
          hasStock = checkStock(selectedRegion);
        }

        const isAvailable = hasStock;
        return (

          <div className="glass-card" style={styles.content}>
            <img
              src={`/${gameId}.png`}
              alt={game.titulo}
              style={{ ...styles.imagePlaceholder, objectFit: 'cover' }}
              onError={(e) => {
                if (!e.target.dataset.triedJpg) {
                  e.target.dataset.triedJpg = 'true';
                  e.target.src = `/${gameId}.jpg`;
                } else {
                  e.target.onerror = null;
                  e.target.src = 'https://via.placeholder.com/300x400?text=No+Image';
                }
              }}
            />

            <div style={styles.info}>
              <h1>{game.titulo}</h1>
              <div style={styles.tags}>
                <span style={styles.tag}>{game.plataforma || 'Otros'}</span>
              </div>

              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem', flexWrap: 'wrap' }}>
                <p style={{ width: '100%', margin: '0 0 0.5rem 0', color: 'var(--text-secondary)' }}>Selecciona tu región:</p>
                {regions.map(r => (
                  <button
                    key={r.id}
                    onClick={() => setSelectedRegion(r.id)}
                    className={selectedRegion === r.id ? 'btn-primary' : 'btn-secondary'}
                    style={{ padding: '0.25rem 0.75rem', fontSize: '0.9rem' }}
                  >
                    {r.label}
                  </button>
                ))}
              </div>

              <p style={{ fontSize: '1.2rem', color: 'var(--text-primary)', margin: '0.5rem 0' }}>
                Stock disponible: <strong>{game.stock}</strong>
              </p>

              <div style={styles.actionArea}>
                <div style={styles.price}>${game.precio_base?.toLocaleString('es-CL') || 0}</div>
                <button
                  className="btn-primary"
                  onClick={() => {
                    // Determine juego id as used by the cart
                    const juegoId = game.id_juego || game.id || gameId;
                    const cartItems = (cart && Array.isArray(cart.items)) ? cart.items : [];
                    const existing = cartItems.find(i => i.juego_id === juegoId);
                    const cantidadEnCarrito = existing ? existing.cantidad : 0;

                    // Check if user is logged in
                    if (!user) {
                      setShowLoginModal(true);
                      return;
                    }

                    // If no stock or the cart already contains the same (or more) quantity than available, show modal
                    if (game.stock === 0 || cantidadEnCarrito >= game.stock) {
                      setShowNoStockModal(true);
                    } else {
                      addToCart(game);
                      onNavigate('cart');
                    }
                  }}
                  style={{ padding: '1.5rem 0.5rem', fontSize: '1.1rem' }}
                  disabled={!isAvailable}
                >
                  Añadir al carrito
                </button>
              </div>
            </div>
          </div>
        );
      })()}
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
  },
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
    zIndex: 1000,
    padding: '20px'
  },
  modalContent: {
    maxWidth: '400px',
    width: '100%',
    padding: '2rem',
    textAlign: 'center',
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
    border: '1px solid rgba(255, 255, 255, 0.1)'
  },
  modalIcon: {
    fontSize: '3rem',
    marginBottom: '0.5rem'
  },
  modalActions: {
    display: 'flex',
    gap: '1rem',
    marginTop: '1rem'
  },
  modalBtn: {
    flex: 1,
    padding: '0.75rem'
  }
};

export default GameDetail;
