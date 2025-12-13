# Scripts

This folder contains utility scripts for the xCIT website.

## scholar_to_qmd.py

Fetches publications from Google Scholar profiles and generates the `publications.qmd` file.

### Setup

1. Create a virtual environment:
   ```bash
   cd scripts
   uv venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   uv pip install -r pyproject.toml
   # or
   uv sync
   ```

### Usage

Run the script to regenerate the publications page:

```bash
source .venv/bin/activate
python scholar_to_qmd.py
```

The script will:
1. Fetch publications from the configured Google Scholar profiles
2. Remove duplicates
3. Filter to publications from 2019 onwards
4. Generate the `publications.qmd` file in the root directory

### Configuration

Edit the `profiles` list in `scholar_to_qmd.py` to add or remove Google Scholar profile IDs:

```python
profiles = [
    "pIK4eZ0AAAAJ",  # Pedro Cardoso-Leite
    "GVsyMf8AAAAJ",  # Morteza Ansarinia
    "IkRvFZkAAAAJ"   # Hoorieh Afkari
]
```

### Notes

- Google Scholar may rate-limit requests. If some profiles fail to fetch, try running the script again later.
- The script generates publications in APA-style format.
