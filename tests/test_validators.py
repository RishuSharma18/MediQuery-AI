import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.validators import validate_sql, enforce_row_limit

assert validate_sql("SELECT * FROM patients WHERE age > 60").is_valid is True
assert validate_sql("DELETE FROM patients WHERE id = 1").is_valid is False
assert validate_sql("DROP TABLE patients").is_valid is False
assert validate_sql("SELECT * FROM patients; DROP TABLE patients;").is_valid is False
assert validate_sql("SELECT * FROM patients -- ; DROP TABLE patients").is_valid is False
assert "LIMIT" in enforce_row_limit("SELECT * FROM patients").upper()

print("All validator checks passed ✅")