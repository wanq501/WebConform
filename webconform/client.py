"""One call to a model behind an OpenAI-compatible chat completions API (vLLM, a provider, or a gateway), with retries."""
import base64, json, time, urllib.error, urllib.request

def chat(base_url, model, system, text, image=None, api_key=None, temperature=0, max_tokens=4096, timeout=120, retries=5, extra=None):
    """returns (answer text, usage, latency in seconds, attempts); raises RuntimeError after the last failed attempt"""
    content = [{"type": "text", "text": text}]
    if image: content.append({"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(image).decode()}})
    body = {"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": content}], "temperature": temperature, "max_tokens": max_tokens}
    if extra: body.update(extra)
    data = json.dumps(body).encode("utf-8"); headers = {"Content-Type": "application/json"}
    if api_key: headers["Authorization"] = "Bearer " + api_key
    url = base_url.rstrip("/") + "/chat/completions"; err = None
    for attempt in range(1, retries + 1):
        t0 = time.time()
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers, method="POST"), timeout=timeout) as r:
                out = json.loads(r.read().decode("utf-8"))
            msg = out["choices"][0]["message"]; txt = msg.get("content") or ""
            if isinstance(txt, list): txt = "".join(p.get("text", "") for p in txt if isinstance(p, dict))
            return txt, out.get("usage") or {}, time.time() - t0, attempt
        except (urllib.error.URLError, urllib.error.HTTPError, KeyError, IndexError, ValueError, TimeoutError, OSError) as e:
            err = e; time.sleep(min(30, 2 ** attempt))
    raise RuntimeError(f"no answer after {retries} attempts: {err}")
