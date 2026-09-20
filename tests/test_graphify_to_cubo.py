from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "graphify_to_cubo.py"
spec = spec_from_file_location("graphify_to_cubo", SCRIPT)
module = module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def test_convert_preserves_graphify_evidence_and_provenance():
    payload = {
        "nodes": [
            {"id": "a", "label": "Alpha", "file_type": "code", "source_file": "a.py"},
            {"id": "b", "label": "Beta", "file_type": "document", "source_file": "b.md"},
        ],
        "edges": [
            {
                "source": "a",
                "target": "b",
                "relation": "references",
                "confidence": "INFERRED",
                "confidence_score": 0.75,
                "source_file": "a.py",
            }
        ],
    }

    out = module.convert(payload, max_nodes=10)

    assert out["meta"]["nodes"] == 2
    assert out["meta"]["links"] == 1
    link = out["links"][0]
    assert link["confidence"] == "INFERRED"
    assert link["confidenceScore"] == 0.75
    assert link["sourceSystem"] == "Graphify"
    assert link["sourceFile"] == "a.py"
    assert link["state"] == "OBSERVED"


def test_extracted_edges_are_normalized_to_full_confidence():
    payload = {
        "nodes": [{"id": "a"}, {"id": "b"}],
        "links": [
            {"source": "a", "target": "b", "relation": "calls", "confidence": "EXTRACTED"}
        ],
    }

    out = module.convert(payload, max_nodes=10)
    assert out["links"][0]["confidence"] == "EXTRACTED"
    assert out["links"][0]["confidenceScore"] == 1.0
