import argparse

from supplier_entity_mapping.config import get_settings
from supplier_entity_mapping.models.schemas import IndexRequest
from supplier_entity_mapping.services.index_service import IndexService


def main() -> None:
    parser = argparse.ArgumentParser(description="Index supplier vendor data into ChromaDB.")
    parser.add_argument(
        "--file-name",
        dest="file_name",
        default=None,
        help="Vendor file name inside the configured vendor data directory.",
    )
    args = parser.parse_args()

    service = IndexService(get_settings())
    result = service.build_index(IndexRequest(file_name=args.file_name))
    print(
        f"Indexed {result.rows_indexed} supplier rows from {result.file_name} into "
        f"{result.persist_directory}."
    )


if __name__ == "__main__":
    main()
