import React, { useState } from 'react';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import GameDetail from './pages/GameDetail';
import Cart from './pages/Cart';
import Admin from './pages/Admin';
import { CartProvider } from './context/CartContext';
import { AuthProvider, useAuth } from './context/AuthContext';
import LoginModal from './components/LoginModal';

function AppContent() {
  const [currentView, setCurrentView] = useState('home');
  const [selectedGameId, setSelectedGameId] = useState(null);
  const { showLoginModal } = useAuth();

  const navigate = (view, payload = null) => {
    setCurrentView(view);
    if (view === 'detail') {
      setSelectedGameId(payload);
    }
    window.scrollTo(0, 0);
  };

  return (
    <>
      <Navbar onNavigate={navigate} currentView={currentView} />
      {showLoginModal && <LoginModal />}
      <main className="main-content container">
        {currentView === 'home' && <Home onNavigate={navigate} />}
        {currentView === 'detail' && <GameDetail gameId={selectedGameId} onNavigate={navigate} />}
        {currentView === 'cart' && <Cart onNavigate={navigate} />}
        {currentView === 'admin' && <Admin />}
      </main>
    </>
  );
}

function App() {
  return (
    <AuthProvider>
      <CartProvider>
        <AppContent />
      </CartProvider>
    </AuthProvider>
  );
}

export default App;
