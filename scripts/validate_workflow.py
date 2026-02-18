"""Quick validation: submit workflow to ComfyUI and immediately cancel."""
import json, random, urllib.request, sys

workflow = json.load(open("comfyui_workflows/video_ltx2_t2v_distilled_api.json"))

# Inject test prompt
for nid, node in workflow.items():
    if node.get("class_type") == "PrimitiveStringMultiline":
        node["inputs"]["value"] = "a cat walking on a sunny street"
        break

# Lower frame count
for nid, node in workflow.items():
    if node.get("class_type") == "PrimitiveInt" and node.get("_meta", {}).get("title") == "Frame Count":
        node["inputs"]["value"] = 97
        break

# Randomize seeds
for nid, node in workflow.items():
    if node.get("class_type") == "RandomNoise":
        node["inputs"]["noise_seed"] = random.randint(0, 2**32 - 1)

payload = json.dumps({"prompt": workflow, "client_id": "validate-test-2"}).encode()
req = urllib.request.Request("http://localhost:8188/prompt", data=payload, headers={"Content-Type": "application/json"})
try:
    resp = urllib.request.urlopen(req, timeout=10)
    result = json.loads(resp.read())
    print("SUCCESS - prompt_id:", result.get("prompt_id"))
    print("node_errors:", result.get("node_errors"))

    # Cancel immediately
    cancel = urllib.request.Request("http://localhost:8188/queue", data=json.dumps({"clear": True}).encode(), headers={"Content-Type": "application/json"})
    urllib.request.urlopen(cancel, timeout=5)
    print("Queue cleared.")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"FAILED ({e.code}): {body}")
    sys.exit(1)
