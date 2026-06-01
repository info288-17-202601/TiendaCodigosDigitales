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
          <div style={styles.cartLink} onClick={() => onNavigate('cart')}>
            <img src="/cart.svg" alt="Carrito" style={styles.cartIcon} />
            <span>Carrito ({totalItems})</span>
          </div>

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
  },
  cartLink: {
    display: 'flex',
    alignItems: 'center', // Alinea verticalmente el icono con el texto
    gap: '8px',           // Espacio entre el icono, el texto y el número
    cursor: 'pointer',
    textDecoration: 'none',
    color: 'inherit',
    fontSize: '1rem'      // Ajusta según el tamaño de tu fuente
  },
  cartIcon: {
    width: '20px',        // Tamaño controlado
    height: '20px',
    display: 'block',     // Evita espacios extra debajo de la imagen
    objectFit: 'contain'
  },
  cartBadge: {
    fontWeight: 'bold',
    color: 'var(--success)', // O el color que prefieras para resaltar el número
  }

};

export default Navbar;
