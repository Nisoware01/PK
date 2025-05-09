# === query_students.py ===
import weaviate
from weaviate.classes.query import Filter, MetadataQuery
from weaviate.classes.init import AdditionalConfig, Timeout

client = weaviate.connect_to_local(
    port=8082,
    grpc_port=50051,
    additional_config=AdditionalConfig(timeout=Timeout(init=30))
)

student_collection = client.collections.get("Student")

# Input query text
query_motivation = "I'm interested in AI for solving environmental issues."

# Perform semantic similarity search on the vectorized 'motivation' field
results = student_collection.query.near_text(
    query=query_motivation,
    limit=5,
    return_metadata=MetadataQuery(distance=True)
)

print("Top 5 matching students:")
for i, obj in enumerate(results.objects, 1):
    print(f"{i}. Name: {obj.properties['name']}")
    print(f"   Age: {obj.properties['age']}")
    print(f"   Major: {obj.properties['major']}")
    print(f"   Motivation: {obj.properties['motivation']}")
    print(f"   Cosine Distance: {obj.metadata.distance:.4f}")
    print("-" * 50)

client.close()
