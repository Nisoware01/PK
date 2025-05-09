import weaviate

# Initialize the client with explicit gRPC port
client = weaviate.connect_to_local(
    port=8082,  # HTTP port
    grpc_port=50051,  # gRPC port - default is 50051
    additional_config=weaviate.classes.init.AdditionalConfig(
        timeout=weaviate.classes.init.Timeout(init=30)  # Increase timeout to 30 seconds
    )
)

# Retrieve all student objects along with the embeddings
def get_student_objects_with_embeddings():
    # Get the Student collection and query objects with explicit field selection
    result = client.query.get("Student", ["name", "age", "major", "motivation", "_additional {vector}"]).do()

    # Print out the properties along with the embeddings
    print("Student objects and their embeddings:")
    for obj in result["data"]["Get"]["Student"]:
        print(f"Name: {obj['name']}")
        print(f"Age: {obj['age']}")
        print(f"Major: {obj['major']}")
        print(f"Motivation: {obj['motivation']}")

        # Fetching embeddings from the "_additional" field
        motivation_embedding = obj["_additional"]["vector"]
        if motivation_embedding is not None:
            print(f"Motivation Embedding: {motivation_embedding}")
        else:
            print("No embedding found for motivation.")
        
        print("--------")

# Run the function to fetch student data along with embeddings
get_student_objects_with_embeddings()

# Close the client connection
client.close()
