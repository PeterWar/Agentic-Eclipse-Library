"""Consulta de visió a OpenRouter (imatges com a data URL) amb el client de la skill (clau al Clauer, mai a la sortida).
Ús: or_vision.py MODEL prompt.txt esforc(no|low|medium|high|xhigh) img1.jpg [img2.jpg ...]"""
import sys, base64, json, os
sys.path.insert(0, os.path.expanduser('~/.claude/skills/openrouter/scripts'))
from openrouter_cli import load_api_key, api_request, response_text, usage_summary
model, ptxt, esforc, *imgs = sys.argv[1:]
prompt = open(ptxt, encoding='utf-8').read()
content = [{"type": "text", "text": prompt}]
for p in imgs:
    b64 = base64.b64encode(open(p, 'rb').read()).decode()
    content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
payload = {"model": model, "messages": [{"role": "user", "content": content}], "max_tokens": int(os.environ.get("OR_MAXTOK","8000")),
           "provider": {"data_collection": "deny"}}
if esforc != 'no':
    payload["reasoning"] = {"effort": esforc}
key = load_api_key()
r = api_request("POST", "/chat/completions", api_key=key, payload=payload, timeout=600)
print(response_text(r))
print("\n[usage]", json.dumps(usage_summary(r), ensure_ascii=False))
