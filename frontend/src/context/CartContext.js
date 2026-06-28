import React, { createContext, useState, useEffect, useContext } from 'react';
import { api } from '../api';

const CartContext = createContext(null);

export const CartProvider = ({ children }) => {
  const [cart, setCart] = useState({
    items: [],
    total_estimado: 0,
    region_compra: 'LATAM'
  });

  const [loading, setLoading] = useState(true);

  // 🔐 Obtener token de sesión
  const getToken = () => localStorage.getItem('token_sesion');

  useEffect(() => {
    const loadCart = async () => {
      try {
        const token_sesion = getToken();
        const data = await api.getCart(token_sesion);

        if (data) setCart(data);
      } catch (error) {
        console.error("Error cargando carrito:", error);
      } finally {
        setLoading(false);
      }
    };

    loadCart();
  }, []);

  const addToCart = async (game) => {
    const token_sesion = getToken();

    const newItems = [...cart.items];

    const juegoId = game.id_juego || game.id;
    const titulo = Array.isArray(game.titulo) ? game.titulo[0] : game.titulo;
    const precioBase = Array.isArray(game.precio_base)
      ? game.precio_base[0]
      : game.precio_base;

    const precio = precioBase ?? game.precio ?? game.precio_unitario ?? 0;

    const existingIndex = newItems.findIndex(i => i.juego_id === juegoId);

    if (existingIndex >= 0) {
      newItems[existingIndex].cantidad += 1;
    } else {
      newItems.push({
        juego_id: juegoId,
        titulo,
        precio,
        cantidad: 1
      });
    }

    const total = newItems.reduce(
      (acc, item) => acc + item.precio * item.cantidad,
      0
    );

    const newCart = {
      ...cart,
      items: newItems,
      total_estimado: total
    };

    setCart(newCart);

    await api.updateCart({
      token_sesion,
      juego_id: juegoId,
      cantidad: 1,
      precio_unitario: precio,
      titulo
    });
  };

  const removeFromCart = async (juego_id) => {
    try {
      const token_sesion = getToken();

      await api.removeFromCart(token_sesion, juego_id);

      const newItems = cart.items.filter(i => i.juego_id !== juego_id);

      const total = newItems.reduce(
        (acc, item) => acc + item.precio * item.cantidad,
        0
      );

      setCart({
        ...cart,
        items: newItems,
        total_estimado: total
      });
    } catch (error) {
      console.error("Error al eliminar el item:", error);
    }
  };

  const clearCart = async () => {
    try {
      const token_sesion = getToken();

      await api.clearCart(token_sesion);

      setCart({
        items: [],
        total_estimado: 0,
        region_compra: 'LATAM'
      });
    } catch (error) {
      console.error("Error al vaciar el carrito:", error);
    }
  };

  return (
    <CartContext.Provider
      value={{ cart, addToCart, removeFromCart, clearCart, loading }}
    >
      {children}
    </CartContext.Provider>
  );
};

export const useCart = () => useContext(CartContext);