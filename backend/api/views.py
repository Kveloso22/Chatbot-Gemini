from rest_framework.decorators import api_view
from rest_framework.response import Response
from .chatbot.main import obtener_respuesta  # Importa tu función

@api_view(['POST'])
def chat(request):
    # 1. Obtener el mensaje del usuario
    mensaje_usuario = request.data.get('mensaje')
    
    if not mensaje_usuario:
        return Response(
            {"error": "No se envió ningún mensaje"},
            status=400
        )
    
    # 2. Obtener o crear historial de la sesión
    if 'historial' not in request.session:
        request.session['historial'] = None  # Se creará en la función
    
    historial = request.session.get('historial')
    
    # 3. Llamar a tu lógica del chatbot
    try:
        respuesta = obtener_respuesta(mensaje_usuario, historial)
        
        # 4. Guardar el historial actualizado en la sesión
        request.session['historial'] = historial
        request.session.modified = True
        
        return Response({
            "respuesta": respuesta,
            "status": "success"
        })
        
    except Exception as e:
        print(f"Error en el chatbot: {e}")
        return Response(
            {"error": "Ocurrió un error al procesar tu mensaje"},
            status=500
        )