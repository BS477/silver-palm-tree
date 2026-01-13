import time
import requests

def test_end_to_end_flow():
    service_b_url = "http://localhost:8001/count"
    service_a_results = "http://localhost:8000/results"

    resp = requests.post(service_b_url, json={"image_url": "https://cdn.wikibound.info/1/16/EB_banner1.jpg"})
    assert resp.status_code == 202

    # wait for consumer processing
    time.sleep(5)

    r = requests.get(service_a_results)
    assert r.status_code == 200
    arr = r.json()
    assert any(item["image_url"] == "https://cdn.wikibound.info/1/16/EB_banner1.jpg" for item in arr)