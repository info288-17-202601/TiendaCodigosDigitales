import React, { createContext, useState, useEffect, useContext } from 'react';
import { api } from '../api';

const CartContext = createContext(null);

export const CartProvider = ({ children }) => {
  const [cart, setCart] = useState({ items: [], total_estimado: 0, region_compra: 'LATAM' });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadCart = async () => {
      const data = await api.getCart();
      if (data) setCart(data);
      setLoading(false);
    };
    loadCart();
  }, []);

  const addToCart = async (game) => {
    const newItems = [...cart.items];
    const existingIndex = newItems.findIndex(i => i.juego_id === game.id_juego);
    
    if (existingIndex >= 0) {
      newItems[existingIndex].cantidad += 1;
    } else {
      newItems.push({
        juego_id: game.id_juego,
        titulo: game.titulo,
        precio: game.precio,
        cantidad: 1
      });
    }

    const total = newItems.reduce((acc, item) => acc + (item.precio * item.cantidad), 0);
    const newCart = { ...cart, items: newItems, total_estimado: total };
    
    setCart(newCart);
    await api.updateCart(newCart);
  };

  const removeFromCart = async (juego_id) => {
    const newItems = cart.items.filter(i => i.juego_id !== juego_id);
    const total = newItems.reduce((acc, item) => acc + (item.precio * item.cantidad), 0);
    const newCart = { ...cart, items: newItems, total_estimado: total };
    
    setCart(newCart);
    await api.updateCart(newCart);
  };

  const clearCart = async () => {
    const newCart = { items: [], total_estimado: 0, region_compra: 'LATAM' };
    setCart(newCart);
    await api.updateCart(newCart);
  };

  return (
    <CartContext.Provider value={{ cart, addToCart, removeFromCart, clearCart, loading }}>
      {children}
    </CartContext.Provider>
  );
};

export const useCart = () => useContext(CartContext);
