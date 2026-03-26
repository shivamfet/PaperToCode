import json

import nbformat
import pytest

from services.notebook_builder import build_notebook, notebook_to_bytes


# Minimal valid tutorial data matching the schema from openai_service
SAMPLE_TUTORIAL = {
    "title": "Attention Is All You Need",
    "authors": ["Vaswani et al."],
    "summary": "This paper introduces the Transformer architecture, replacing recurrence with self-attention.",
    "math_foundations": [
        {
            "name": "Scaled Dot-Product Attention",
            "latex": r"Attention(Q,K,V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V",
            "explanation": "Computes attention weights via scaled dot products.",
        },
        {
            "name": "Multi-Head Attention",
            "latex": r"MultiHead(Q,K,V) = Concat(head_1, \dots, head_h)W^O",
            "explanation": "Runs multiple attention heads in parallel.",
        },
    ],
    "algorithms": [
        {
            "name": "Scaled Dot-Product Attention",
            "pseudocode": "1. Compute QK^T\n2. Scale by sqrt(d_k)\n3. Apply softmax\n4. Multiply by V",
            "implementation": "import torch\nimport torch.nn.functional as F\n\ndef scaled_dot_product_attention(Q, K, V):\n    d_k = Q.size(-1)\n    scores = torch.matmul(Q, K.transpose(-2, -1)) / d_k**0.5\n    weights = F.softmax(scores, dim=-1)\n    return torch.matmul(weights, V)",
            "synthetic_data": "Q = torch.randn(2, 8, 10, 64)\nK = torch.randn(2, 8, 10, 64)\nV = torch.randn(2, 8, 10, 64)",
        }
    ],
    "visualizations": [
        {
            "title": "Attention Heatmap",
            "code": "import matplotlib.pyplot as plt\nimport numpy as np\nattn = np.random.rand(10, 10)\nplt.imshow(attn, cmap='viridis')\nplt.colorbar()\nplt.title('Attention Weights')\nplt.show()",
        }
    ],
    "ablation_study": {
        "description": "Vary number of attention heads from 1 to 16",
        "code": "heads = [1, 2, 4, 8, 16]\nresults = [train_model(num_heads=h) for h in heads]\nplt.plot(heads, results)",
    },
    "exercises": [
        {
            "question": "Implement positional encoding from scratch.",
            "hint": "Use sine and cosine functions of different frequencies.",
        },
        {
            "question": "What happens if you remove the scaling factor?",
            "hint": "Think about the magnitude of dot products in high dimensions.",
        },
    ],
    "references": [
        "Vaswani et al., 'Attention Is All You Need', NeurIPS 2017",
        "Ba et al., 'Layer Normalization', 2016",
    ],
}


class TestBuildNotebook:
    """Tests for build_notebook()."""

    def test_returns_notebook_node(self):
        nb = build_notebook(SAMPLE_TUTORIAL)
        assert isinstance(nb, nbformat.NotebookNode)

    def test_notebook_is_valid(self):
        """Notebook passes nbformat validation."""
        nb = build_notebook(SAMPLE_TUTORIAL)
        nbformat.validate(nb)  # raises on invalid

    def test_notebook_version_4(self):
        nb = build_notebook(SAMPLE_TUTORIAL)
        assert nb.nbformat == 4

    def test_has_title_cell(self):
        nb = build_notebook(SAMPLE_TUTORIAL)
        first_cell = nb.cells[0]
        assert first_cell.cell_type == "markdown"
        assert "Attention Is All You Need" in first_cell.source

    def test_has_authors_in_title_cell(self):
        nb = build_notebook(SAMPLE_TUTORIAL)
        first_cell = nb.cells[0]
        assert "Vaswani et al." in first_cell.source

    def test_has_summary_cell(self):
        nb = build_notebook(SAMPLE_TUTORIAL)
        sources = [c.source for c in nb.cells if c.cell_type == "markdown"]
        assert any("Transformer architecture" in s for s in sources)

    def test_has_pip_install_cell(self):
        nb = build_notebook(SAMPLE_TUTORIAL)
        code_cells = [c for c in nb.cells if c.cell_type == "code"]
        assert any("pip install" in c.source for c in code_cells)

    def test_has_math_cells(self):
        """Each math foundation should appear as a markdown cell with LaTeX."""
        nb = build_notebook(SAMPLE_TUTORIAL)
        sources = "\n".join(c.source for c in nb.cells if c.cell_type == "markdown")
        assert "Scaled Dot-Product Attention" in sources
        assert r"\text{softmax}" in sources

    def test_has_algorithm_sections(self):
        """Each algorithm should have pseudocode (markdown) and implementation (code)."""
        nb = build_notebook(SAMPLE_TUTORIAL)
        md_sources = "\n".join(c.source for c in nb.cells if c.cell_type == "markdown")
        code_sources = "\n".join(c.source for c in nb.cells if c.cell_type == "code")
        assert "Scaled Dot-Product Attention" in md_sources
        assert "scaled_dot_product_attention" in code_sources

    def test_has_synthetic_data_cell(self):
        nb = build_notebook(SAMPLE_TUTORIAL)
        code_sources = "\n".join(c.source for c in nb.cells if c.cell_type == "code")
        assert "torch.randn" in code_sources

    def test_has_visualization_cells(self):
        nb = build_notebook(SAMPLE_TUTORIAL)
        code_sources = "\n".join(c.source for c in nb.cells if c.cell_type == "code")
        assert "plt.imshow" in code_sources

    def test_has_ablation_study(self):
        nb = build_notebook(SAMPLE_TUTORIAL)
        all_sources = "\n".join(c.source for c in nb.cells)
        assert "Ablation" in all_sources or "ablation" in all_sources
        code_sources = "\n".join(c.source for c in nb.cells if c.cell_type == "code")
        assert "train_model" in code_sources

    def test_has_exercises(self):
        nb = build_notebook(SAMPLE_TUTORIAL)
        md_sources = "\n".join(c.source for c in nb.cells if c.cell_type == "markdown")
        assert "positional encoding" in md_sources.lower()
        assert "Hint" in md_sources or "hint" in md_sources.lower()

    def test_has_references(self):
        nb = build_notebook(SAMPLE_TUTORIAL)
        md_sources = "\n".join(c.source for c in nb.cells if c.cell_type == "markdown")
        assert "NeurIPS 2017" in md_sources

    def test_cell_count_reasonable(self):
        """Notebook should have a reasonable number of cells."""
        nb = build_notebook(SAMPLE_TUTORIAL)
        assert len(nb.cells) >= 10

    def test_has_both_cell_types(self):
        nb = build_notebook(SAMPLE_TUTORIAL)
        types = {c.cell_type for c in nb.cells}
        assert "markdown" in types
        assert "code" in types


class TestNotebookToBytes:
    """Tests for notebook_to_bytes()."""

    def test_returns_bytes(self):
        nb = build_notebook(SAMPLE_TUTORIAL)
        result = notebook_to_bytes(nb)
        assert isinstance(result, bytes)

    def test_bytes_are_valid_json(self):
        nb = build_notebook(SAMPLE_TUTORIAL)
        result = notebook_to_bytes(nb)
        data = json.loads(result.decode("utf-8"))
        assert "cells" in data
        assert "nbformat" in data

    def test_bytes_are_utf8(self):
        nb = build_notebook(SAMPLE_TUTORIAL)
        result = notebook_to_bytes(nb)
        text = result.decode("utf-8")
        assert len(text) > 0

    def test_roundtrip_valid_notebook(self):
        """Bytes can be read back as a valid notebook."""
        nb = build_notebook(SAMPLE_TUTORIAL)
        raw = notebook_to_bytes(nb)
        restored = nbformat.reads(raw.decode("utf-8"), as_version=4)
        nbformat.validate(restored)
        assert restored.cells[0].source == nb.cells[0].source
