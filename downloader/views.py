import os
import re
import uuid
import json
import threading
import tempfile
import urllib.parse
import traceback
from django.shortcuts import render
from django.http import JsonResponse, FileResponse, HttpResponse
from yt_dlp import YoutubeDL

TEMP_DIR = os.path.join(tempfile.gettempdir(), "yt_downloader")
os.makedirs(TEMP_DIR, exist_ok=True)

ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


def clean_youtube_url(url: str) -> str:
    """Приводим ссылку к стандартному виду"""
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    video_id = query.get('v', [None])[0]

    if not video_id:
        match = re.search(r'youtu\.be/([0-9A-Za-z_-]{11})', url)
        if match:
            video_id = match.group(1)

    if not video_id:
        return None

    return f"https://www.youtube.com/watch?v={video_id}"


def get_formats(request):
    """Возвращает список доступных форматов для данного видео"""
    url = request.GET.get("url")
    if not url:
        return JsonResponse({"error": "URL не указан"}, status=400)

    cleaned = clean_youtube_url(url)
    if not cleaned:
        return JsonResponse({"error": "Неверная ссылка"}, status=400)

    try:
        ydl_opts = {"quiet": True, "skip_download": True}
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(cleaned, download=False)
            formats = info.get("formats", [])
    except Exception as e:
        print(f"[get_formats] Ошибка при получении форматов: {e}")
        return JsonResponse({"error": str(e)}, status=500)

    # Преобразуем данные о форматах
    formats_list = []
    for f in formats:
        # resolution может быть '720p', '1080p', или отсутствовать
        res = f.get("format_note") or f.get("height") or "unknown"
        if isinstance(res, int):
            res_str = f"{res}p"
            res_val = res
        elif isinstance(res, str) and res.endswith("p"):
            try:
                res_val = int(res.replace("p", ""))
            except ValueError:
                res_val = 0
            res_str = res
        else:
            res_val = 0
            res_str = str(res)

        # фильтруем только видео (без аудио-only)
        if not f.get("vcodec") or f["vcodec"] == "none":
            continue

        formats_list.append({
            "format_id": f.get("format_id"),
            "ext": f.get("ext"),
            "resolution": res_str,
            "res_val": res_val,
            "filesize": f.get("filesize") or f.get("filesize_approx"),
        })

    # Сортируем по числовому значению разрешения
    formats_list.sort(key=lambda x: x.get("res_val", 0), reverse=True)

    return JsonResponse({"formats": formats_list})


def start_download(task_id: str, url: str, format_id: str = None):
    """Фоновая загрузка видео (с автоматическим объединением звука)"""
    progress_file = os.path.join(TEMP_DIR, f"{task_id}.json")
    file_info_file = os.path.join(TEMP_DIR, f"{task_id}_file.json")

    print(f"[{task_id}] ▶ start_download for {url} (format_id={format_id})")

    def progress_hook(d):
        try:
            status = d.get('status')
            if status == 'downloading':
                raw_percent = d.get('_percent_str') or d.get('percent') or '0.0'
                clean = ANSI_ESCAPE.sub('', str(raw_percent))
                clean = clean.replace('%', '').strip()
                try:
                    value = float(clean)
                except ValueError:
                    value = 0.0
                with open(progress_file, 'w') as f:
                    json.dump({'progress': value}, f)
            elif status == 'finished':
                with open(progress_file, 'w') as f:
                    json.dump({'progress': 100.0}, f)
        except Exception as hook_exc:
            print(f"[{task_id}] Exception in progress_hook: {hook_exc}")

    # --- выбираем корректный формат ---
    if format_id:
        fmt = f"{format_id}+bestaudio/best"  # 👈 добавляем звук!
    else:
        fmt = "bestvideo+bestaudio/best"

    try:
        ydl_opts = {
            'format': fmt,
            'merge_output_format': 'mp4',
            'outtmpl': os.path.join(TEMP_DIR, f"{task_id}.%(ext)s"),
            'progress_hooks': [progress_hook],
            'quiet': True,
            'noplaylist': True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=True)
            except Exception as e:
                print(f"[{task_id}] ❗ Primary format failed: {e}")
                # пробуем fallback формат
                ydl.params['format'] = 'best'
                info = ydl.extract_info(url, download=True)

            title = info.get('title', f'video_{task_id}')
            ext = info.get('ext', 'mp4')

        filename = os.path.join(TEMP_DIR, f"{task_id}.{ext}")
        with open(file_info_file, 'w') as f:
            json.dump({'filename': filename, 'title': title}, f)

        print(f"[{task_id}] ✅ Download complete: {filename}")

    except Exception as e:
        import traceback
        print(f"[{task_id}] ❌ Exception in start_download: {e}")
        traceback.print_exc()
        with open(progress_file, 'w') as f:
            json.dump({'progress': 'error', 'message': str(e)}, f)




def index(request):
    if request.method == 'POST':
        url = request.POST.get('url')
        format_id = request.POST.get('format_id')  # 👈 новый параметр
        cleaned = clean_youtube_url(url)

        if not cleaned:
            return JsonResponse({'error': 'Неверная ссылка'}, status=400)

        task_id = str(uuid.uuid4())
        thread = threading.Thread(target=start_download, args=(task_id, cleaned, format_id))
        thread.daemon = True
        thread.start()

        return JsonResponse({'task_id': task_id})

    return render(request, 'downloader/index.html')



def get_progress(request, task_id):
    progress_file = os.path.join(TEMP_DIR, f"{task_id}.json")
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r') as f:
                data = json.load(f)
            return JsonResponse(data)
        except json.JSONDecodeError:
            return JsonResponse({'progress': 0.0})
    return JsonResponse({'progress': 0.0})


def download_file(request, task_id):
    file_info_file = os.path.join(TEMP_DIR, f"{task_id}_file.json")
    if not os.path.exists(file_info_file):
        return HttpResponse("Файл ещё не готов.", status=404)

    with open(file_info_file, 'r') as f:
        data = json.load(f)

    file_path = data.get('filename')
    title = re.sub(r'[\\/*?:"<>|]', "_", data.get('title', 'video'))
    ext = file_path.split('.')[-1] if file_path else 'mp4'
    final_name = f"{title}.{ext}"

    if file_path and os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=final_name)
    return HttpResponse("Файл не найден.", status=404)
