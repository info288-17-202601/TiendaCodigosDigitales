import React from 'react';
import { useCart } from '../context/CartContext';

const Navbar = ({ onNavigate, currentView }) => {
  const { cart } = useCart();

  const totalItems = cart.items.reduce((acc, item) => acc + item.cantidad, 0);

  return (
    <nav style={styles.nav} className="glass">
      <div className="container" style={styles.container}>
        <div style={styles.logo} onClick={() => onNavigate('home')}>
          <img src="/logo.png" alt="Store Logo" style={styles.logoImage} />
        </div>

        <div style={styles.links}>
          <button
            className={`btn-secondary ${currentView === 'home' ? 'active' : ''}`}
            onClick={() => onNavigate('home')}
          >
            CATÁLOGO
          </button>

          <button
            className="btn-primary"
            onClick={() => onNavigate('cart')}
          >
            🛒 Carrito ({totalItems})
          </button>
        </div>
      </div>
    </nav>
  );
};

const styles = {
  nav: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    height: '80px',
    zIndex: 1000,
    display: 'flex',
    alignItems: 'center',
  },
  container: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    width: '100%',
  },
  logo: {
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',

  },
  logoImage: {
    marginTop: "14px",
    height: '180px',
    objectFit: 'contain'
  },
  links: {
    display: 'flex',
    gap: '1.5rem',
    alignItems: 'center'
  }
};

export default Navbar;
