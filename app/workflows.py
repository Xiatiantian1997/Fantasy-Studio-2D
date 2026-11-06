"""Minimal SDXL/Illustrious/RealVisXL workflows for ComfyUI core nodes."""
from __future__ import annotations

import secrets

SIZES = {
    "portrait": (768, 1152),
    "square": (1024, 1024),
    "landscape": (1152, 768),
    "wallpaper": (832, 1216),
}


def build_workflow(spec: dict) -> dict:
    """Validate a request and return the ComfyUI API-formatted graph."""
    checkpoint = spec.get("checkpoint")
    if not isinstance(checkpoint, str) or not checkpoint.strip() or len(checkpoint) > 300:
        raise ValueError("请先选择模型。")
    prompt = spec.get("prompt", "")
    negative = spec.get("negative", "")
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 5000:
        raise ValueError("请输入提示词（上限 5000 字符）。")
    if not isinstance(negative, str) or len(negative) > 5000:
        raise ValueError("负面提示词过长。")
    size_key = spec.get("size", "portrait")
    if size_key not in SIZES:
        raise ValueError("不支持的尺寸。")
    width, height = SIZES[size_key]
    try:
        steps = int(spec.get("steps", 28))
        cfg = float(spec.get("cfg", 6))
        seed_arg = spec.get("seed", "")
        seed = secrets.randbelow(2**53) if seed_arg in ("", None) else int(seed_arg)
        strength = float(spec.get("strength", 0.55))
        lora_strength = float(spec.get("lora_strength", 0.75))
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("生成参数格式不正确。") from exc
    if not 5 <= steps <= 60 or not 1 <= cfg <= 15 or not 0 <= seed < 2**53:
        raise ValueError("步数、CFG 或种子超出允许范围。")
    if not 0.1 <= strength <= 1.0 or not 0 <= lora_strength <= 1.5:
        raise ValueError("重绘幅度或 LoRA 强度超出范围。")
    mode = spec.get("mode", "txt2img")
    if mode not in ("txt2img", "img2img"):
        raise ValueError("未知生成模式。")
    lora = spec.get("lora", "")
    if not isinstance(lora, str) or len(lora) > 300:
        raise ValueError("LoRA 名称不正确。")

    graph = {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": checkpoint}},
    }
    model_src = ["1", 0]
    clip_src = ["1", 1]
    if lora:
        graph["10"] = {"class_type": "LoraLoader", "inputs": {
            "lora_name": lora, "strength_model": lora_strength,
            "strength_clip": lora_strength, "model": model_src, "clip": clip_src,
        }}
        model_src = ["10", 0]
        clip_src = ["10", 1]

    graph.update({
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": clip_src}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": clip_src}},
    })
    if mode == "img2img":
        upload_name = spec.get("upload_name", "")
        if not isinstance(upload_name, str) or not upload_name.startswith("studio_") or len(upload_name) > 100:
            raise ValueError("请先上传参考图。")
        graph["4"] = {"class_type": "LoadImage", "inputs": {"image": upload_name}}
        graph["8"] = {"class_type": "ImageScale", "inputs": {
            "image": ["4", 0], "upscale_method": "lanczos",
            "width": width, "height": height, "crop": "center",
        }}
        graph["9"] = {"class_type": "VAEEncode", "inputs": {
            "pixels": ["8", 0], "vae": ["1", 2],
        }}
        latent_src = ["9", 0]
        denoise = strength
    else:
        graph["4"] = {"class_type": "EmptyLatentImage", "inputs": {
            "width": width, "height": height, "batch_size": 1,
        }}
        latent_src = ["4", 0]
        denoise = 1.0

    graph["5"] = {"class_type": "KSampler", "inputs": {
        "seed": seed, "steps": steps, "cfg": cfg,
        "sampler_name": "euler", "scheduler": "normal", "denoise": denoise,
        "model": model_src, "positive": ["2", 0],
        "negative": ["3", 0], "latent_image": latent_src,
    }}
    graph["6"] = {"class_type": "VAEDecode", "inputs": {
        "samples": ["5", 0], "vae": ["1", 2],
    }}
    graph["7"] = {"class_type": "SaveImage", "inputs": {
        "filename_prefix": "LocalStudio", "images": ["6", 0],
    }}
    return graph
