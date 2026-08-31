from django.db import models

# Create your models here.
class Documento(models.Model):
    """
    Representa un documento subido por el usuario.
    """
    nombre = models.CharField(max_length=255, help_text="Nombre original del archivo")
    archivo = models.FileField(upload_to='documentos/', help_text="Archivo subido (PDF, DOCX, TXT)")
    fecha_subida = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ['-fecha_subida']


class FragmentoDocumento(models.Model):
    """
    Representa un fragmento (chunk) de un documento con su embedding.
    """
    documento = models.ForeignKey(
        Documento, 
        on_delete=models.CASCADE, 
        related_name='fragmentos',
        help_text="Documento al que pertenece el fragmento"
    )
    contenido = models.TextField(help_text="Texto del fragmento")
    embedding = models.JSONField(help_text="Vector de embedding del fragmento")
    metadata = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Metadatos (ej: {'pagina': 3, 'titulo': 'Introducción'})"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.documento.nombre} - Fragmento {self.id}"

    class Meta:
        ordering = ['documento', 'id']