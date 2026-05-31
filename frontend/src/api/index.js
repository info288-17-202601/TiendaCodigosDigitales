const API_URL = '/api';

export const api = {
  searchGames: async (query = '*:*') => {
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
      const res = await fetch(`${API_URL}/cart`);
      if (!res.ok) throw new Error('Failed to fetch cart');
      return await res.json();
    } catch (e) {
      console.error(e);
      return { items: [], total_estimado: 0, region_compra: 'LATAM' };
    }
  },

  updateCart: async (cartData) => {
    try {
      const res = await fetch(`${API_URL}/cart`, {
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

  checkout: async () => {
    try {
      const res = await fetch(`${API_URL}/ventas/comprar`, {
        method: 'POST'
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Checkout failed');
      return data;
    } catch (e) {
      console.error(e);
      throw e;
    }
  }
};
