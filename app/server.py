"""Loopback-only UI and ComfyUI API bridge. Python standard library only."""
from __future__ import annotations

import base64
import binascii
import json
import os
import re
import sys
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
COMFY = os.environ.get("STUDIO_COMFY_URL", "http://127.0.0.1:8190").rstrip("/")
PORT = int(os.environ.get("STUDIO_PORT", "7865"))
MAX_JSON = 20 * 1024 * 1024
WEB = ROOT / "web" / "index.html"


class BridgeError(Exception):
    pass


def comfy_get(path: str, timeout=8):
    try:
        with urlopen(COMFY + path, timeout=timeout) as response:
            return json.loads(response.read())
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        raise BridgeError("ComfyUI 无法连接或返回异常，请确认后端已经启动。") from exc


def comfy_post(path: str, data: bytes, content_type="application/json", timeout=90):
    req = Request(COMFY + path, data=data, headers={"Content-Type": content_type}, method="POST")
    try:
        with urlopen(req, timeout=timeout) as response:
            return json.loads(response.read())
    except HTTPError as exc:
        message = exc.read(2000).decode("utf-8", "replace")
        raise BridgeError(f"后端拒绝任务：{message[:700]}") from exc
    except (URLError, TimeoutError, ValueError) as exc:
        raise BridgeError("无法发送请求到 ComfyUI。") from exc


def available_models(folder):
    value = comfy_get("/models/" + folder)
    if isinstance(value, list):
        return [v for v in value if isinstance(v, str)]
    return []


def upload_reference(data_url: str):
    if not isinstance(data_url, str) or "," not in data_url:
        raise ValueError("图片内容无效。")
    prefix, b64 = data_url.split(",", 1)
    extensions = {
        "data:image/png;base64": ("png", b"\x89PNG\r\n\x1a\n"),
        "data:image/jpeg;base64": ("jpg", b"\xff\xd8\xff"),
        "data:image/webp;base64": ("webp", b"RIFF"),
    }
    if prefix not in extensions or len(b64) > 15_000_000:
        raise ValueError("仅支持 10 MB 以内的 PNG/JPG/WebP。")
    try:
        raw = base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("图片编码不正确。") from exc
    ext, magic = extensions[prefix]
    if not raw.startswith(magic) or len(raw) > 10 * 1024 * 1024 or len(raw) < 50:
        raise ValueError("文件格式或大小不正确。")
    if ext == "webp" and raw[8:12] != b"WEBP":
        raise ValueError("WebP 格式不正确。")
    name = f"studio_{uuid.uuid4().hex}.{ext}"
    boundary = "----LocalStudio" + uuid.uuid4().hex
    b = boundary.encode("ascii")
    body = (b"--" + b + b"\r\n"
            + f'Content-Disposition: form-data; name="image"; filename="{name}"\r\n'.encode()
            + f"Content-Type: image/{'jpeg' if ext == 'jpg' else ext}\r\n\r\n".encode()
            + raw + b"\r\n--" + b + b"--\r\n")
    result = comfy_post("/upload/image", body, f"multipart/form-data; boundary={boundary}")
    returned = result.get("name", "")
    if returned != name:
        raise BridgeError("后端上传结果与请求不一致。")
    return name


class Handler(BaseHTTPRequestHandler):
    server_version = "LocalStudio/1.0"

    def log_message(self, fmt, *args):
        sys.stdout.write("[UI] " + (fmt % args) + "\n")

    def send(self, status, payload, mime="application/json; charset=utf-8"):
        if isinstance(payload, (dict, list)):
            payload = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        elif isinstance(payload, str):
            payload = payload.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        parsed = urlparse(self.path)
        try:
            if parsed.path in ("/", "/index.html"):
                return self.send(200, WEB.read_bytes(), "text/html; charset=utf-8")
            if parsed.path == "/api/status":
                try:
                    stats = comfy_get("/system_stats", timeout=2)
                    return self.send(200, {"ready": True, "devices": stats.get("devices", [])})
                except BridgeError:
                    return self.send(200, {"ready": False})
            if parsed.path == "/api/models":
                return self.send(200, {
                    "checkpoints": available_models("checkpoints"),
                    "loras": available_models("loras"),
                })
            if parsed.path == "/api/job":
                prompt_id = parse_qs(parsed.query).get("id", [""])[0]
                if not re.fullmatch(r"[0-9a-fA-F-]{36}", prompt_id):
                    raise ValueError("任务编号不正确。")
                data = comfy_get("/history/" + prompt_id)
                job = data.get(prompt_id)
                if not job:
                    return self.send(200, {"state": "running"})
                images = []
                for node in job.get("outputs", {}).values():
                    for entry in node.get("images", []):
                        if entry.get("type") == "output":
                            qs = urlencode({"filename": entry["filename"], "subfolder": entry.get("subfolder", ""), "type": "output"})
                            images.append("/api/image?" + qs)
                if images:
                    return self.send(200, {"state": "done", "images": images})
                errors = job.get("status", {}).get("messages", [])
                is_failed = job.get("status", {}).get("status_str") == "error"
                return self.send(200, {"state": "error" if is_failed else "running", "message": str(errors)[-700:] if is_failed else ""})
            if parsed.path == "/api/image":
                query = parse_qs(parsed.query)
                filename = query.get("filename", [""])[0]
                subfolder = query.get("subfolder", [""])[0]
                if not re.fullmatch(r"[\w .()\-]{1,255}\.(png|jpg|jpeg|webp)", filename, flags=re.I):
                    raise ValueError("图片文件名无效。")
                if subfolder and (not re.fullmatch(r"[\w\-/]{1,120}", subfolder) or ".." in subfolder):
                    raise ValueError("图片目录无效。")
                qs = urlencode({"filename": filename, "subfolder": subfolder, "type": "output"})
                try:
                    with urlopen(COMFY + "/view?" + qs, timeout=30) as response:
                        raw = response.read(25 * 1024 * 1024 + 1)
                        ctype = response.headers.get("Content-Type", "image/png")
                    if len(raw) > 25 * 1024 * 1024:
                        raise ValueError("图片过大。")
                    return self.send(200, raw, ctype if ctype.startswith("image/") else "image/png")
                except (HTTPError, URLError) as exc:
                    raise BridgeError("无法读取生成图片。") from exc
            return self.send(404, {"error": "地址不存在。"})
        except ValueError as exc:
            return self.send(400, {"error": str(exc)})
        except BridgeError as exc:
            return self.send(502, {"error": str(exc)})
        except Exception as exc:
            print("GET error:", repr(exc))
            return self.send(500, {"error": "内部错误，请查看启动窗口。"})

    def do_POST(self):
        try:
            if self.path not in ("/api/upload", "/api/generate", "/api/interrupt"):
                return self.send(404, {"error": "地址不存在。"})
            if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                raise ValueError("请求格式必须为 JSON。")
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_JSON:
                raise ValueError("请求内容太大或为空。")
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise ValueError("参数不是对象。")
            if self.path == "/api/upload":
                name = upload_reference(body.get("data", ""))
                return self.send(200, {"name": name})
            if self.path == "/api/interrupt":
                comfy_post("/interrupt", b"{}")
                return self.send(200, {"ok": True})
            from workflows import build_workflow
            checkpoints = available_models("checkpoints")
            if body.get("checkpoint") not in checkpoints:
                raise ValueError("选择的模型未安装或未刷新模型列表。")
            loras = available_models("loras")
            if body.get("lora") and body["lora"] not in loras:
                raise ValueError("选择的 LoRA 不存在。")
            graph = build_workflow(body)
            result = comfy_post("/prompt", json.dumps({"prompt": graph, "client_id": uuid.uuid4().hex}).encode("utf-8"))
            prompt_id = result.get("prompt_id")
            if not prompt_id:
                raise BridgeError("后端没有返回任务编号：" + str(result)[:500])
            return self.send(200, {"id": prompt_id})
        except (ValueError, json.JSONDecodeError) as exc:
            return self.send(400, {"error": str(exc)})
        except BridgeError as exc:
            return self.send(502, {"error": str(exc)})
        except Exception as exc:
            print("POST error:", repr(exc))
            return self.send(500, {"error": "内部错误，请查看启动窗口。"})


def main():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"[LocalStudio] 中文界面：http://127.0.0.1:{PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
