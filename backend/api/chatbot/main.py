#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Chatbot profesional con streaming, configuración por .env y guardado de conversaciones.
VERSIÓN WEB - Adaptado para Django
"""

import sys
from . import config
from . import utils
from openai import OpenAI

def obtener_respuesta(mensaje_usuario, historial=None):
    """
    Función principal para la web.
    Recibe un mensaje y opcionalmente un historial.
    Devuelve la respuesta del chatbot.
    """
    # Verificar que la API Key esté configurada
    if not config.API_KEY:
        return "❌ No se encontró API_KEY en el archivo .env"

    # Inicializar cliente
    cliente = OpenAI(
        api_key=config.API_KEY,
        base_url=config.BASE_URL
    )

    # Si no hay historial, crear uno nuevo con mensaje de sistema
    if historial is None:
        historial = [
            {"role": "system", "content": "Eres un asistente útil, amigable y conciso."}
        ]

    # Agregar el mensaje del usuario al historial
    historial.append({"role": "user", "content": mensaje_usuario})

    # Obtener respuesta
    respuesta = utils.obtener_respuesta_stream(cliente, historial)

    if respuesta is None:
        # Si falló, eliminar el mensaje del usuario del historial
        historial.pop()
        return "❌ No se pudo obtener respuesta. Intenta de nuevo."

    # Agregar la respuesta al historial
    historial.append({"role": "assistant", "content": respuesta})

    return respuesta

# ============================================================
# NUEVA FUNCIÓN: RESPUESTA CON CONTEXTO (RAG)
# ============================================================

def obtener_respuesta_con_contexto(pregunta, contexto, historial=None):
    """
    Genera una respuesta basada en el contexto proporcionado (fragmentos de documentos).
    Si el historial es None, se crea uno nuevo con el mensaje de sistema.
    """
    if not config.API_KEY:
        return "❌ No se encontró API_KEY en el archivo .env"

    cliente = OpenAI(
        api_key=config.API_KEY,
        base_url=config.BASE_URL
    )

    # Si no hay contexto, responder sin él (o devolver mensaje)
    if not contexto:
        return "ℹ️ No se encontró información relevante en los documentos para responder a tu pregunta."

    # Construir el prompt con el contexto
    contexto_texto = "\n\n---\n\n".join(contexto)
    prompt = f"""
Eres un asistente experto en analizar documentos. Responde la pregunta basándote ÚNICAMENTE en el siguiente contexto.
Si la respuesta no está en el contexto, di: "No encontré información sobre eso en los documentos proporcionados."
Instrucciones importantes:
1. Si la respuesta está en el contexto, proporciónala de forma clara y concisa.
2. Si la respuesta NO está en el contexto, di: "No encontré información sobre eso en los documentos proporcionados."
3. No inventes información ni uses conocimiento externo.
4. Si el contexto contiene números de página, menciónalos al final de la respuesta.
Contexto:
{contexto_texto}

Pregunta: {pregunta}

Respuesta (basada ÚNICAMENTE en el contexto):
"""

    # Inicializar historial si no se proporciona
    if historial is None:
        historial = [
            {"role": "system", "content": prompt}
        ]
    else:
        # Si se proporciona historial, añadir el prompt como mensaje de sistema
        # (o reemplazar el mensaje de sistema existente)
        # Para simplificar, usamos un historial nuevo para RAG
        historial = [
            {"role": "system", "content": prompt}
        ]

    # Agregar la pregunta del usuario (aunque ya está en el prompt)
    historial.append({"role": "user", "content": pregunta})

    # Obtener respuesta usando la función existente de streaming
    respuesta = utils.obtener_respuesta_stream(cliente, historial)

    if respuesta is None:
        return "❌ No se pudo obtener respuesta. Intenta de nuevo."

    return respuesta