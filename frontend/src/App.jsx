import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

// ✅ CONFIGURACIÓN: Usa la variable de entorno para la URL del backend
const API_URL = import.meta.env.VITE_API_URL;

// Verificar que la variable esté definida
if (!API_URL) {
  console.error('❌ VITE_API_URL no está definida. Configura esta variable en Cloudflare Pages.');
}

function App() {
  const [message, setMessage] = useState('');
  const [chatLog, setChatLog] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatLog]);

  const sendMessage = async () => {
    if (!message.trim() || isLoading) return;

    if (!API_URL) {
      setChatLog(prev => [...prev, {
        sender: 'bot',
        text: '❌ Error: VITE_API_URL no configurada',
        timestamp: new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })
      }]);
      return;
    }

    const userMessage = message.trim();
    setMessage('');
    setIsLoading(true);

    setChatLog(prev => [...prev, {
      sender: 'user',
      text: userMessage,
      timestamp: new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })
    }]);

    try {
      // ✅ AHORA USA API_URL en lugar de localhost
      const response = await axios.post(`${API_URL}/chat/`, {
        mensaje: userMessage,
      });

      setChatLog(prev => [...prev, {
        sender: 'bot',
        text: response.data.respuesta,
        timestamp: new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })
      }]);
    } catch (error) {
      console.error('Error:', error);
      let mensajeError = '⚠️ Error de conexión. Intenta de nuevo.';
      if (error.response) {
        mensajeError = `⚠️ Error ${error.response.status}: ${error.response.data?.error || 'Error del servidor'}`;
      } else if (error.request) {
        mensajeError = '⚠️ No se pudo conectar con el servidor. Verifica tu conexión.';
      }
      setChatLog(prev => [...prev, {
        sender: 'bot',
        text: mensajeError,
        timestamp: new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl shadow-2xl w-full max-w-3xl h-[650px] flex flex-col overflow-hidden">
        
        <div className="bg-gradient-to-r from-purple-800 via-indigo-800 to-blue-800 p-5 text-white flex items-center gap-4">
          <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center text-2xl backdrop-blur-sm">
            🤖
          </div>
          <div>
            <h2 className="font-bold text-lg">Asistente IA</h2>
            <p className="text-sm opacity-80">Powered by Gemini</p>
          </div>
          <div className="ml-auto flex items-center gap-2 text-sm">
            <span className={`w-2.5 h-2.5 rounded-full ${isLoading ? 'bg-yellow-400 animate-pulse' : 'bg-green-400'}`}></span>
            <span className="text-white/90">
              {isLoading ? 'Escribiendo...' : 'En línea'}
            </span>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-3 bg-gray-50 scrollbar-thin">
          {chatLog.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center text-gray-400">
              <div className="text-6xl mb-4">👋</div>
              <h3 className="text-xl font-semibold text-gray-600">¡Bienvenido!</h3>
              <p className="text-sm max-w-sm">
                Escribe un mensaje para comenzar a conversar con el asistente.
              </p>
            </div>
          ) : (
            chatLog.map((entry, index) => (
              <div
                key={index}
                className={`flex ${entry.sender === 'user' ? 'justify-end' : 'justify-start'} animate-fadeIn`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 shadow-sm ${
                    entry.sender === 'user'
                      ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-br-none'
                      : 'bg-white text-gray-800 rounded-bl-none border border-gray-200'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-semibold">
                      {entry.sender === 'user' ? '👤 Tú' : '🤖 Asistente'}
                    </span>
                    <span className={`text-[10px] ${entry.sender === 'user' ? 'text-white/60' : 'text-gray-400'}`}>
                      {entry.timestamp}
                    </span>
                  </div>
                  <p className="text-sm leading-relaxed">{entry.text}</p>
                </div>
              </div>
            ))
          )}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white rounded-2xl rounded-bl-none px-4 py-3 shadow-sm border border-gray-200">
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-purple-500 rounded-full animate-typing" style={{ animationDelay: '0s' }}></div>
                  <div className="w-2 h-2 bg-purple-500 rounded-full animate-typing" style={{ animationDelay: '0.2s' }}></div>
                  <div className="w-2 h-2 bg-purple-500 rounded-full animate-typing" style={{ animationDelay: '0.4s' }}></div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={chatEndRef} />
        </div>

        <div className="p-4 bg-white border-t border-gray-200">
          <div className="flex gap-3">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Escribe tu mensaje..."
              disabled={isLoading}
              className="flex-1 px-4 py-2.5 bg-gray-50 border border-gray-300 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all disabled:opacity-50"
            />
            <button
              onClick={sendMessage}
              disabled={isLoading}
              className="px-6 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-full text-sm font-medium hover:shadow-lg hover:shadow-purple-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isLoading ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                  Enviando
                </>
              ) : (
                '✉️ Enviar'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;