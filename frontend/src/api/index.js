const API_URL = 'http://localhost/api';

export const api = {
  searchGames: async (query = '*:*' ) => {
    try {
      const res = await fetch(`${API_URL}/busqueda/buscar?q=${encodeURIComponent(query)}`);
      if (!res.ok) throw new Error('Search failed');
      return await res.json();
    } catch (e) {
      console.error(e);
      return { resultados: [] };
    }
  },

  getGameDetails: async (id) => {
    try {
      const res = await fetch(`${API_URL}/busqueda/juego/${id}`);
      if (!res.ok) throw new Error('Game not found');
      return await res.json();
    } catch (e) {
      console.error(e);
      return null;
    }
  },

  getCart: async () => {
    try {
      const res = await fetch(`${API_URL}/ventas/carrito`);
      if (!res.ok) throw new Error('Failed to fetch cart');
      return await res.json();
    } catch (e) {
      console.error(e);
      return { items: [], total_estimado: 0, region_compra: 'LATAM' };
    }
  },

  updateCart: async (cartData) => {
    try {
      const res = await fetch(`${API_URL}/ventas/carrito`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(cartData),
      });
      if (!res.ok) throw new Error('Failed to update cart');
      return await res.json();
    } catch (e) {
      console.error(e);
      return null;
    }
  },

  // --- NUEVAS FUNCIONES DE ELIMINACIÓN ---

  // Elimina una instancia de un juego específico
  removeFromCart: async (usuarioId, juegoId) => {
    try {
      const res = await fetch(`${API_URL}/ventas/carrito/${usuarioId}/item/${juegoId}`, {
        method: 'DELETE'
      });
      if (!res.ok) throw new Error('Failed to remove item');
      return await res.json();
    } catch (e) {
      console.error(e);
      return null;
    }
  },

  // Vacía todo el carrito del usuario
  clearCart: async (usuarioId) => {
    try {
      const res = await fetch(`${API_URL}/ventas/carrito/${usuarioId}`, {
        method: 'DELETE'
      });
      if (!res.ok) throw new Error('Failed to clear cart');
      return await res.json();
    } catch (e) {
      console.error(e);
      return null;
    }
  },

  // ---------------------------------------

  checkout: async (payload) => {
    try {
      const res = await fetch(`${API_URL}/ventas/checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const contentType = res.headers.get('content-type') || '';
      const data = contentType.includes('application/json') ? await res.json() : null;
      if (!res.ok) throw new Error(data?.error || 'Checkout failed');
      return data;
    } catch (e) {
      console.error(e);
      throw e;
    }
  }
};
