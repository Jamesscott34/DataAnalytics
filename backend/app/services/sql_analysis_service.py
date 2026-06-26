"""SQL analysis service.

Imports uploaded CSV files into queryable SQLite tables and runs validated
read-only SQL against the imported rows.
"""

import csv
import re
from collections import Counter
from collections.abc import Sequence
from io import StringIO
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.csv_data import CsvData
from app.models.uploaded_file import UploadedFile
from app.schemas.sql import (
    SQLGroupImportResponse,
    SQLImportResponse,
    SQLPreset,
    SQLQueryResponse,
)
from app.utils.encoding_utils import decode_csv_bytes

FORBIDDEN_SQL = re.compile(
    r"\b("
    r"INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|ATTACH|DETACH|"
    r"TRUNCATE|VACUUM|GRANT|REVOKE"
    r")\b",
    re.IGNORECASE,
)
IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


class SQLAnalysisError(ValueError):
    """Raised when SQL import or query execution fails."""


class SQLAnalysisService:
    """Service for importing CSV rows and running read-only SQL."""

    def import_rows(
        self,
        db: Session,
        *,
        file_id: int,
        max_rows: int | None = None,
    ) -> SQLImportResponse:
        """Import CSV rows into csv_data and a SQLite query table."""
        file = self._get_file(db, file_id)
        content = self._read_file_bytes(file)
        decoded = decode_csv_bytes(content)
        reader = csv.DictReader(StringIO(decoded, newline=""))
        if reader.fieldnames is None:
            raise SQLAnalysisError("CSV must contain a header row")

        columns = self._normalize_columns(list(reader.fieldnames))
        rows = list(reader)
        if max_rows is not None:
            rows = rows[:max_rows]

        table_name = self._table_name(file_id)
        self._clear_import(db, file_id=file_id, table_name=table_name)
        self._create_import_table(db, table_name=table_name, columns=columns)

        for index, row in enumerate(rows):
            normalized_row = {
                columns[col_index]: (row.get(original) or "").strip()
                for col_index, original in enumerate(reader.fieldnames)
            }
            db.add(
                CsvData(
                    file_id=file_id,
                    row_index=index,
                    data=normalized_row,
                ),
            )
            self._insert_row(
                db,
                table_name=table_name,
                columns=columns,
                row=normalized_row,
            )

        db.commit()
        return SQLImportResponse(
            imported_rows=len(rows),
            table_name=table_name,
            columns=columns,
        )

    def table_name_for_file(self, file_id: int) -> str:
        """Return the SQLite table name for an uploaded file."""
        return self._table_name(file_id)

    def alias_from_filename(self, filename: str) -> str:
        """Derive a SQL-friendly alias from an uploaded filename."""
        stem = Path(filename).stem
        cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", stem) or "dataset"
        if cleaned[0].isdigit():
            cleaned = f"t_{cleaned}"
        return cleaned

    def get_import_schema(
        self,
        db: Session,
        *,
        file_id: int,
    ) -> tuple[list[str], int] | None:
        """Return columns and row count when a file has been imported."""
        first_row = (
            db.query(CsvData)
            .filter(CsvData.file_id == file_id)
            .order_by(CsvData.row_index.asc())
            .first()
        )
        if first_row is None:
            return None
        count = db.query(CsvData.id).filter(CsvData.file_id == file_id).count()
        return list(first_row.data.keys()), count

    def import_group(
        self,
        db: Session,
        *,
        group_id: int,
        members: list[Any],
        group_name: str,
    ) -> SQLGroupImportResponse:
        """Import every file in a dataset group (headers returned, not row data)."""
        from app.schemas.sql import SQLGroupTableSchema

        tables: list[SQLGroupTableSchema] = []
        for member in members:
            imported = self.import_rows(db, file_id=member.file_id)
            tables.append(
                SQLGroupTableSchema(
                    file_id=member.file_id,
                    table_alias=member.table_alias,
                    original_filename=member.file.original_filename,
                    table_name=imported.table_name,
                    columns=imported.columns,
                    imported_rows=imported.imported_rows,
                ),
            )
        return SQLGroupImportResponse(
            group_id=group_id,
            group_name=group_name,
            tables=tables,
        )

    def run_group_query(
        self,
        db: Session,
        *,
        table_names: list[str],
        query: str,
        params: dict[str, Any] | None = None,
    ) -> SQLQueryResponse:
        """Execute read-only SQL against one or more imported group tables."""
        self._validate_read_only_query(query, table_names=table_names)
        return self._execute_query(db, query=query, params=params)

    def list_group_presets(
        self,
        *,
        tables: list[tuple[str, str, list[str]]],
    ) -> list[SQLPreset]:
        """Build presets for a multi-table group (alias, table_name, columns)."""
        presets: list[SQLPreset] = []
        for alias, table_name, columns in tables:
            presets.append(
                SQLPreset(
                    id=f"all_{alias}",
                    name=f"{alias}: all rows",
                    description=f"Select every row from {alias}.",
                    sql=f'SELECT * FROM "{table_name}"',
                ),
            )
            presets.append(
                SQLPreset(
                    id=f"count_{alias}",
                    name=f"{alias}: row count",
                    description=f"Count rows in {alias}.",
                    sql=f'SELECT COUNT(*) AS row_count FROM "{table_name}"',
                ),
            )
            for column in columns[:3]:
                presets.append(
                    SQLPreset(
                        id=f"{alias}_{column}",
                        name=f'{alias}: "{column}"',
                        description=f"Select {column} from {alias}.",
                        sql=f'SELECT "{column}" FROM "{table_name}"',
                    ),
                )
        if len(tables) >= 2:
            left_alias, left_table, left_cols = tables[0]
            right_alias, right_table, _ = tables[1]
            join_col = next(
                (
                    column
                    for column in left_cols
                    if any(
                        column.lower() == other.lower()
                        for _, _, other_cols in tables[1:]
                        for other in other_cols
                    )
                ),
                None,
            )
            if join_col:
                presets.append(
                    SQLPreset(
                        id="join_shared_column",
                        name=f"JOIN {left_alias} + {right_alias}",
                        description=(f"Inner join on shared column {join_col}."),
                        sql=(
                            f'SELECT * FROM "{left_table}" AS {left_alias} '
                            f'INNER JOIN "{right_table}" AS {right_alias} '
                            f'ON {left_alias}."{join_col}" = {right_alias}."{join_col}"'
                        ),
                    ),
                )
        return presets

    def run_query(
        self,
        db: Session,
        *,
        file_id: int,
        query: str,
        params: dict[str, Any] | None = None,
    ) -> SQLQueryResponse:
        """Execute a validated read-only SQL query."""
        table_name = self._table_name(file_id)
        self._ensure_imported(db, file_id=file_id)
        self._validate_read_only_query(
            query,
            table_names=[table_name],
        )
        return self._execute_query(db, query=query, params=params)

    def list_presets(self, db: Session, *, file_id: int) -> list[SQLPreset]:
        """Return SQL presets tailored to an imported file."""
        table_name = self._table_name(file_id)
        self._ensure_imported(db, file_id=file_id)
        columns = self._import_columns(db, file_id=file_id)
        group_column = self._pick_group_column(db, file_id=file_id, columns=columns)

        presets = [
            SQLPreset(
                id="view_all_rows",
                name="View all rows",
                description="Show every imported row in the dataset table.",
                sql=f'SELECT * FROM "{table_name}"',
            ),
            SQLPreset(
                id="row_count",
                name="Total rows",
                description="Count imported rows in the dataset table.",
                sql=f'SELECT COUNT(*) AS row_count FROM "{table_name}"',
            ),
        ]
        if group_column is not None:
            presets.append(
                SQLPreset(
                    id="group_by_count",
                    name=f"Count by {group_column}",
                    description="Group imported rows and count occurrences.",
                    sql=(
                        f'SELECT "{group_column}" AS {group_column}, '
                        f"COUNT(*) AS row_count "
                        f'FROM "{table_name}" '
                        f'GROUP BY "{group_column}" '
                        f"ORDER BY row_count DESC"
                    ),
                ),
            )
            presets.append(
                SQLPreset(
                    id="top_values",
                    name=f"Top values in {group_column}",
                    description="Return the five most frequent values.",
                    sql=(
                        f'SELECT "{group_column}" AS {group_column}, '
                        f"COUNT(*) AS row_count "
                        f'FROM "{table_name}" '
                        f'GROUP BY "{group_column}" '
                        f"ORDER BY row_count DESC "
                        f"LIMIT 5"
                    ),
                ),
            )
        return presets

    def run_preset(
        self,
        db: Session,
        *,
        file_id: int,
        preset_id: str,
    ) -> SQLQueryResponse:
        """Run a built-in preset query for an imported file."""
        presets = {
            preset.id: preset for preset in self.list_presets(db, file_id=file_id)
        }
        preset = presets.get(preset_id)
        if preset is None:
            raise SQLAnalysisError(f"Unknown preset: {preset_id}")
        return self.run_query(db, file_id=file_id, query=preset.sql)

    def _get_file(self, db: Session, file_id: int) -> UploadedFile:
        file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if file is None:
            raise SQLAnalysisError("File not found")
        return file

    def _read_file_bytes(self, file: UploadedFile) -> bytes:
        upload_dir = Path(get_settings().upload_dir)
        path = upload_dir / file.stored_path
        if not path.exists():
            raise SQLAnalysisError("Stored file not found")
        return path.read_bytes()

    def _table_name(self, file_id: int) -> str:
        return f"csv_import_{file_id}"

    def _normalize_columns(self, headers: Sequence[str]) -> list[str]:
        seen: Counter[str] = Counter()
        normalized: list[str] = []
        for header in headers:
            base = self._sanitize_identifier(header)
            seen[base] += 1
            name = base if seen[base] == 1 else f"{base}_{seen[base]}"
            normalized.append(name)
        return normalized

    def _sanitize_identifier(self, value: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", value.strip()) or "column"
        if cleaned[0].isdigit():
            cleaned = f"col_{cleaned}"
        if not IDENTIFIER_PATTERN.match(cleaned):
            raise SQLAnalysisError(f"Invalid column name: {value}")
        return cleaned

    def _clear_import(self, db: Session, *, file_id: int, table_name: str) -> None:
        db.query(CsvData).filter(CsvData.file_id == file_id).delete()
        db.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))

    def _create_import_table(
        self,
        db: Session,
        *,
        table_name: str,
        columns: list[str],
    ) -> None:
        column_defs = ", ".join(f'"{column}" TEXT' for column in columns)
        db.execute(text(f'CREATE TABLE "{table_name}" ({column_defs})'))

    def _insert_row(
        self,
        db: Session,
        *,
        table_name: str,
        columns: list[str],
        row: dict[str, str],
    ) -> None:
        bindings = {f"p{index}": row[column] for index, column in enumerate(columns)}
        placeholders = ", ".join(f":p{index}" for index in range(len(columns)))
        quoted_columns = ", ".join(f'"{column}"' for column in columns)
        statement = text(
            f'INSERT INTO "{table_name}" ({quoted_columns}) VALUES ({placeholders})',
        )
        db.execute(statement, bindings)

    def _ensure_imported(self, db: Session, *, file_id: int) -> None:
        exists = (
            db.query(CsvData.id).filter(CsvData.file_id == file_id).first() is not None
        )
        if not exists:
            raise SQLAnalysisError("CSV rows have not been imported for this file")

    def _import_columns(self, db: Session, *, file_id: int) -> list[str]:
        first_row = (
            db.query(CsvData)
            .filter(CsvData.file_id == file_id)
            .order_by(CsvData.row_index.asc())
            .first()
        )
        if first_row is None:
            raise SQLAnalysisError("CSV rows have not been imported for this file")
        return list(first_row.data.keys())

    def _pick_group_column(
        self,
        db: Session,
        *,
        file_id: int,
        columns: list[str],
    ) -> str | None:
        if not columns:
            return None
        counts: dict[str, int] = {column: 0 for column in columns}
        rows = (
            db.query(CsvData)
            .filter(CsvData.file_id == file_id)
            .order_by(CsvData.row_index.asc())
            .limit(200)
            .all()
        )
        for row in rows:
            for column in columns:
                if row.data.get(column):
                    counts[column] += 1
        ranked = sorted(
            columns,
            key=lambda column: (counts[column], column),
            reverse=True,
        )
        return ranked[0] if counts[ranked[0]] > 0 else columns[0]

    def _validate_read_only_query(
        self,
        query: str,
        *,
        table_names: list[str],
    ) -> None:
        normalized = query.strip().rstrip(";")
        if not normalized:
            raise SQLAnalysisError("Query must not be empty")
        if ";" in normalized:
            raise SQLAnalysisError("Multiple SQL statements are not allowed")

        leading = normalized.lstrip("(").strip().upper()
        if leading.startswith("PRAGMA"):
            if not any(name in normalized for name in table_names):
                raise SQLAnalysisError(
                    "PRAGMA must reference one of the group tables",
                )
            return

        if FORBIDDEN_SQL.search(normalized):
            raise SQLAnalysisError("Destructive SQL statements are not allowed")

        if not (
            leading.startswith("SELECT")
            or leading.startswith("WITH")
            or leading.startswith("EXPLAIN")
        ):
            raise SQLAnalysisError(
                "Only read-only queries are allowed (SELECT, WITH, EXPLAIN, PRAGMA)",
            )
        lowered = normalized.lower()
        if not any(name.lower() in lowered for name in table_names):
            names = ", ".join(table_names)
            raise SQLAnalysisError(f"Query must reference at least one table: {names}")

    def _execute_query(
        self,
        db: Session,
        *,
        query: str,
        params: dict[str, Any] | None,
    ) -> SQLQueryResponse:
        try:
            result = db.execute(text(query), params or {})
            rows = result.fetchall()
            columns = list(result.keys())
        except Exception as exc:
            raise SQLAnalysisError(f"SQL execution failed: {exc}") from exc

        serialized = [list(row) for row in rows]
        return SQLQueryResponse(
            columns=columns,
            rows=serialized,
            row_count=len(serialized),
        )


sql_analysis_service = SQLAnalysisService()
