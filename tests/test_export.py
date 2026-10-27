import csv
import io
from counsel.export import COLUMNS, rows, to_csv
from counsel.seed import SEED


def test_csv_has_header_and_one_row_per_dispute():
    parsed = list(csv.DictReader(io.StringIO(to_csv(SEED))))
    assert list(parsed[0].keys()) == COLUMNS
    assert len(parsed) == len(SEED)
    assert all(r["submitted"] == "False" for r in parsed)


def test_rows_sorted_by_due_date():
    due = [r["due_date"] for r in rows(SEED)]
    assert due == sorted(due)
