import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../api';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [authLoading, setAuthLoading] = useState(true);
  const [region, setRegion] = useState(localStorage.getItem('region') || 'LATAM');  

  // Persistir la región seleccionada
  useEffect(() => {
    localStorage.setItem('region', region);
  }, [region]);

  // EFECTO CRÍTICO: Restaurar sesión al cargar (F5)
  useEffect(() => {
    const restoreSession = async () => {
      const savedToken = localStorage.getItem('token_sesion');
      const savedUser = localStorage.getItem('usuario');

      if (savedToken && savedUser) {
        try {
          // 1. Carga inmediata para evitar parpadeo de "Login"
          const parsedUser = JSON.parse(savedUser);
          setUser(parsedUser);
          setAuthLoading(false); 

          // 2. Validación en segundo plano contra el servidor (Redis)
          const usuarioData = await api.getUsuario(savedToken);

          console.log("usuarioData =", usuarioData);
          console.log("typeof =", typeof usuarioData);
          if (!usuarioData) {
            // Token expirado o inválido
            logout(); 
            console.log("Sesión expirada o inválida. Cerrando sesión. (1)");
          } else {
            // Sincronizar datos frescos del servidor
            const userObj = buildUserObj(usuarioData, savedToken);
            setUser(userObj);
            localStorage.setItem('usuario', JSON.stringify(userObj));
          }
        } catch (e) {
          console.error('Error restaurando sesión:', e);
        }
      } else {
        setAuthLoading(false);
      }
    };

    restoreSession();
  }, []);

  /**
   * Mapea los datos del backend al objeto 'user' del frontend.
   * Backend entrega: { id_usuario, usuario, correo, region, rol }
   */
  const buildUserObj = (usuarioData, token) => ({
    id: usuarioData.id_usuario,
    nombre: usuarioData.usuario,
    email: usuarioData.correo,
    region: usuarioData.region,
    rol: usuarioData.rol,
    token_sesion: token, // Necesario para peticiones autenticadas
  });

  const login = async (email, contrasena) => {
    try {
      const data = await api.login(email, contrasena);

      if (!data || !data.token || !data.usuario) {
        throw new Error('Credenciales incorrectas o error de servidor');
      }

      const userObj = buildUserObj(data.usuario, data.token);
      
      // Guardar en estado y localStorage
      setUser(userObj);
      setRegion(userObj.region || 'LATAM');
      localStorage.setItem('token_sesion', data.token);
      localStorage.setItem('usuario', JSON.stringify(userObj));
      
      setShowLoginModal(false);
      return userObj;
    } catch (e) {
      throw e;
    }
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
    // Limpiar todo rastro local
    setUser(null);
    localStorage.removeItem('token_sesion');
    localStorage.removeItem('usuario');
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      login, 
      logout, 
      showLoginModal, 
      setShowLoginModal, 
      authLoading, 
      region, 
      setRegion 
    }}>
      {children}
    </AuthContext.Provider>
  );
};
