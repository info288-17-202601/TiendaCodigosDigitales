import React, { useState } from 'react';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import GameDetail from './pages/GameDetail';
import Cart from './pages/Cart';
import Admin from './pages/Admin';
import { CartProvider } from './context/CartContext';

function App() {
  const [currentView, setCurrentView] = useState('home');
  const [selectedGameId, setSelectedGameId] = useState(null);

  const navigate = (view, payload = null) => {
    setCurrentView(view);
    if (view === 'detail') {
      setSelectedGameId(payload);
    }
    window.scrollTo(0, 0);
  };

  return (
    <CartProvider>
      <Navbar onNavigate={navigate} currentView={currentView} />
      <main className="main-content container">
        {currentView === 'home' && <Home onNavigate={navigate} />}
        {currentView === 'detail' && <GameDetail gameId={selectedGameId} onNavigate={navigate} />}
        {currentView === 'cart' && <Cart onNavigate={navigate} />}
        {currentView === 'admin' && <Admin />}
      </main>
    </CartProvider>
  );
}

export default App;
