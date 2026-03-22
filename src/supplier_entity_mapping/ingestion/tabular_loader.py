from pathlib import Path

import pandas as pd

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


def resolve_vendor_file(data_dir: Path, file_name: str | None = None) -> Path:
    resolved_data_dir = data_dir.resolve()

    if file_name:
        candidate = (resolved_data_dir / file_name).resolve()
        if resolved_data_dir != candidate.parent and resolved_data_dir not in candidate.parents:
            raise ValueError(
                "Vendor data file must be inside the configured vendor data directory."
            )
        if not candidate.exists():
            raise FileNotFoundError(f"Vendor data file not found: {candidate}")
        return candidate

    available_files = sorted(
        path
        for path in resolved_data_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )
    if not available_files:
        raise FileNotFoundError(f"No vendor data files found in {resolved_data_dir}")
    return available_files[0]


def load_tabular_file(file_path: Path) -> pd.DataFrame:
    suffix = file_path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {suffix}")

    try:
        if suffix == ".csv":
            dataframe = pd.read_csv(file_path)
        else:
            dataframe = pd.read_excel(file_path)
    except Exception as exc:
        raise ValueError(f"Unable to read vendor data file '{file_path.name}': {exc}") from exc

    if dataframe.empty:
        raise ValueError(f"Vendor data file is empty: {file_path}")

    return dataframe.fillna("")
