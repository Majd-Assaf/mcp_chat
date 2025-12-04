from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("upload/", views.upload_document, name="upload"),
    path("mcp/manifest/", views.mcp_manifest, name="mcp_manifest"),
    path("mcp/document/<int:doc_id>/", views.mcp_document, name="mcp_document"),
    path("chat/send/", views.chat_send, name="chat_send"),
]
