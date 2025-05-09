import weaviate
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.init import AdditionalConfig, Timeout

# Initialize the client with explicit gRPC port
client = weaviate.connect_to_local(
    port=8082,  # HTTP port
    grpc_port=50051,  # gRPC port - default is 50051
    additional_config=AdditionalConfig(
        timeout=Timeout(init=30)  # Increase timeout to 30 seconds
    )
)

# Create schema for "Student" collection
def create_schema():
    client.collections.create(
        name="Student",
        properties=[
            Property(
                name="name", 
                data_type=DataType.TEXT,
                skip_vectorization=True  # Skip vectorizing this property
            ),
            Property(
                name="age", 
                data_type=DataType.INT
            ),
            Property(
                name="major", 
                data_type=DataType.TEXT,
                skip_vectorization=True  # Skip vectorizing this property
            ),
            Property(
                name="motivation", 
                data_type=DataType.TEXT
                # No skip_vectorization parameter, so this will be vectorized
            )
        ],
        vectorizer_config=Configure.Vectorizer.text2vec_transformers()
    )
    print("Schema created successfully!")

# Add a student object with normal fields and a motivation paragraph
def add_student_object():
    student_data = {
        "name": "John Doe",
        "age": 21,
        "major": "Computer Science",
        "motivation": "I am passionate about learning AI and creating real-world applications that can make a positive impact on society."
    }

    # Get the Student collection and add the object
    student_collection = client.collections.get("Student")
    student_collection.data.insert(student_data)
    print("Student object added successfully!")

# Retrieve all student objects to check if the data is added
def get_student_object():
    # Get the Student collection and query objects
    student_collection = client.collections.get("Student")
    result = student_collection.query.fetch_objects(include_vector=True)
    print("Student objects:")
    for obj in result.objects:
        print("Properties:", obj.properties)
        print("Vector_length:", len(obj.vector['default']))  # This will show the vector embeddings

if client.collections.exists("Student"):
    client.collections.delete("Student")
    print("Deleted existing Student collection")
# Run the functions
create_schema()
add_student_object()
get_student_object()

# Close the client connection
client.close()
