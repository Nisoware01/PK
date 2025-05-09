# === schema_creation.py ===
import weaviate
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.init import AdditionalConfig, Timeout

client = weaviate.connect_to_local(
    port=8082,
    grpc_port=50051,
    additional_config=AdditionalConfig(timeout=Timeout(init=30))
)

# Delete existing schema if it exists
if client.collections.exists("Student"):
    client.collections.delete("Student")
    print("Deleted existing Student collection")

# Create new schema
client.collections.create(
    name="Student",
    properties=[
        Property(name="name", data_type=DataType.TEXT, skip_vectorization=True),
        Property(name="age", data_type=DataType.INT),
        Property(name="major", data_type=DataType.TEXT, skip_vectorization=True),
        Property(name="motivation", data_type=DataType.TEXT)
    ],
    vectorizer_config=Configure.Vectorizer.text2vec_transformers()
)

print("Schema created successfully!")
client.close()
