import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../api';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [authLoading, setAuthLoading] = useState(true);

  // Al montar: recuperar sesión desde localStorage y validar token contra Redis
  useEffect(() => {
    const restoreSession = async () => {
      const savedToken = localStorage.getItem('token_sesion');
      if (savedToken) {
        try {
          // Valida que el token aún exista en Redis
          const usuarioData = await api.getUsuario(savedToken);
          if (usuarioData) {
            const userObj = buildUserObj(usuarioData, savedToken);
            setUser(userObj);
          } else {
            // Token expirado o inválido, limpiar
            localStorage.removeItem('token_sesion');
            localStorage.removeItem('usuario');
          }
        } catch (e) {
          console.error('Error restaurando sesión:', e);
          localStorage.removeItem('token_sesion');
          localStorage.removeItem('usuario');
        }
      }
      setAuthLoading(false);
    };
    restoreSession();
  }, []);

  /**
   * Construye el objeto de usuario normalizado.
   * El backend devuelve: { id_usuario, usuario, correo, region, rol }
   */
  const buildUserObj = (usuarioData, token) => ({
    id: usuarioData.id_usuario,
    nombre: usuarioData.usuario,
    email: usuarioData.correo,
    region: usuarioData.region,
    rol: usuarioData.rol,
    token,                      // token Redis — necesario para logout y carrito
  });

  const login = async (email, contrasena) => {
    // data = { mensaje, token, usuario: { id_usuario, usuario, correo, region, rol } }
    const data = await api.login(email, contrasena);

    if (!data || !data.token || !data.usuario) {
      throw new Error('Respuesta de login inválida');
    }

    const userObj = buildUserObj(data.usuario, data.token);

    setUser(userObj);
    localStorage.setItem('token_sesion', data.token);
    localStorage.setItem('usuario', JSON.stringify(userObj));
    setShowLoginModal(false);
    return userObj;
  };

  const logout = async () => {
    const token = localStorage.getItem('token_sesion');
    if (token) {
      try {
        await api.logout(token);
      } catch (e) {
        console.error('Error al cerrar sesión en el servidor:', e);
      }
    }
    setUser(null);
    localStorage.removeItem('token_sesion');
    localStorage.removeItem('usuario');
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, showLoginModal, setShowLoginModal, authLoading }}>
      {children}
    </AuthContext.Provider>
  );
};
