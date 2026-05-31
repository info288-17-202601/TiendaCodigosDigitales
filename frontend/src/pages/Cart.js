import React, { useState } from 'react';
import { useCart } from '../context/CartContext';
import { api } from '../api';

const Cart = ({ onNavigate }) => {
  const { cart, removeFromCart, clearCart, loading } = useCart();
  const [checkoutStatus, setCheckoutStatus] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleCheckout = async () => {
    setIsProcessing(true);
    try {
      const result = await api.checkout();
      setCheckoutStatus({ success: true, orderId: result.id_orden_compra });
      await clearCart();
    } catch (e) {
      setCheckoutStatus({ success: false, error: e.message });
    } finally {
      setIsProcessing(false);
    }
  };

  if (loading) return <div style={styles.center}>Cargando carrito...</div>;

  if (checkoutStatus?.success) {
    return (
      <div className="animate-fade-in" style={styles.center}>
        <div className="glass-card" style={styles.successCard}>
          <div style={styles.successIcon}>✓</div>
          <h2>¡Procesando pago!</h2>
          <p>Tu ID de orden es: <strong>{checkoutStatus.orderId}</strong></p>
          <p>Recibirás un correo electrónico una vez que se entreguen las claves.</p>
          <button className="btn-primary" onClick={() => onNavigate('home')} style={{ marginTop: '2rem' }}>
            Seguir Comprando
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in" style={styles.container}>
      <h2>Tu Carrito</h2>

      {cart.items.length === 0 ? (
        <div className="glass-card" style={styles.emptyCart}>
          <p>Tu carrito está vacío.</p>
          <button className="btn-primary" onClick={() => onNavigate('home')} style={{ marginTop: '1rem' }}>
            Explorar Catálogo
          </button>
        </div>
      ) : (
        <div style={styles.cartLayout}>
          <div style={styles.itemsList}>
            {cart.items.map(item => (
              <div key={item.juego_id} className="glass-card" style={styles.cartItem}>
                <div style={styles.itemInfo}>
                  <h3>{item.titulo}</h3>
                  <p>Cantidad: {item.cantidad}</p>
                </div>
                <div style={styles.itemActions}>
                  <div style={styles.price}>${(item.precio * item.cantidad).toLocaleString('es-CL')}</div>
                  <button className="btn-danger" onClick={() => removeFromCart(item.juego_id)}>
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
              <span>Region</span>
              <span>{cart.region_compra}</span>
            </div>
            <hr style={styles.divider} />
            <div style={styles.summaryTotal}>
              <span>Total</span>
              <span>${cart.total_estimado.toLocaleString('es-CL')}</span>
            </div>

            {checkoutStatus?.error && (
              <div style={styles.errorBox}>{checkoutStatus.error}</div>
            )}

            <button
              className="btn-primary"
              style={styles.checkoutBtn}
              onClick={handleCheckout}
              disabled={isProcessing}
            >
              {isProcessing ? 'Procesando...' : 'Proceder al Pago'}
            </button>
          </div>
        </div>
      )}
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
  }
};

export default Cart;
