# Backend

See the [project README](../README.md) for full setup, run, migration,
seed, and test commands (§12–17), plus architecture and environment
variable documentation.

Quick reference, run from this directory:

```bash
pip install -r requirements.txt
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
pytest
```
