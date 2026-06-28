const API_URL = 'http://localhost/api'; 

const getToken = () => localStorage.getItem('token_sesion');

const authHeaders = () => {
  const token = getToken();
  return token
    ? { Authorization: `Bearer ${token}` }
    : {};
};

const inflight = new Map();

export const api = {
  searchGames: async (query = '*:*' ) => {
    try {
      const res = await fetch(`${API_URL}/busqueda/buscar?q=${encodeURIComponent(query)}`);
      if (!res.ok) throw new Error('Fallo al buscar juegos');
      return await res.json();
    } catch (e) {
      console.error(e);
      return { resultados: [] };
    }
  },

  getGameDetails: async (id) => {
    try {
      const res = await fetch(`${API_URL}/busqueda/juego/${id}`);
      if (!res.ok) throw new Error('Juego no encontrado');
      return await res.json();
    } catch (e) {
      console.error(e);
      return null;
    }
  },

  getStock: async (id, region = 'LATAM') => {
    try {
      const res = await fetch(`${API_URL}/inventario/stock/${id}?region=${region}`);
      if (!res.ok) throw new Error('Fallo al obtener el stock');
      return await res.json();
    } catch (e) {
      console.error(e);
      return { stock_disponible: 0 };
    }
  },

  getCart: async () => {
    try {
        const res = await fetch(`${API_URL}/ventas/carrito`, {
        headers: {
            ...authHeaders()
        }
        });

        if (!res.ok) throw new Error('Fallo al obtener el carrito');
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
        headers: {
            'Content-Type': 'application/json',
            ...authHeaders()
        },
        body: JSON.stringify(cartData),
        });

        if (!res.ok) throw new Error('Fallo al actualizar el carrito');
        return await res.json();
    } catch (e) {
        console.error(e);
        return null;
    }
  },

  removeFromCart: async (juegoId) => {
    try {
        const res = await fetch(
        `${API_URL}/ventas/carrito/item/${juegoId}`,
        {
            method: 'DELETE',
            headers: {
            ...authHeaders()
            }
        }
        );

        if (!res.ok) throw new Error('Fallo al eliminar el artículo');
        return await res.json();
    } catch (e) {
        console.error(e);
        return null;
    }
  },

  clearCart: async () => {
    try {
        const res = await fetch(`${API_URL}/ventas/carrito`, {
        method: 'DELETE',
        headers: {
            ...authHeaders()
        }
        });

        if (!res.ok) throw new Error('Fallo al vaciar el carrito');
        return await res.json();
    } catch (e) {
        console.error(e);
        return null;
    }
  },

  getOrdenes: async () => {
    try {
        const res = await fetch(`${API_URL}/ventas/ordenes`, {
        headers: {
            ...authHeaders()
        }
        });

        const data = await res.json();

        if (!res.ok) {
        throw new Error(data?.error || 'Error al obtener el historial de compras');
        }

        return data;
    } catch (e) {
        console.error(e);
        return { historial: [] };
    }
  },

  // ---------------------------------------

  checkout: async (payload) => {
    try {
        const res = await fetch(`${API_URL}/ventas/checkout`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...authHeaders()
        },
        body: JSON.stringify(payload),
        });

        const contentType = res.headers.get('content-type') || '';
        const data = contentType.includes('application/json')
        ? await res.json()
        : null;

        if (!res.ok) throw new Error(data?.error || 'Error en el proceso de checkout');

        return data;
    } catch (e) {
        console.error(e);
        throw e;
    }
  },

  addStock: async (payload) => {
    try {
      const res = await fetch(`http://localhost/admin/admin/agregar_stock`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const contentType = res.headers.get('content-type') || '';
      const data = contentType.includes('application/json') ? await res.json() : null;
      if (!res.ok) return { error: data?.error || 'Error al agregar stock' };
      return data;
    } catch (e) {
      console.error(e);
      return { error: 'Error de red' };
    }
  },

  // ---------------------------------------

  // 1. Iniciar sesión
  login: async (email, contrasena) => {
    try {
      const res = await fetch(`${API_URL}/usuario/login`, {
        method: 'POST', // Coincide con @app.route('/login', methods=['GET'])
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, contrasena })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Error al iniciar sesión');
      return data; // { mensaje, token, usuario: { id_usuario, usuario, correo, region, rol } }
    } catch (e) {
      console.error('Error en login:', e);
      throw e;
    }
  },

  // 2. Registrar un nuevo usuario
  registrar: async (payload) => {
    try {
      const res = await fetch(`${API_URL}/usuario/registrar`, {
        method: 'POST', // Coincide con @app.route('/registrar', methods=['POST'])
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Error al registrarse');
      return data;
    } catch (e) {
      console.error('Error en registro:', e);
      throw e;
    }
  },

  // 3. Obtener datos del usuario (Valida token contra caché/Redis)
  getUsuario: async (token) => {
    const url = `${API_URL}/usuario?token=${encodeURIComponent(token)}`;
    try {
      // Implementación de deduplicación (inflight) para evitar peticiones repetidas
      if (inflight.has(url)) return await inflight.get(url);
      
      const p = (async () => {
        const res = await fetch(url); // Coincide con @app.route('/usuario', methods=['GET'])
        if (!res.ok) return null;
        const data = await res.json();
        return data.detalle || null;
      })();

      inflight.set(url, p);
      try {
        return await p;
      } finally {
        inflight.delete(url);
      }
    } catch (e) {
      console.error('Error al obtener usuario:', e);
      return null;
    }
  },

  // 4. Recuperar contraseña (meolvide)
  recuperarContrasena: async (email) => {
    try {
      const res = await fetch(`${API_URL}/usuario/usuario_olvidado?email=${encodeURIComponent(email)}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Error al solicitar recuperación');
      return data;
    } catch (e) {
      console.error('Error en recuperación:', e);
      throw e;
    }
  },

  // 5. Cerrar sesión
  logout: async (token) => {
    try {
      const res = await fetch(`${API_URL}/usuario/logout?token=${encodeURIComponent(token)}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Error al cerrar sesión');
      return data;
    } catch (e) {
      console.error('Error en logout:', e);
      throw e;
    }
  }
};