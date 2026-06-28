import React, { useState, useEffect } from 'react';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';
import { api } from '../api';

const Cart = ({ onNavigate }) => {
  const { cart, removeFromCart, clearCart, loading, updateQuantity, updateRegion } = useCart();
  const { user } = useAuth();

  const [checkoutStatus, setCheckoutStatus] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [ordenes, setOrdenes] = useState([]);

  const confirmClearCart = async () => {
    await clearCart();
    const data = await api.getOrdenes();
    setOrdenes(data.historial || []);
    setShowConfirmModal(false);
  };

  const handleCheckout = async () => {
    if (!user?.token_sesion) {
      setCheckoutStatus({
        success: false,
        error: 'Debes iniciar sesión para comprar'
      });
      return;
    }

    setIsProcessing(true);

    try {
      // 1. Validar stock
      for (const item of cart.items) {
        try {
          const stockData = await api.getStock(
            item.juego_id,
            cart.region_compra || 'LATAM'
          );

          const disponible = stockData?.stock_disponible ?? 0;

          if (disponible < item.cantidad) {
            setCheckoutStatus({
              success: false,
              error: `No queda stock suficiente de "${item.titulo}" (solicitado: ${item.cantidad}, disponible: ${disponible})`
            });
            setIsProcessing(false);
            return;
          }
        } catch (e) {
          setCheckoutStatus({
            success: false,
            error: `Error al verificar stock de "${item.titulo}": ${e.message}`
          });
          setIsProcessing(false);
          return;
        }
      }

      // 2. Checkout con token real
      const result = await api.checkout({
        token_sesion: user.token_sesion,
        email: user.email,
        metodo_pago: 'tarjeta'
      });

      setCheckoutStatus({
        success: true,
        orderId: result.id_orden_compra
      });

      await clearCart();

    } catch (e) {
      setCheckoutStatus({
        success: false,
        error: e.message
      });
    } finally {
      setIsProcessing(false);
    }
  };

  useEffect(() => {
    const cargarOrdenes = async () => {
      const data = await api.getOrdenes();
      setOrdenes(data.historial || []);
    };

    cargarOrdenes();
  }, []);

  if (loading) {
    return <div style={styles.center}>Cargando carrito...</div>;
  }

  if (checkoutStatus?.success) {
    return (
      <div className="animate-fade-in" style={styles.center}>
        <div className="glass-card" style={styles.successCard}>
          <div style={styles.successIcon}>✓</div>
          <h2>¡Procesando pago!</h2>
          <p>
            Tu ID de orden es: <strong>{checkoutStatus.orderId}</strong>
          </p>
          <p>Recibirás un correo con las claves.</p>

          <button
            className="btn-primary"
            onClick={() => onNavigate('home')}
            style={{ marginTop: '2rem' }}
          >
            Seguir Comprando
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in" style={styles.container}>
      {showConfirmModal && (
        <div style={styles.modalOverlay}>
          <div className="glass-card animate-fade-in" style={styles.modalContent}>
            <div style={styles.modalIcon}>⚠️</div>
            <h3>¿Vaciar carrito?</h3>
            <p>Esta acción eliminará todos los productos.</p>

            <div style={styles.modalActions}>
              <button
                className="btn-secondary"
                onClick={() => setShowConfirmModal(false)}
                style={styles.modalBtn}
              >
                Cancelar
              </button>

              <button
                className="btn-danger"
                onClick={confirmClearCart}
                style={styles.modalBtn}
              >
                Sí, vaciar todo
              </button>
            </div>
          </div>
        </div>
      )}

      <h2>Tu Carrito</h2>

      {cart.items.length === 0 ? (
        <div className="glass-card" style={styles.emptyCart}>
          <p>Tu carrito está vacío.</p>
          <button
            className="btn-primary"
            onClick={() => onNavigate('home')}
            style={{ marginTop: '1rem' }}
          >
            Explorar Catálogo
          </button>
        </div>
      ) : (
        <div style={styles.cartLayout}>
          <div style={styles.itemsList}>
            {cart.items.map(item => (
              <div
                key={item.juego_id}
                className="glass-card"
                style={styles.cartItem}
              >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  marginTop: '0.5rem'
                }}
              >
                <button
                  className="btn-secondary"
                  onClick={() => updateQuantity(item.juego_id, -1)}
                >
                  -
                </button>

                <span>{item.cantidad}</span>

                <button
                  className="btn-secondary"
                  onClick={() => updateQuantity(item.juego_id, 1)}
                >
                  +
                </button>
              </div>

                <div style={styles.itemActions}>
                  <div style={styles.price}>
                    ${(item.precio * item.cantidad).toLocaleString('es-CL')}
                  </div>

                  <button
                    className="btn-danger"
                    onClick={() => removeFromCart(item.juego_id)}
                  >
                    Eliminar
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="glass-card" style={styles.summary}>
            <h3>Resumen del pedido</h3>

            <div style={styles.summaryRow}>
              <span>Subtotal</span>
              <span>${cart.total_estimado.toLocaleString('es-CL')}</span>
            </div>

            <div style={styles.summaryRow}>
              <span>Región</span>

              <select
                value={cart.region_compra}
                onChange={(e) => updateRegion(e.target.value)}
                style={{
                  background: 'var(--surface)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--glass-border)',
                  borderRadius: '6px',
                  padding: '0.3rem'
                }}
              >
                <option value="LATAM">LATAM</option>
                <option value="NA">NA</option>
                <option value="EU">EU</option>
                <option value="ASIA">ASIA</option>
              </select>
            </div>

            <hr style={styles.divider} />

            <div style={styles.summaryTotal}>
              <span>Total</span>
              <span>${cart.total_estimado.toLocaleString('es-CL')}</span>
            </div>

            {checkoutStatus?.error && (
              <div style={styles.errorBox}>
                {checkoutStatus.error}
              </div>
            )}

            <button
              className="btn-primary"
              style={styles.checkoutBtn}
              onClick={handleCheckout}
              disabled={isProcessing}
            >
              {isProcessing ? 'Procesando...' : 'Proceder al Pago'}
            </button>

            <button
              className="btn-danger-outline"
              style={styles.clearBtn}
              onClick={() => setShowConfirmModal(true)}
              disabled={isProcessing}
            >
              Vaciar Carrito
            </button>
          </div>
        </div>
      )}
    
      {ordenes.map((orden) => (
        <div
          key={orden.id_orden_compra}
          style={{
            borderBottom: '1px solid var(--glass-border)',
            padding: '15px'
          }}
        >
          <h3>Orden #{orden.id_orden_compra}</h3>

          <p>
            <strong>Fecha:</strong>{' '}
            {new Date(orden.fecha_transaccion).toLocaleString('es-CL')}
          </p>

          <p>
            <strong>Método de pago:</strong>{' '}
            {orden.metodo_pago}
          </p>

          <p>
            <strong>Estado:</strong>{' '}
            {orden.estado_pago}
          </p>

          <p>
            <strong>Total:</strong>{' '}
            ${Number(orden.total_pagado).toLocaleString('es-CL')}
          </p>

          <div style={{ marginTop: '1rem' }}>
            <strong>Productos:</strong>

            {orden.detalles_carrito?.map((item, idx) => (
              <div
                key={idx}
                style={{
                  marginTop: '0.5rem',
                  paddingLeft: '1rem',
                  color: 'var(--text-secondary)'
                }}
              >
                • {item.titulo} × {item.cantidad}
              </div>
            ))}
          </div>
        </div>
      ))}
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
    display: 'flex',
    justifyContent: 'center'
  },
  successCard: {
    maxWidth: '500px',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '1rem'
  },
  successIcon: {
    width: '60px',
    height: '60px',
    borderRadius: '50%',
    background: 'rgba(16, 185, 129, 0.2)',
    color: 'var(--success)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '2rem',
    marginBottom: '1rem'
  },
  emptyCart: {
    textAlign: 'center',
    padding: '4rem'
  },
  cartLayout: {
    display: 'flex',
    gap: '2rem',
    alignItems: 'flex-start',
    flexWrap: 'wrap',
    marginTop: '2rem'
  },
  itemsList: {
    flex: '2',
    minWidth: '300px',
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem'
  },
  cartItem: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '1.5rem'
  },
  itemInfo: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem'
  },
  itemActions: {
    display: 'flex',
    alignItems: 'center',
    gap: '1.5rem'
  },
  price: {
    fontWeight: 'bold',
    fontSize: '1.1rem',
    color: 'var(--success)'
  },
  summary: {
    flex: '1',
    minWidth: '300px',
    display: 'flex',
    flexDirection: 'column',
    gap: '1.5rem',
    position: 'sticky',
    top: '100px'
  },
  summaryRow: {
    display: 'flex',
    justifyContent: 'space-between',
    color: 'var(--text-secondary)'
  },
  divider: {
    border: 'none',
    borderTop: '1px solid var(--glass-border)',
    margin: '0.5rem 0'
  },
  summaryTotal: {
    display: 'flex',
    justifyContent: 'space-between',
    fontWeight: 'bold',
    fontSize: '1.25rem',
    color: 'var(--text-primary)'
  },
  checkoutBtn: {
    width: '100%',
    padding: '1rem',
    marginTop: '1rem'
  },
  errorBox: {
    background: 'rgba(239, 68, 68, 0.1)',
    color: 'var(--danger)',
    padding: '1rem',
    borderRadius: '8px',
    fontSize: '0.9rem',
    textAlign: 'center',
    border: '1px solid rgba(239, 68, 68, 0.2)'
  },
  clearBtn: {
    width: '100%',
    padding: '0.75rem',
    marginTop: '0.5rem',
    background: 'transparent',
    border: '1px solid var(--danger)',
    color: 'var(--danger)',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '0.9rem',
    transition: 'all 0.3s'
  },

  headerRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1rem'
  },

  // 4. ESTILOS PARA EL MODAL
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

export default Cart;