# Placement Analytics Dashboard  

## Screenshots

### Header
<img width="1360" height="262" alt="01-header" src="https://github.com/user-attachments/assets/b9a1ae83-9da8-487a-bf55-199c9884c5da" />

### Backlog - Internship
<img width="961" height="420" alt="03-backlogs-internships" src="https://github.com/user-attachments/assets/f8643124-8fff-4595-b3e8-7e9bd4fbc72a" />

### Skills
<img width="985" height="494" alt="04-skills" src="https://github.com/user-attachments/assets/7f03feb5-75cb-4435-bed4-237812031086" />

### Model - Metrics
<img width="958" height="356" alt="05-model-metrics" src="https://github.com/user-attachments/assets/f1859f86-eaf3-41f0-b904-575c6502cf92" />

### Model - Weight
<img width="1001" height="574" alt="06-model-weights" src="https://github.com/user-attachments/assets/44025e22-588f-4276-8c8f-e33faec50c5b" />

Explores which factors (CGPA, backlogs, skills, internships ...) relate to campus
shortlisting, with an interactive Streamlit dashboard and a logistic-regression
model that estimates a shortlisting probability.

The bundled data is **synthetic**. Say so wherever you show results.

## Layout

| File | Responsibility |
|---|---|
| `dataset.py` | Load (CSV or database), validate, build skill features |
| `analysis.py` | Aggregations behind the charts (no UI code) |
| `model.py` | Train, evaluate, predict |
| `app.py` | Streamlit UI only |
| `generate_data.py` | Synthetic data generator |
| `schema.sql`, `load_to_mysql.py` | Optional MySQL setup and loader |
| `tests/` | Unit tests |

## Run

```bash
pip install -r requirements.txt
python generate_data.py          # writes data/students.csv
streamlit run app.py
python -m unittest               # tests (pytest also works)
```

The model is retrained when the app starts (about 50 ms on 500 rows), so there is
no `model.pkl` to go stale or to load from an untrusted source.

## Optional: MySQL

```bash
pip install -r requirements-mysql.txt
mysql -u root -p < schema.sql
```

Create two accounts, choosing your own passwords (never commit them):

```sql
CREATE USER 'placement_loader'@'localhost' IDENTIFIED BY '<password>';
GRANT INSERT, DELETE ON placement_db.students TO 'placement_loader'@'localhost';
CREATE USER 'placement_ro'@'localhost' IDENTIFIED BY '<password>';
GRANT SELECT ON placement_db.students TO 'placement_ro'@'localhost';
```

```bash
# load (loader account)
export PLACEMENT_DB_URL='mysql+pymysql://placement_loader:<password>@localhost:3306/placement_db'
python load_to_mysql.py            # add --replace to delete existing rows first

# serve (read-only account)
export PLACEMENT_DB_URL='mysql+pymysql://placement_ro:<password>@localhost:3306/placement_db'
streamlit run app.py
```

Windows PowerShell: `$env:PLACEMENT_DB_URL = '...'`. If `PLACEMENT_DB_URL` is unset,
the app reads `data/students.csv`. Passwords containing `@`, `:` or `/` must be
URL-encoded.
