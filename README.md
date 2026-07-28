## Setup (only needed once per computer)

Requires Python 3.9+.

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

## How to run

### Run main.py. First run requires Internet. Subsequent runs will not require Internet.
```bash
python3 main.py [desired product] [center wavelength] [span (optional)]
```
