import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useDropzone } from 'react-dropzone';

// ✅ CONFIGURACIÓN: Usa la variable de entorno para la URL del backend
const API_URL = import.meta.env.VITE_API_URL || 'https://chatbot-gemini-production.up.railway.app/api';

function App() {
  const [message, setMessage] = useState('');
  const [chatLog, setChatLog] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [documentos, setDocumentos] = useState([]); // nombres de documentos subidos
  const [subiendo, setSubiendo] = useState(false);
  const chatEndRef = useRef(null);

  // Auto-scroll al final del chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatLog]);

  // ===== DROPZONE PARA SUBIR DOCUMENTOS =====
  const onDrop = async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    // Validar tipo de archivo
    const tiposPermitidos = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    if (!tiposPermitidos.includes(file.type)) {
      alert('❌ Solo se permiten archivos PDF, DOCX o TXT.');
      return;
    }

    setSubiendo(true);
    const formData = new FormData();
    formData.append('archivo', file);

    try {
      const response = await axios.post(`${API_URL}/subir-documento/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      // Añadir documento a la lista
      setDocumentos(prev => [...prev, file.name]);
      // Mensaje de confirmación en el chat
      setChatLog(prev => [...prev, {
        sender: 'bot',
        text: `📄 Documento **${file.name}** subido y procesado correctamente (${response.data.fragmentos} fragmentos).`,
        timestamp: new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' }),
        esConfirmacion: true,
      }]);
    } catch (error) {
      console.error('Error al subir:', error);
      const mensaje = error.response?.data?.error || 'Error al subir el documento.';
      setChatLog(prev => [...prev, {
        sender: 'bot',
        text: `❌ ${mensaje}`,
        timestamp: new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' }),
        esConfirmacion: true,
      }]);
    } finally {
      setSubiendo(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
    maxFiles: 1,
  });

  // ===== ENVIAR MENSAJE =====
  const sendMessage = async () => {
    if (!message.trim() || isLoading) return;

    const userMessage = message.trim();
    setMessage('');
    setIsLoading(true);

    setChatLog(prev => [...prev, {
      sender: 'user',
      text: userMessage,
      timestamp: new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })
    }]);

    try {
      // Si hay documentos subidos, usar el endpoint con documentos
      const endpoint = documentos.length > 0 ? `${API_URL}/chat-con-documentos/` : `${API_URL}/chat/`;
      const response = await axios.post(endpoint, { mensaje: userMessage });

      // Preparar mensaje del bot con posibles fuentes
      let textoRespuesta = response.data.respuesta;
      let fuentes = response.data.fuentes || [];

      // Agregar al chat
      setChatLog(prev => [...prev, {
        sender: 'bot',
        text: textoRespuesta,
        timestamp: new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' }),
        fuentes: fuentes, // Guardamos las fuentes para mostrarlas
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

  // ===== REINICIAR CONVERSACIÓN =====
  const reiniciarConversacion = async () => {
    if (!window.confirm('¿Estás seguro de que quieres reiniciar la conversación?')) {
      return;
    }
    try {
      await axios.post(`${API_URL}/reiniciar/`);
      setChatLog([]);
      setDocumentos([]); // También limpiamos los documentos subidos
      setChatLog([{
        sender: 'bot',
        text: '🔄 Conversación reiniciada. Los documentos también han sido eliminados.',
        timestamp: new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })
      }]);
    } catch (error) {
      console.error('Error al reiniciar:', error);
      alert('❌ Error al reiniciar la conversación. Intenta de nuevo.');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl shadow-2xl w-full max-w-3xl h-[650px] flex flex-col overflow-hidden">
        
        {/* HEADER */}
        <div className="bg-gradient-to-r from-purple-800 via-indigo-800 to-blue-800 p-5 text-white flex items-center gap-4">
          <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center text-2xl backdrop-blur-sm">
            🤖
          </div>
          <div>
            <h2 className="font-bold text-lg">Asistente IA</h2>
            <p className="text-sm opacity-80">Powered by Gemini</p>
          </div>
          <div className="ml-auto flex items-center gap-3">
            <button
              onClick={reiniciarConversacion}
              className="text-white/80 hover:text-white hover:bg-white/10 rounded-full px-3 py-1.5 text-sm transition-all duration-200 flex items-center gap-1 border border-white/20"
              title="Reiniciar conversación"
            >
              🔄 Reiniciar
            </button>
            <div className="flex items-center gap-2 text-sm">
              <span className={`w-2.5 h-2.5 rounded-full ${isLoading ? 'bg-yellow-400 animate-pulse' : 'bg-green-400'}`}></span>
              <span className="text-white/90">
                {isLoading ? 'Escribiendo...' : 'En línea'}
              </span>
            </div>
          </div>
        </div>

        {/* ÁREA DE SUBIDA DE DOCUMENTOS */}
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <div 
            {...getRootProps()} 
            className={`border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition-colors ${
              isDragActive ? 'border-purple-500 bg-purple-50' : 'border-gray-300 hover:border-purple-400'
            }`}
          >
            <input {...getInputProps()} />
            {subiendo ? (
              <span className="text-gray-500">⏳ Procesando documento...</span>
            ) : isDragActive ? (
              <span className="text-purple-600">📄 Suelta el archivo aquí</span>
            ) : (
              <span className="text-gray-500">📤 Arrastra un PDF, DOCX o TXT aquí, o haz clic para seleccionar</span>
            )}
          </div>
          {documentos.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-2">
              {documentos.map((doc, i) => (
                <span key={i} className="bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded-full">
                  📄 {doc}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* CHAT LOG */}
        <div className="flex-1 overflow-y-auto p-5 space-y-3 bg-gray-50 scrollbar-thin">
          {chatLog.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center text-gray-400">
              <div className="text-6xl mb-4">👋</div>
              <h3 className="text-xl font-semibold text-gray-600">¡Bienvenido!</h3>
              <p className="text-sm max-w-sm">
                Escribe un mensaje para comenzar a conversar con el asistente.
                {documentos.length === 0 && " Puedes subir documentos (PDF, DOCX, TXT) para hacer preguntas sobre su contenido."}
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
                  {/* Contenido del mensaje */}
                  <div className="text-sm leading-relaxed whitespace-pre-wrap">
                    {entry.text}
                  </div>
                  {/* Fuentes (si existen) */}
                  {entry.fuentes && entry.fuentes.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-gray-200 text-xs text-gray-500">
                      <span className="font-semibold">📚 Fuentes:</span>
                      <ul className="list-disc pl-4 mt-1">
                        {entry.fuentes.map((fuente, idx) => (
                          <li key={idx}>
                            {fuente.documento} {fuente.pagina !== 'N/A' && `(pág. ${fuente.pagina})`} 
                            <span className="text-gray-400"> (similitud: {fuente.similitud}%)</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
          
          {/* Indicador de escritura */}
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

        {/* INPUT */}
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