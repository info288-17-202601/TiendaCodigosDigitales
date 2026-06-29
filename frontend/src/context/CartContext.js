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

  useEffect(() => {
    const loadCart = async () => {
      try {
        const data = await api.getCart();

        if (data) {
          setCart(data);
        }
      } catch (error) {
        console.error('Error cargando carrito:', error);
      } finally {
        setLoading(false);
      }
    };

    loadCart();
  }, []);

  const addToCart = async (game) => {
    try {
      const newItems = [...cart.items];

      const juegoId = game.id_juego || game.id;

      const titulo = Array.isArray(game.titulo)
        ? game.titulo[0]
        : game.titulo;

      const precioBase = Array.isArray(game.precio_base)
        ? game.precio_base[0]
        : game.precio_base;

      const precio =
        precioBase ??
        game.precio ??
        game.precio_unitario ??
        0;

      const existingIndex = newItems.findIndex(
        item => item.juego_id === juegoId
      );

      let cantidadFinal = 1;

      if (existingIndex >= 0) {
        newItems[existingIndex].cantidad += 1;
        cantidadFinal = newItems[existingIndex].cantidad;
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

      setCart({
        ...cart,
        items: newItems,
        total_estimado: total
      });

      await api.updateCart({
        juego_id: juegoId,
        cantidad: cantidadFinal,
        precio_unitario: precio,
        titulo
      });

    } catch (error) {
      console.error('Error agregando al carrito:', error);
    }
  };

  const updateQuantity = async (juego_id, delta) => {
    try {
      const itemActual = cart.items.find(
        item => item.juego_id === juego_id
      );

      if (!itemActual) return;

      const nuevaCantidad = Math.max(
        1,
        itemActual.cantidad + delta
      );

      const newItems = cart.items.map(item =>
        item.juego_id === juego_id
          ? { ...item, cantidad: nuevaCantidad }
          : item
      );

      const total = newItems.reduce(
        (acc, item) => acc + item.precio * item.cantidad,
        0
      );

      setCart({
        ...cart,
        items: newItems,
        total_estimado: total
      });

      await api.updateCart({
        juego_id,
        cantidad: nuevaCantidad,
        precio_unitario: itemActual.precio,
        titulo: itemActual.titulo
      });

    } catch (error) {
      console.error('Error actualizando cantidad:', error);
    }
  };

  const removeFromCart = async (juego_id) => {
    try {
      await api.removeFromCart(juego_id);

      const newItems = cart.items.filter(
        item => item.juego_id !== juego_id
      );

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
      console.error('Error al eliminar item:', error);
    }
  };

  const clearCart = async () => {
    try {
      await api.clearCart();

      setCart({
        items: [],
        total_estimado: 0,
        region_compra: 'LATAM'
      });
    } catch (error) {
      console.error('Error al vaciar carrito:', error);
    }
  };

  return (
    <CartContext.Provider
      value={{
        cart,
        addToCart,
        updateQuantity,
        removeFromCart,
        clearCart,
        loading
      }}
    >
      {children}
    </CartContext.Provider>
  );
};

export const useCart = () => useContext(CartContext);