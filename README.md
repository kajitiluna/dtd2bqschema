# dtd2bqschema
Convert to dtd schema to bigquery schema. (json format)

## Usage

```python
from dtd2bqschema import Dtd2BqSchema, BqSchema

file_path: str = "..." # path to dtd file
top_node: str = "..." # top node name

parser: Dtd2BqSchema = Dtd2BqSchema()
bq_schema: BqSchema = parser.parse_from_file(file_path, top_node)

print(bq_schema.to_json())
```
