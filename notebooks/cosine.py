import openai
import numpy as np
from numpy.linalg import norm
import os
# Initialize OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Function to get embeddings from OpenAI
def get_embedding(text: str) -> np.ndarray:
    response = openai.Embedding.create(
        model="text-embedding-3-large",  # You can use the appropriate model here
        input=text
    )
    return np.array(response['data'][0]['embedding'])

# Function to calculate cosine similarity
def cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    # Compute the cosine similarity between two embeddings
    dot_product = np.dot(embedding1, embedding2)
    norm1 = norm(embedding1)
    norm2 = norm(embedding2)
    return dot_product / (norm1 * norm2)

# Main function to fetch embeddings and calculate cosine similarity
def calculate_similarity(text1: str, text2: str) -> float:
    # Fetch embeddings for both texts
    embedding1 = get_embedding(text1)
    embedding2 = get_embedding(text2)
    
    # Calculate cosine similarity
    similarity = cosine_similarity(embedding1, embedding2)
    
    return similarity

# Example usage
text1 = ("The acceptable values of length range for the component is from 15 mm to 20 mm, increase by 1 mm increments. When comparing this length with others, focus on identifying any overlapping or intersecting values within this length interval."
"The acceptable values of diameter range for the component is from 100 mm to 200 mm, increase by 1 mm increments. When comparing this length with others, focus on identifying any overlapping or intersecting values within this length interval."

)


text2 = ("The acceptable values of length range for the component is from 20 mm to 25 mm, increase by 1 mm increments. When comparing this length with others, focus on identifying any overlapping or intersecting values within this length interval."
"The acceptable values of diameter range for the component is from 150 mm to 200 mm, increase by 1 mm increments. When comparing this length with others, focus on identifying any overlapping or intersecting values within this length interval."

)
similarity_score = calculate_similarity(text1, text2)
print(f"Cosine Similarity: {similarity_score}")
