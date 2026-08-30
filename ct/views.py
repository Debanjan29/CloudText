from django.shortcuts import render,HttpResponse,redirect,HttpResponseRedirect
from . models import Store
from django.contrib import messages
# Create your views here.

import uuid

# === 2026 update! ===
import base64
import zipfile
import io
import os
from datetime import timedelta
from django.utils.timezone import now
from django.http import Http404

from django.db.models import Sum

def get_total_db_storage_bytes():
    """Calculates total file storage size in bytes for all stored files."""
    try:
        total = Store.objects.filter(is_file=True).aggregate(Sum('file_size'))['file_size__sum']
        return total or 0
    except Exception:
        return 0

def cleanup_expired_files(incoming_file_size=0):
    """
    === 2026 update! Conditional 30-Day Cleanup Strategy ===
    Purges file records (is_file=True) older than 30 days based on 'date' stored in DB
    IFF:
      1. Total DB file storage is above 400 MB (400 * 1024 * 1024 bytes), OR
      2. Incoming file to be stored is >= 200 MB (200 * 1024 * 1024 bytes).
    Otherwise, 30-day-old files are NOT deleted.
    CRITICAL REQUIREMENT: Text data (is_file=False) is NEVER deleted!
    """
    try:
        total_storage = get_total_db_storage_bytes()
        mb_400 = 400 * 1024 * 1024
        mb_200 = 200 * 1024 * 1024

        should_cleanup = (total_storage > mb_400) or (incoming_file_size >= mb_200)

        if should_cleanup:
            cutoff_date = now() - timedelta(days=30)
            Store.objects.filter(is_file=True, date__lt=cutoff_date).delete()
    except Exception as e:
        print("Cleanup error:", e)

def format_file_size(size_bytes):
    if not size_bytes:
        return "0 B"
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
# === 2026 update! ===

# === SECURITY MEASURES 2026: File Name Sanitization & Path Traversal Guard ===
# Explanation: Strips dangerous path characters (../, ..\) and invalid characters from uploaded file names using Django's get_valid_filename to prevent Zip Slip and directory traversal attacks.
from django.utils.text import get_valid_filename

def sanitize_filename(filename):
    if not filename:
        return "cloudtext_file"
    clean_name = os.path.basename(filename)
    clean_name = get_valid_filename(clean_name)
    return clean_name or "cloudtext_file"
# === SECURITY MEASURES 2026 ===

# === SECURITY MEASURES 2026: IP-Based Rate Limiter (Max 7 requests/min per IP) ===
# Explanation: Prevents automated brute-force 4-digit code enumeration and DoS storage spamming by tracking request timestamps per IP address (Max 7 requests/min per IP).
IP_REQUEST_LOG = {}

def is_rate_limited(request, max_requests=7, window_seconds=60):
    client_ip = request.META.get('HTTP_X_FORWARDED_FOR')
    if client_ip:
        client_ip = client_ip.split(',')[0].strip()
    else:
        client_ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    
    current_time = now().timestamp()
    timestamps = IP_REQUEST_LOG.get(client_ip, [])
    timestamps = [t for t in timestamps if current_time - t < window_seconds]
    
    if len(timestamps) >= max_requests:
        return True
    
    timestamps.append(current_time)
    IP_REQUEST_LOG[client_ip] = timestamps
    return False
# === SECURITY MEASURES 2026 ===

def generate_unique_id():
    # Generate a random UUID
    unique_id = uuid.uuid4()

    # Extract the first 4 characters to get a 4-digit ID
    return str(unique_id)[:4]

def contains_alphabet(s):
    for char in s:
        if char.isalpha():
            return True
    return False

# Usage example
def create():
  id=generate_unique_id()
  if(contains_alphabet(id)==False) :
    return(id[0:3]+'p')
  else:
    return(id)


def about(request):
    return render(request,"About.html")

def save(request):
    if request.method=="POST":
        # === SECURITY MEASURES 2026: IP Rate Limit Guard ===
        if is_rate_limited(request, max_requests=7, window_seconds=60):
            messages.error(request, "Rate limit exceeded (Max 7 requests per minute). Please wait a minute before trying again.")
            return render(request, "save1.html")
        # === SECURITY MEASURES 2026 ===

        # === 2026 update! ===
        uploaded_files = request.FILES.getlist("file_upload")
        msgs = request.POST.get("content", "")

        incoming_file_size = sum(f.size for f in uploaded_files) if uploaded_files else 0
        cleanup_expired_files(incoming_file_size=incoming_file_size)
        # === 2026 update! ===

        if uploaded_files:
            val = 1
            s = create()
            while Store.objects.filter(id=s).exists():
                s = create()

            if len(uploaded_files) == 1:
                file_obj = uploaded_files[0]
                content_type = file_obj.content_type or ""
                raw_filename = file_obj.name
                
                # === SECURITY MEASURES 2026: Sanitize Filename ===
                filename = sanitize_filename(raw_filename)
                # === SECURITY MEASURES 2026 ===

                # Check if image
                is_img = content_type.startswith("image/") or filename.lower().endswith(
                    ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg')
                )

                if is_img:
                    # NO COMPRESSION FOR PICS - Preserve 100% original quality
                    raw_bytes = file_obj.read()
                    file_type = content_type or "image/png"
                    save_name = filename
                else:
                    if filename.lower().endswith('.zip'):
                        raw_bytes = file_obj.read()
                        file_type = "application/zip"
                        save_name = filename
                    else:
                        in_mem_zip = io.BytesIO()
                        with zipfile.ZipFile(in_mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                            file_bytes = file_obj.read()
                            zf.writestr(filename, file_bytes)
                        raw_bytes = in_mem_zip.getvalue()
                        file_type = "application/zip"
                        save_name = f"{os.path.splitext(filename)[0]}.zip"
            else:
                # Multiple files / Folder drop: Package into ZIP archive lossless
                in_mem_zip = io.BytesIO()
                with zipfile.ZipFile(in_mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                    for f in uploaded_files:
                        # === SECURITY MEASURES 2026: Sanitize Relative Path ===
                        clean_rel_path = sanitize_filename(f.name)
                        zf.writestr(clean_rel_path, f.read())
                        # === SECURITY MEASURES 2026 ===
                raw_bytes = in_mem_zip.getvalue()
                file_type = "application/zip"
                save_name = "cloudtext_files.zip"

            st = Store(
                msg=msgs if msgs else save_name,
                id=s,
                is_file=True,
                file_data=raw_bytes,
                file_name=save_name,
                file_size=len(raw_bytes),
                file_type=file_type
            )
            st.save()
            params = {'uuid': s, 'val': val}
            messages.success(request, "Your unique code is ")
            return render(request, "save1.html", params)
        # === 2026 update! ===

        # Legacy text save handling
        if msgs==" " or msgs=="" or msgs=="  ":
            return render(request,'save1.html')
        else:
            val=1
            s=create()
            while(Store.objects.filter(id=s).exists()):
                s=create()
            st=Store(msg=msgs,id=s,is_file=False)
            st.save()
            params={'uuid':s , 'val':val}
            messages.success(request,"Your unique code is ")
            msgs=''
            return render(request,"save1.html",params)
    
    return render(request,"save1.html")

def get(request):#search
    # === 2026 update! ===
    cleanup_expired_files()
    # === 2026 update! ===

    if request.method=="POST":
        # === SECURITY MEASURES 2026: IP Rate Limit Guard ===
        if is_rate_limited(request, max_requests=7, window_seconds=60):
            messages.error(request, "Rate limit exceeded (Max 7 requests per minute). Please wait a minute before trying again.")
            return render(request, "save1.html", {'val2': 1})
        # === SECURITY MEASURES 2026 ===

        uid=request.POST["query"]
        uid=uid.lower()#Converting input into LowerCase
        print(uid)
        val2=1
        param={ 'val2':val2}
        if(len(uid)>6):
            messages.error(request,"Invalid Code")
            return render(request,"save1.html",param)
        else:
            q=Store.objects.filter(id=uid).first()
            if not q:
                messages.error(request,"Code not found")
                return render(request,"save1.html",param)

            # === 2026 update! ===
            is_image = False
            image_b64 = ""
            formatted_size = "0 B"
            zip_file_list = []
            image_gallery = []

            if q.is_file and q.file_data:
                file_bytes = bytes(q.file_data)
                formatted_size = format_file_size(q.file_size or len(file_bytes))
                
                if q.file_type and q.file_type.startswith("image/"):
                    is_image = True
                    image_b64 = base64.b64encode(file_bytes).decode("utf-8")
                elif q.file_type == "application/zip" or (q.file_name and q.file_name.endswith(".zip")):
                    try:
                        with zipfile.ZipFile(io.BytesIO(file_bytes), mode="r") as zf:
                            for info in zf.infolist():
                                if not info.is_dir():
                                    zip_file_list.append({
                                        'name': info.filename,
                                        'size': format_file_size(info.file_size)
                                    })
                                    ext = info.filename.lower()
                                    if ext.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg')):
                                        try:
                                            img_bytes = zf.read(info.filename)
                                            mime = "image/png"
                                            if ext.endswith(('.jpg', '.jpeg')): mime = "image/jpeg"
                                            elif ext.endswith('.gif'): mime = "image/gif"
                                            elif ext.endswith('.webp'): mime = "image/webp"
                                            elif ext.endswith('.svg'): mime = "image/svg+xml"
                                            img_b64 = base64.b64encode(img_bytes).decode("utf-8")
                                            image_gallery.append({
                                                'name': info.filename,
                                                'mime': mime,
                                                'b64': img_b64
                                            })
                                        except Exception as e_img:
                                            print("Image extract error:", e_img)
                    except Exception as e_zip:
                        print("Zip inspect error:", e_zip)

            param = {
                'msgg': q,
                'is_file': q.is_file,
                'is_image': is_image,
                'image_b64': image_b64,
                'formatted_size': formatted_size,
                'zip_file_list': zip_file_list,
                'image_gallery': image_gallery
            }
            # === 2026 update! ===
            print(q)
            return render(request,"result1.html",param)
    else:
        return redirect('/')

# === 2026 update! ===
def download_file(request, id):
    uid = id.lower()
    st = Store.objects.filter(id=uid).first()
    if not st or not st.is_file or not st.file_data:
        raise Http404("File not found")
    
    # === SECURITY MEASURES 2026: Stored XSS Prevention & Security Headers ===
    # Explanation: Forces Content-Disposition: attachment and X-Content-Type-Options: nosniff header so browsers never execute scripts in uploaded .html/.svg files in the user's browser context.
    response = HttpResponse(bytes(st.file_data), content_type=st.file_type or 'application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{st.file_name or "download"}"'
    response['X-Content-Type-Options'] = 'nosniff'
    return response
    # === SECURITY MEASURES 2026 ===
# === 2026 update! ===
        