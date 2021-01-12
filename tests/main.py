import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from dtd2bqschema import Dtd2BqSchema, BqSchema


def main():
    """
    For operation check.

    Args:
        file_path (str): dtd file path for analizing
        top_node (str): display for element name
    """

    file_path: str = sys.argv[1]
    top_node: str = sys.argv[2]
    parser: Dtd2BqSchema = Dtd2BqSchema()
    bq_schema: BqSchema = parser.parse_from_file(file_path, top_node)

    print(bq_schema.to_json())


if __name__ == "__main__":
    main()
