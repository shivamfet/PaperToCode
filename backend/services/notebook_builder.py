import json

import nbformat


def build_notebook(tutorial_data: dict) -> nbformat.NotebookNode:
    """Build a research-grade Jupyter notebook from structured tutorial data.

    Args:
        tutorial_data: Dict with keys: title, authors, summary, math_foundations,
                       algorithms, visualizations, ablation_study, exercises, references.

    Returns:
        A valid nbformat v4 NotebookNode.
    """
    nb = nbformat.v4.new_notebook()
    nb.metadata.update({
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "name": "python",
            "version": "3.10.0",
        },
    })

    cells = []

    # --- Title cell ---
    authors_str = ", ".join(tutorial_data.get("authors", []))
    cells.append(nbformat.v4.new_markdown_cell(
        f"# {tutorial_data['title']}\n\n"
        f"**Authors:** {authors_str}\n\n"
        f"*Generated research notebook — implements key algorithms with synthetic data, "
        f"visualizations, and exercises.*"
    ))

    # --- Executive summary ---
    cells.append(nbformat.v4.new_markdown_cell(
        f"## Executive Summary\n\n{tutorial_data['summary']}"
    ))

    # --- Pip installs ---
    cells.append(nbformat.v4.new_code_cell(
        "# Install required packages\n"
        "!pip install -q torch numpy matplotlib plotly scipy scikit-learn"
    ))

    # --- Mathematical foundations ---
    if tutorial_data.get("math_foundations"):
        cells.append(nbformat.v4.new_markdown_cell("## Mathematical Foundations"))
        for mf in tutorial_data["math_foundations"]:
            cells.append(nbformat.v4.new_markdown_cell(
                f"### {mf['name']}\n\n"
                f"$$\n{mf['latex']}\n$$\n\n"
                f"{mf['explanation']}"
            ))

    # --- Algorithms ---
    if tutorial_data.get("algorithms"):
        cells.append(nbformat.v4.new_markdown_cell("## Algorithm Implementations"))
        for algo in tutorial_data["algorithms"]:
            # Pseudocode
            cells.append(nbformat.v4.new_markdown_cell(
                f"### {algo['name']}\n\n"
                f"**Pseudocode:**\n```\n{algo['pseudocode']}\n```"
            ))
            # Implementation
            cells.append(nbformat.v4.new_code_cell(algo["implementation"]))
            # Synthetic data
            if algo.get("synthetic_data"):
                cells.append(nbformat.v4.new_markdown_cell(
                    f"#### Synthetic Data for {algo['name']}"
                ))
                cells.append(nbformat.v4.new_code_cell(algo["synthetic_data"]))

    # --- Visualizations ---
    if tutorial_data.get("visualizations"):
        cells.append(nbformat.v4.new_markdown_cell("## Visualizations"))
        for viz in tutorial_data["visualizations"]:
            cells.append(nbformat.v4.new_markdown_cell(f"### {viz['title']}"))
            cells.append(nbformat.v4.new_code_cell(viz["code"]))

    # --- Ablation study ---
    if tutorial_data.get("ablation_study"):
        abl = tutorial_data["ablation_study"]
        cells.append(nbformat.v4.new_markdown_cell(
            f"## Ablation Study\n\n{abl['description']}"
        ))
        cells.append(nbformat.v4.new_code_cell(abl["code"]))

    # --- Exercises ---
    if tutorial_data.get("exercises"):
        cells.append(nbformat.v4.new_markdown_cell("## Exercises"))
        for i, ex in enumerate(tutorial_data["exercises"], 1):
            cells.append(nbformat.v4.new_markdown_cell(
                f"### Exercise {i}\n\n"
                f"{ex['question']}\n\n"
                f"**Hint:** {ex['hint']}"
            ))

    # --- References ---
    if tutorial_data.get("references"):
        ref_lines = "\n".join(f"- {r}" for r in tutorial_data["references"])
        cells.append(nbformat.v4.new_markdown_cell(
            f"## References\n\n{ref_lines}"
        ))

    nb.cells = cells
    return nb


def notebook_to_bytes(nb: nbformat.NotebookNode) -> bytes:
    """Serialize a notebook to UTF-8 JSON bytes.

    Args:
        nb: A valid nbformat NotebookNode.

    Returns:
        UTF-8 encoded bytes of the notebook JSON.
    """
    return nbformat.writes(nb).encode("utf-8")
