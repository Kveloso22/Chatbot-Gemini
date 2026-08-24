import time
import openai
from openai import OpenAI
from datetime import datetime
import os
from api.chatbot import config
import sys

# Desactivar colorama para la web (no lo necesitamos)
# Si quieres mantener colores en logs, puedes mantenerlo

def obtener_respuesta_stream(cliente, historial, max_reintentos=3, retraso_inicial=2):
    """
    Obtiene respuesta del modelo con streaming y reintentos en rate-limit.
    Adaptado para la web: ahora puede recibir un callback para el streaming.
    """
    intento = 0
    while intento <= max_reintentos:
        try:
            stream = cliente.chat.completions.create(
                model=config.MODEL,
                messages=historial,
                temperature=config.TEMPERATURE,
                max_tokens=config.MAX_TOKENS,
                stream=True  # Streaming activado
            )

            respuesta_completa = ""
            # Para la web, vamos a ir acumulando la respuesta
            # y devolverla completa al final
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    contenido = chunk.choices[0].delta.content
                    respuesta_completa += contenido

            return respuesta_completa

        except openai.AuthenticationError:
            print(f"❌ Error de autenticación: API Key inválida.")
            return None
        except openai.RateLimitError:
            intento += 1
            if intento > max_reintentos:
                print(f"⏳ Has superado el límite de peticiones.")
                return None
            retraso = retraso_inicial * (2 ** (intento - 1))
            print(f"⏳ Rate limit. Reintentando en {retraso}s...")
            time.sleep(retraso)
            continue
        except openai.APIConnectionError:
            print(f"🌐 Error de conexión. Revisa tu Internet.")
            return None
        except openai.APIError as e:
            print(f"⚠️ Error en la API: {e}")
            return None
        except Exception as e:
            print(f"❗ Error inesperado: {e}")
            return None

def guardar_conversacion(historial, nombre_archivo=None):
    """Guarda el historial en un archivo de log dentro de la carpeta logs/."""
    # Crear carpeta logs en la misma ubicación que este archivo
    logs_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    if not nombre_archivo:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = os.path.join(logs_dir, f"conversacion_{timestamp}.log")
    
    with open(nombre_archivo, "w", encoding="utf-8") as f:
        for msg in historial:
            f.write(f"{msg['role'].capitalize()}: {msg['content']}\n")
    
    print(f"💾 Conversación guardada en {nombre_archivo}")
    return nombre_archivo