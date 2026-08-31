from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.chat, name='chat'),
    path('subir-documento/', views.subir_documento, name='subir_documento'),
    path('chat-con-documentos/', views.chat_con_documentos, name='chat_con_documentos')
]