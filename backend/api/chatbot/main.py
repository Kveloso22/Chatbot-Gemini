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