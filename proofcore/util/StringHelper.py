"""
 Copyright (c) 2025-2026
 Karlsruhe Institute of Technology - Institute for Automation and Applied Informatics (IAI)
"""
import csv
import logging
from io import StringIO


class StringHelper:
    """
    Base helper for extracting values from single lines of delimited text (e.g. CSV/CSV-like content).

    Keeps track of the detected/configured separator and the first header row seen,
    so repeated calls on subsequent lines of the same stream reuse that state.
    """

    def __init__(self, separator: str = "", header_requested = True, logger=None):
        self.separator = separator
        self.header_requested = header_requested
        self._header = []
        self._logger = logger or logging.getLogger(__name__)

    def extract_value_from_line(self, line: str, column_name: str) -> str:
        """
        Extract the value for one configured column from one CSV line.

        Thin wrapper around extract_values_from_line() for the single-column case.
        """
        return self.extract_values_from_line(line, [column_name])[column_name]

    def extract_values_from_line(self, line: str, column_names: list[str]) -> dict:
        """
        Extract the values for multiple configured columns from one CSV line, in a single pass.

        Behaves like extract_value_from_line for each name, but resolves the header and the
        current data row only once, so it stays correct when several columns are needed from
        the same line (repeated calls to extract_value_from_line would re-read the header row
        as data once the header is already known).
        """
        rows = line.splitlines()
        self._logger.debug(f"Rows:\n{rows}")
        if len(rows) == 0:
            self._logger.warning(f"No rows found in line '{line}'.")
            return {name: "" for name in column_names}

        # Headerless mode: there is no header row, so every line is a data row and the
        # configured column_names are 0-based positional indices (given as strings).
        if not self.header_requested:
            # If several lines are passed at once, use the most recent one as the data row.
            row = self._parse_single_csv_row(rows[-1])
            result = {}
            for name in column_names:
                try:
                    idx = int(name)
                except (TypeError, ValueError):
                    self._logger.debug("Requested column '%s' is not a valid index.", name)
                    result[name] = ""
                    continue
                if 0 <= idx < len(row):
                    result[name] = row[idx]
                else:
                    self._logger.debug(f"Index {idx} out of range for row {row}")
                    result[name] = ""
            return result

        # Header mode: the first row is a header, subsequent rows are data.
        row = self._parse_single_csv_row(rows[0])

        # Store header or overwrite when multiple rows.
        if not self._header or len(rows) > 1:
            self._header = row
            self._logger.debug(f"Header detected/stored: {self._header}")
            # Reset row.
            row = ""

        if not self._header:
            self._logger.debug("No header known yet. Skipping line.")
            return {name: "" for name in column_names}

        # If we have mutiple rows we assume the first row to be the header:
        if len(rows) > 1:
            self._logger.info("Multiple rows as input, assuming 1st row to be the header, using the 2nd row as data row")
            row = self._parse_single_csv_row(rows[1])

        if not row:
            return {name: "" for name in column_names}

        result = {}
        for name in column_names:
            if name not in self._header:
                self._logger.debug("Requested column '%s' not in header %s", name, self._header)
                result[name] = ""
                continue
            idx = self._header.index(name)
            if idx >= len(row):
                self._logger.debug(f"Index {idx} out of range for row {row}")
                result[name] = ""
                continue
            result[name] = row[idx]
        return result

    def _detect_delimiter(self, line: str) -> str:
        """
        Detect the separator used in one incoming CSV line.

        Supports both comma-separated and semicolon-separated input.
        It first tries Python's csv.Sniffer for automatic detection.
        If that fails, it falls back to simple heuristics based on the characters found in the line.
        """
        try:
            dialect = csv.Sniffer().sniff(line, delimiters=",;")
            return dialect.delimiter
        except csv.Error:
            # Fallback for short or ambiguous lines where csv.Sniffer cannot
            # reliably determine the separator.
            if ";" in line and "," not in line:
                return ";"
            if line.count(";") > line.count(","):
                return ";"
            return ","

    def _parse_single_csv_row(self, line: str) -> list[str]:
        """
        Parse one text line into a list of CSV fields.

        Empty or whitespace-only input is treated as "no row" and returns an empty list.
        For valid text, the delimiter is detected first and then the line is parsed with Python's csv module
        so quoted fields are handled correctly.
        """
        if not isinstance(line, str) or not line.strip():
            return []
        if self.separator == "":
            # Detect the delimiter
            self.separator = self._detect_delimiter(line)
        reader = csv.reader(StringIO(line), delimiter=self.separator)
        return next(reader, [])
