"""Embedding collection for the util embedding experiments.
Pick a model; embed_dataset() dispatches to the OpenAI API or a local open-weight model
depending on which list the model name is in. Each (dataset, model) pair gets its own
on-disk cache file under data/ (gitignored): if it exists, it's loaded as-is and nothing
is re-embedded; if not, everything is embedded and saved. So `dataset` must be a stable
name for one exact set of texts (e.g. one subset/label) - reusing it for a different
text set will silently return the wrong cached vectors.
Call embed_dataset(texts, dataset=..., model=...) -> {text: unit vector}.
"""
import json, urllib.request
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"; DATA.mkdir(exist_ok=True)

OPENAI_MODELS = ["text-embedding-3-large"]
QWEN_MODELS = ["Qwen/Qwen3-Embedding-4B"]


def _unit(v):
    v = np.asarray(v, dtype=np.float32)
    return v / (np.linalg.norm(v) + 1e-9)


def _cache_path(dataset, model):
    return DATA / f"{dataset}_{model.replace('/', '_')}.npz"


def _load_cache(path):
    if path.exists():
        z = np.load(path, allow_pickle=True)
        return {t: v for t, v in zip(z["texts"], z["vecs"])}
    return {}


def _save_cache(path, cache):
    # every vector in one cache file has the same dim, so stack into a plain (N, dim)
    # float32 array - no dtype=object needed, and it can't accidentally bloat like one can.
    vecs = np.stack([np.asarray(v, dtype=np.float32) for v in cache.values()])
    tmp = path.with_name(path.stem + ".tmp.npz")  # np.savez always appends .npz to bare names
    np.savez(tmp, texts=np.array(list(cache.keys()), dtype=object), vecs=vecs)
    tmp.replace(path)  # atomic - readers never see a torn/partial write


# ---------------- OpenAI models (HTTP API) ----------------
def _embed_openai(texts, dataset, model, api_key, batch=100):
    path = _cache_path(dataset, model)
    if path.exists():
        cache = _load_cache(path)
        return {str(t): _unit(cache[str(t)]) for t in texts}
    if not api_key:
        raise ValueError(f"model {model!r} needs api_key=... (an OpenAI API key)")
    texts = [str(t) for t in texts]
    print(f"[{model}] embedding {len(texts)} texts for {dataset!r}")
    cache = {}
    for i in range(0, len(texts), batch):
        chunk = texts[i:i + batch]
        req = urllib.request.Request(
            "https://api.openai.com/v1/embeddings",
            data=json.dumps({"input": chunk, "model": model}).encode(),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"})
        r = json.load(urllib.request.urlopen(req, timeout=60))
        for t, d in zip(chunk, r["data"]):
            cache[t] = np.array(d["embedding"], dtype=np.float32)
    _save_cache(path, cache)
    print(f"[{model}] done, cache={len(cache)}")
    return {t: _unit(v) for t, v in cache.items()}


# ---------------- local open-weight models (transformers, GPU) ----------------
_loaded_models = {}  # avoids reloading a multi-GB model on every embed_dataset() call

def _load_open_weight(model):
    if model not in _loaded_models:
        tok = AutoTokenizer.from_pretrained(model, padding_side="left")
        mdl = AutoModel.from_pretrained(model, dtype=torch.bfloat16, device_map="cuda").eval()
        _loaded_models[model] = (mdl, tok)
    return _loaded_models[model]


def _embed_open_weight(texts, dataset, model, batch=16, max_len=2048):
    path = _cache_path(dataset, model)
    if path.exists():
        cache = _load_cache(path)
        return {str(t): _unit(cache[str(t)]) for t in texts}
    texts = [str(t) for t in texts]
    mdl, tok = _load_open_weight(model)
    print(f"[{model}] embedding {len(texts)} texts for {dataset!r}")
    cache = {}
    with torch.no_grad():
        for i in range(0, len(texts), batch):
            chunk = texts[i:i + batch]
            b = tok(chunk, padding=True, truncation=True, max_length=max_len, return_tensors="pt").to("cuda")
            out = mdl(**b)
            last_token = out.last_hidden_state[:, -1]  # tokenizer uses padding_side="left", so this is always the real last token
            emb = F.normalize(last_token, p=2, dim=1).float().cpu().numpy()
            for t, v in zip(chunk, emb):
                cache[t] = v.astype(np.float32)
    _save_cache(path, cache)
    print(f"[{model}] done, cache={len(cache)}")
    return {t: _unit(v) for t, v in cache.items()}


def embed_dataset(texts, dataset, model=OPENAI_MODELS[0], api_key=None, **kw):
    if model in OPENAI_MODELS:
        return _embed_openai(texts, dataset, model, api_key, **kw)
    if model in QWEN_MODELS:
        return _embed_open_weight(texts, dataset, model, **kw)
    raise ValueError(f"unknown model {model!r} - known: {OPENAI_MODELS + QWEN_MODELS}")
