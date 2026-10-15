import importlib.util
from pathlib import Path

script=Path(__file__).resolve().parents[1]/"scripts"/"probe_uljin_ecobank_download_js_v0.py"
spec=importlib.util.spec_from_file_location("uljin_download_js_probe",script)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_public_js_function_summary_redacts_arguments():
    js="""function fn_atchFileDwldOpinionModal(attachment_id, secret) {
      var url='/rdm/file/fileDownload.do?id=secret234';
      $.ajax({url:url, method:'POST'});
      fn_checkLogin('private-secret');
    }"""
    x=m.summarize_function(js)
    assert x["function_definition_found"]
    assert x["uses_ajax_keyword"]
    assert "secret234" not in str(x)
    assert "private-secret" not in str(x)
    assert "attachment_id" not in str(x)


def test_only_original_host_script_paths_and_never_query_tokens():
    x=m.analyze_html("""<html>
      <script src="/js/public.js?token=secret123"></script>
      <script src="https://evil.example/js/bad.js"></script>
      <script>function fn_atchFileDwldOpinionModal(x) { $('#modal').modal(); }</script>
      </html>""")
    assert x["provider_js_paths_only"] == ["/js/public.js"]
    assert not x["forms_submitted"]
    assert not x["zip_bytes_downloaded"]
    assert "secret123" not in str(x)
