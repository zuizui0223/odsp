import scripts.n2_bat_mets_inventory as mod


def test_dspace_inventory_never_fetches_content(monkeypatch):
    calls = []

    def fake_fetch_json(url):
        calls.append(url)
        if "pid/find" in url:
            payload = {"_links": {"bundles": {"href": "https://repo/bundles"}}}
        elif url == "https://repo/bundles":
            payload = {
                "_embedded": {
                    "bundles": [
                        {
                            "uuid": "bundle-1",
                            "name": "ORIGINAL",
                            "_links": {
                                "bitstreams": {"href": "https://repo/bitstreams"}
                            },
                        }
                    ]
                }
            }
        elif url == "https://repo/bitstreams":
            payload = {
                "_embedded": {
                    "bitstreams": [
                        {
                            "uuid": "bs-1",
                            "name": "events.csv",
                            "description": "tracking data",
                            "sizeBytes": 123,
                            "checkSum": {
                                "checkSumAlgorithm": "MD5",
                                "value": "abc",
                            },
                            "_links": {
                                "self": {"href": "https://repo/bitstreams/bs-1"},
                                "content": {"href": "https://repo/bitstreams/bs-1/content"},
                            },
                        }
                    ]
                }
            }
        else:
            raise AssertionError(f"unexpected URL: {url}")
        raw = str(payload).encode()
        return payload, raw, url

    monkeypatch.setattr(mod, "fetch_json", fake_fetch_json)
    report = mod.inventory_from_dspace()

    assert calls == [mod.PID_URL, "https://repo/bundles", "https://repo/bitstreams"]
    assert "https://repo/bitstreams/bs-1/content" not in calls
    assert report["bitstreams_downloaded"] is False
    assert report["tracking_values_downloaded"] is False
    assert report["outcome_metrics_computed"] is False
    assert report["scientific_terminal_decision"] is False
    assert report["files"][0]["filename"] == "events.csv"
    assert report["files"][0]["content_url"].endswith("/content")
    assert report["files"][0]["bitstream_content_fetched"] is False
