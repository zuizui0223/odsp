from scripts.build_n2_mee_manuscript_v4 import build_manuscript_text


def test_verified_milotic_reference_is_rendered_in_submission_manuscript():
    text = build_manuscript_text()
    assert "Dataset description associated with the MH_ANTWERPEN bird-tracking project" not in text
    assert "Milotić, T., Desmet, P., Anselin, A." in text
    assert "GPS tracking data of Western marsh harriers breeding in Belgium and the Netherlands" in text
    assert "*ZooKeys*, 947, 143–155" in text
    assert "https://doi.org/10.3897/zookeys.947.52570" in text
