# === insert_students.py ===
import weaviate
import random
from weaviate.classes.init import AdditionalConfig, Timeout

client = weaviate.connect_to_local(
    port=8082,
    grpc_port=50051,
    additional_config=AdditionalConfig(timeout=Timeout(init=30))
)

student_collection = client.collections.get("Student")

names = [f"Student {i}" for i in range(1, 101)]
majors = ["Computer Science", "Math", "Physics", "Biology", "Engineering"]
motivations = [
    "I want to use AI to solve healthcare problems.",
    "Building intelligent robots fascinates me.",
    "My passion is to develop educational apps for children.",
    "I'm curious about how AI can improve agriculture.",
    "My dream is to work in AI safety and ethics.",
    "Using data science to fight climate change inspires me.",
    "I want to create assistive tech for the visually impaired.",
    "AI in finance and fraud detection is exciting.",
    "I'm driven to automate boring tasks through ML.",
    "I love experimenting with generative AI models."
]

# Generate and insert 100 student records
for i in range(100):
    student = {
        "name": names[i],
        "age": random.randint(18, 30),
        "major": random.choice(majors),
        "motivation": random.choice(motivations)
    }
    student_collection.data.insert(student)

print("Inserted 100 student objects successfully.")
client.close()
