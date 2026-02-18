"""Debug: submit workflow and log all websocket messages."""
import json, random, asyncio, aiohttp

async def main():
    workflow = json.load(open("comfyui_workflows/video_ltx2_t2v_distilled_api.json"))

    # Inject simple prompt
    for nid, node in workflow.items():
        if node.get("class_type") == "PrimitiveStringMultiline":
            node["inputs"]["value"] = "a cat walking on a sunny street"
            break

    # Lower frame count to minimum valid (8+1=9)
    for nid, node in workflow.items():
        if node.get("class_type") == "PrimitiveInt" and node.get("_meta", {}).get("title") == "Frame Count":
            node["inputs"]["value"] = 9
            break

    for nid, node in workflow.items():
        if node.get("class_type") == "RandomNoise":
            node["inputs"]["noise_seed"] = random.randint(0, 2**32 - 1)

    client_id = "debug-ws-test"

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8188/prompt",
            json={"prompt": workflow, "client_id": client_id}
        ) as resp:
            result = await resp.json()
            prompt_id = result["prompt_id"]
            print(f"prompt_id: {prompt_id}")

        ws_url = f"ws://localhost:8188/ws?clientId={client_id}"
        async with session.ws_connect(ws_url) as ws:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    msg_type = data.get("type")
                    event_data = data.get("data")

                    if msg_type == "progress":
                        print(f"  progress: {event_data.get('value')}/{event_data.get('max')}")
                    elif msg_type == "executed":
                        node = event_data.get("node") if isinstance(event_data, dict) else "?"
                        output = (event_data.get("output") or {}) if isinstance(event_data, dict) else {}
                        output_keys = list(output.keys())
                        print(f"  executed: node={node} output_keys={output_keys}")
                        if isinstance(event_data, dict) and event_data.get("prompt_id") == prompt_id:
                            output = event_data.get("output") or {}
                            for key in ("videos", "gifs", "images"):
                                items = output.get(key)
                                if items:
                                    print(f"  >>> FOUND OUTPUT: {key} = {items}")
                                    return
                    elif msg_type in ("executing", "execution_start", "execution_cached", "execution_complete"):
                        print(f"  {msg_type}: data_type={type(event_data).__name__} data={str(event_data)[:200]}")
                    elif msg_type == "execution_error":
                        print(f"  ERROR: {event_data}")
                        return
                    else:
                        print(f"  {msg_type}: data_type={type(event_data).__name__} data={str(event_data)[:100]}")
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print(f"  WS ERROR: {msg.data}")
                    return

asyncio.run(main())
