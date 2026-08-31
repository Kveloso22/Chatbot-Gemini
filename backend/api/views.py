from rest_framework.decorators import api_view
from rest_framework.response import Response
from .chatbot.main import obtener_respuesta 
import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from .models import Documento, FragmentoDocumento
from .chatbot.document_processor import procesar_documento, buscar_fragmentos
from .chatbot.main import obtener_respuesta_con_contexto

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

# ============================================================
# NUEVOS ENDPOINTS PARA DOCUMENTOS (RAG)
# ============================================================

@api_view(['POST'])
def subir_documento(request):
    """
    Recibe un archivo (PDF, DOCX, TXT), lo procesa y guarda los fragmentos en la BD.
    """
    if 'archivo' not in request.FILES:
        return Response({'error': 'No se envió ningún archivo'}, status=400)
    
    archivo = request.FILES['archivo']
    nombre = archivo.name
    
    # Validar extensión
    extension = os.path.splitext(nombre)[1].lower()
    if extension not in ['.pdf', '.docx', '.txt']:
        return Response({'error': f'Formato no soportado: {extension}. Usa PDF, DOCX o TXT.'}, status=400)
    
    # Guardar el archivo físicamente
    ruta = default_storage.save(f'documentos/{nombre}', ContentFile(archivo.read()))
    ruta_completa = os.path.join(settings.MEDIA_ROOT, ruta)
    
    # Crear el documento en la BD
    documento = Documento.objects.create(nombre=nombre)
    
    try:
        # Procesar el documento (extraer texto, chunking, embeddings)
        fragmentos = procesar_documento(ruta_completa, nombre)
        
        # Guardar fragmentos en la BD
        for frag in fragmentos:
            FragmentoDocumento.objects.create(
                documento=documento,
                contenido=frag['contenido'],
                embedding=frag['embedding'],
                metadata=frag['metadata']
            )
        
        return Response({
            'mensaje': 'Documento procesado correctamente',
            'documento_id': documento.id,
            'fragmentos': len(fragmentos)
        })
        
    except Exception as e:
        # Si falla, eliminar el documento y el archivo
        documento.delete()
        if os.path.exists(ruta_completa):
            os.remove(ruta_completa)
        return Response({'error': f'Error al procesar el documento: {str(e)}'}, status=500)


@api_view(['POST'])
def chat_con_documentos(request):
    """
    Recibe una pregunta y responde usando el contenido de los documentos subidos.
    """
    pregunta = request.data.get('mensaje')
    if not pregunta:
        return Response({'error': 'No se envió ninguna pregunta'}, status=400)
    
    # Obtener todos los fragmentos de todos los documentos
    fragmentos = FragmentoDocumento.objects.all()
    if not fragmentos.exists():
        # Si no hay documentos, redirigir al chat normal
        return chat(request)  # ← REUTILIZA TU CHAT EXISTENTE
    
    # Preparar lista de fragmentos para la búsqueda
    lista_fragmentos = [
        {
            'contenido': f.contenido,
            'embedding': f.embedding,
            'metadata': f.metadata,
            'documento_id': f.documento.id,
            'documento_nombre': f.documento.nombre
        }
        for f in fragmentos
    ]
    
    # Buscar fragmentos relevantes
    resultados = buscar_fragmentos(pregunta, lista_fragmentos, top_k=5)
    
    # Extraer contexto y fuentes
    contexto = []
    fuentes = []
    for res in resultados:
        frag = res['fragmento']
        contexto.append(frag['contenido'])
        fuentes.append({
            'documento': frag['documento_nombre'],
            'pagina': frag['metadata'].get('pagina', 'N/A'),
            'similitud': round(res['similitud'] * 100, 2)
        })
    
    # Generar respuesta usando el contexto
    respuesta = obtener_respuesta_con_contexto(pregunta, contexto)
    
    return Response({
        'respuesta': respuesta,
        'fuentes': fuentes
    })