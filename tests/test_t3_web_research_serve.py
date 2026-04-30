from importlib import util
from pathlib import Path


def load_serve_module():
    serve_path = (
        Path(__file__).resolve().parents[1]
        / "tasks-public"
        / "assets"
        / "t3_web_research_and_cite"
        / "serve.py"
    )
    spec = util.spec_from_file_location("t3_web_research_serve", serve_path)
    module = util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_article_paths_resolve_only_known_article_slugs():
    serve = load_serve_module()

    assert serve.article_for_request_path("/article/01_grid_basics").name == "01_grid_basics.html"
    assert serve.article_for_request_path("/article/../../serve.py") is None
    assert serve.article_for_request_path("/article/%2e%2e/%2e%2e/serve.py") is None
