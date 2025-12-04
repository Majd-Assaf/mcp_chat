import os
import json
import mimetypes
from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse, Http404
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from .models import Document
from django.core.files.storage import default_storage

import requests

# Optional PDF text extraction
try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None

def index(request):
    docs = Document.objects.order_by("-uploaded_at")
    return render(request, "chatapp/chat.html", {"docs": docs})

@require_POST
def upload_document(request):
    f = request.FILES.get("file")
    title = request.POST.get("title") or (getattr(f, "name", "uploaded"))
    if not f:
        return HttpResponseBadRequest("No file uploaded.")
    doc = Document.objects.create(title=title, file=f)
    # try to extract text
    extracted = ""
    try:
        _, ext = os.path.splitext(doc.file.name.lower())
        if ext == ".pdf" and PdfReader:
            path = doc.file.path
            reader = PdfReader(path)
            texts = []
            for p in reader.pages:
                texts.append(p.extract_text() or "")
            extracted = "\n".join(texts)
        else:
            # read as text if small
            path = doc.file.path
            with open(path, "rb") as fh:
                raw = fh.read()
            try:
                extracted = raw.decode("utf-8", errors="replace")
            except Exception:
                extracted = ""
    except Exception:
        extracted = ""
    doc.extracted_text = extracted
    doc.save()
    return redirect("/")

# ---------------- MCP endpoints ----------------
@require_GET
def mcp_manifest(request):
    """
    Very small MCP-like manifest: describes available resources/documents.
    Agent can call /mcp/document/<id>/ to fetch content.
    """
    docs = Document.objects.order_by("-uploaded_at")
    items = []
    for d in docs:
        items.append({
            "id": str(d.id),
            "title": d.title,
            "uploaded_at": d.uploaded_at.isoformat(),
            "mcp_document_url": request.build_absolute_uri(f"/mcp/document/{d.id}/"),
            # a short summary we can expose
            "summary": (d.extracted_text[:300] + "...") if d.extracted_text else "",
        })
    manifest = {
        "name": "chatapp-document-store",
        "description": "Documents uploaded by users; simple MCP manifest exposing doc metadata & URLs.",
        "resources": items,
    }
    return JsonResponse(manifest)

@require_GET
def mcp_document(request, doc_id):
    """
    Return the content for a document. In a real MCP server you'd follow the
    MCP spec exactly (schemas, auth, streaming, etc). This is a simple JSON
    endpoint returning the extracted_text and download link.
    """
    try:
        d = Document.objects.get(pk=doc_id)
    except Document.DoesNotExist:
        raise Http404("Document not found.")
    data = {
        "id": str(d.id),
        "title": d.title,
        "uploaded_at": d.uploaded_at.isoformat(),
        "extracted_text": d.extracted_text,
        "download_url": request.build_absolute_uri(d.file.url),
    }
    return JsonResponse(data)

# ---------------- Chat endpoint ----------------
@csrf_exempt
@require_POST
def chat_send(request):
    """
    Accepts JSON: { "message": "..." , "include_doc_ids": [1,2] }
    It will fetch the selected docs, assemble a context payload and forward
    to the configured AI_AGENT_API_URL. It returns the agent response.
    """
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    user_message = payload.get("message", "").strip()
    if not user_message:
        return HttpResponseBadRequest("Empty message")

    include_doc_ids = payload.get("include_doc_ids") or []
    # fallback: we may pick top N recent docs if none requested
    if not include_doc_ids:
        docs = list(Document.objects.order_by("-uploaded_at")[: settings.AI_CONTEXT_MAX_DOCS])
    else:
        docs = list(Document.objects.filter(id__in=include_doc_ids).order_by("-uploaded_at"))

    # assemble context: a simple list of dicts
    context_items = []
    for d in docs:
        context_items.append({
            "id": str(d.id),
            "title": d.title,
            "text": d.extracted_text or "",
            "mcp_url": request.build_absolute_uri(f"/mcp/document/{d.id}/")
        })

    # Build the forwarded payload. The exact shape depends on your agent API.
    # We include an "mcp_context" object so the agent knows these docs came from an MCP server.
    forward_payload = {
        "input": user_message,
        "mcp_context": {
            "source": request.build_absolute_uri("/mcp/manifest/"),
            "documents": context_items,
        },
        "metadata": {"via": "mcp_chat_app"}
    }

    agent_url = getattr(settings, "AI_AGENT_API_URL", None)
    agent_auth = getattr(settings, "AI_AGENT_API_AUTH", None)
    if not agent_url:
        return HttpResponse("AI agent URL not configured. Set AI_AGENT_API_URL in settings.", status=500)

    headers = {"Content-Type": "application/json"}
    if agent_auth:
        # if AI_AGENT_API_AUTH is "Bearer xxx" or "ApiKey xxx", pass directly
        headers["Authorization"] = agent_auth

    try:
        resp = requests.post(agent_url, json=forward_payload, headers=headers, timeout=30)
    except requests.RequestException as e:
        return JsonResponse({"error": "failed to contact agent", "details": str(e)}, status=502)

    # forward the agent response (try to preserve JSON if possible)
    try:
        agent_json = resp.json()
        return JsonResponse({"agent_response": agent_json, "mcp_sent": forward_payload})
    except Exception:
        return HttpResponse(resp.content, status=resp.status_code, content_type=resp.headers.get("Content-Type", "text/plain"))
