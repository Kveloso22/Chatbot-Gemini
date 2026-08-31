import os
import PyPDF2
import pdfplumber
from docx import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import numpy as np
import config 
from openai import OpenAI

# ============================================================
# 1. MODELO DE EMBEDDINGS
# ============================================================

client = OpenAI(api_key=config.API_KEY, base_url=config.BASE_URL)

def generar_embedding(texto):
    """
    Genera un embedding usando Gemini (text-embedding-004).
    """
    try:
        response = cliente.embeddings.create(
            model="text-embedding-004",  # Modelo de embeddings de Gemini
            input=texto,
            encoding_format="float"
        )
        # Extraer el embedding de la respuesta
        embedding = response.data[0].embedding
        return embedding
    except Exception as e:
        raise RuntimeError(f"Error al generar embedding con Gemini: {e}")


# ============================================================
# 2. EXTRACCIÓN DE TEXTO POR TIPO DE ARCHIVO
# ============================================================

def extraer_texto_pdf(file_path):
    """
    Extrae texto de un archivo PDF con información de páginas.
    Usa pdfplumber (mejor para tablas) y fallback a PyPDF2.
    """
    paginas = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text and text.strip():
                    paginas.append({
                        'pagina': i + 1,
                        'texto': text.strip()
                    })
    except Exception as e:
        print(f"⚠️ pdfplumber falló, usando PyPDF2: {e}")
        # Fallback con PyPDF2
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for i, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text and text.strip():
                        paginas.append({
                            'pagina': i + 1,
                            'texto': text.strip()
                        })
        except Exception as e2:
            print(f"❌ Error al leer PDF: {e2}")
            raise ValueError(f"No se pudo extraer texto del PDF: {e2}")
    
    if not paginas:
        raise ValueError("El PDF no contiene texto extraíble.")
    
    return paginas


def extraer_texto_docx(file_path):
    """
    Extrae texto de un archivo DOCX.
    Devuelve una lista de párrafos con su contenido.
    """
    try:
        doc = Document(file_path)
        parrafos = []
        for p in doc.paragraphs:
            texto = p.text.strip()
            if texto:
                parrafos.append({
                    'texto': texto,
                    'metadata': {}  # DOCX no tiene páginas, pero podrías añadir estilo si quieres
                })
        if not parrafos:
            raise ValueError("El DOCX no contiene texto.")
        return parrafos
    except Exception as e:
        raise ValueError(f"Error al leer DOCX: {e}")


def extraer_texto_txt(file_path):
    """
    Extrae texto de un archivo TXT.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            texto = f.read().strip()
        if not texto:
            raise ValueError("El archivo TXT está vacío.")
        return [{'texto': texto, 'metadata': {}}]
    except Exception as e:
        raise ValueError(f"Error al leer TXT: {e}")


# ============================================================
# 3. DIVISIÓN EN FRAGMENTOS (CHUNKING)
# ============================================================

# Configuración del divisor de texto
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,          # Tamaño del fragmento en caracteres
    chunk_overlap=50,        # Solapamiento entre fragmentos para no perder contexto
    length_function=len,
    separators=["\n\n", "\n", " ", ""]  # Prioridad de separadores
)


def dividir_texto_en_fragmentos(texto, metadatos=None):
    """
    Divide un texto largo en fragmentos usando el splitter configurado.
    """
    if metadatos is None:
        metadatos = {}
    
    chunks = text_splitter.split_text(texto)
    fragmentos = []
    for i, chunk in enumerate(chunks):
        # Añadir número de fragmento a los metadatos
        meta = metadatos.copy()
        meta['chunk'] = i + 1
        fragmentos.append({
            'contenido': chunk,
            'metadata': meta
        })
    return fragmentos


# ============================================================
# 4. GENERACIÓN DE EMBEDDINGS
# ============================================================

def generar_embedding(texto):
    """
    Genera un embedding para un texto usando el modelo configurado.
    (Versión local con sentence-transformers)
    """
    try:
        # El modelo espera una lista de textos
        embedding = embedding_model.encode([texto])[0]
        # Convertir a lista de floats (JSON serializable)
        return embedding.tolist()
    except Exception as e:
        raise RuntimeError(f"Error al generar embedding: {e}")


# ============================================================
# 5. PROCESADOR PRINCIPAL DE DOCUMENTOS
# ============================================================

def procesar_documento(file_path, nombre_archivo):
    """
    Función principal: recibe la ruta de un archivo y su nombre,
    extrae el texto, lo divide en fragmentos y genera embeddings.
    Devuelve una lista de diccionarios con la información de cada fragmento.
    """
    extension = os.path.splitext(nombre_archivo)[1].lower()
    
    # 1. Extraer texto según el tipo de archivo
    if extension == '.pdf':
        paginas = extraer_texto_pdf(file_path)
        # Convertir a formato unificado
        items = []
        for p in paginas:
            items.append({
                'texto': p['texto'],
                'metadata': {'pagina': p['pagina']}
            })
    elif extension == '.docx':
        items = extraer_texto_docx(file_path)
        # Añadir tipo de documento a metadatos
        for item in items:
            item['metadata']['tipo'] = 'docx'
    elif extension == '.txt':
        items = extraer_texto_txt(file_path)
        for item in items:
            item['metadata']['tipo'] = 'txt'
    else:
        raise ValueError(f"Formato no soportado: {extension}")

    # 2. Dividir cada ítem en fragmentos y generar embeddings
    fragmentos_finales = []
    for item in items:
        texto = item['texto']
        metadatos = item['metadata']
        
        # Dividir en fragmentos
        fragmentos = dividir_texto_en_fragmentos(texto, metadatos)
        
        # Para cada fragmento, generar embedding
        for frag in fragmentos:
            embedding = generar_embedding(frag['contenido'])
            fragmentos_finales.append({
                'contenido': frag['contenido'],
                'embedding': embedding,
                'metadata': frag['metadata']
            })
    
    return fragmentos_finales


# ============================================================
# 6. BÚSQUEDA SEMÁNTICA
# ============================================================

def buscar_fragmentos(query, lista_fragmentos, top_k=5):
    """
    Busca los fragmentos más similares a la consulta usando similitud de coseno.
    `lista_fragmentos` debe ser una lista de diccionarios con 'contenido', 'embedding' y 'metadata'.
    Devuelve los top_k fragmentos con su puntuación de similitud.
    """
    if not lista_fragmentos:
        return []
    
    # Generar embedding de la consulta
    query_embedding = np.array(generar_embedding(query))
    
    resultados = []
    for frag in lista_fragmentos:
        # Obtener embedding del fragmento
        frag_embedding = np.array(frag['embedding'])
        
        # Calcular similitud de coseno
        # (producto punto / (norma del vector de consulta * norma del vector del fragmento))
        dot_product = np.dot(query_embedding, frag_embedding)
        norm_query = np.linalg.norm(query_embedding)
        norm_frag = np.linalg.norm(frag_embedding)
        
        if norm_query == 0 or norm_frag == 0:
            similitud = 0
        else:
            similitud = dot_product / (norm_query * norm_frag)
        
        resultados.append({
            'fragmento': frag,
            'similitud': similitud
        })
    
    # Ordenar de mayor a menor similitud
    resultados.sort(key=lambda x: x['similitud'], reverse=True)
    
    # Devolver los top_k
    return resultados[:top_k]