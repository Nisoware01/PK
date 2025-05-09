# def get_static_part(part_number: str) -> str:
#     """Returns the static part before the first [ in the template."""
#     bracket_index = part_number.find('[')
#     if bracket_index == -1:
#         return part_number  # No [ found, entire part is static
#     return part_number[:bracket_index]
import openai
import os

def get_openai_response(prompt):
    openai.api_key = os.getenv('OPENAI_API_KEY')
    
    if openai.api_key is None:
        return "Error: OPENAI_API_KEY environment variable is not set."

    try:
        response = openai.ChatCompletion.create(  # <-- Corrected here
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7
        )

        return response['choices'][0]['message']['content'].strip()

    except Exception as e:
        return f"Error: {str(e)}"


def main():
    print("Welcome to the OpenAI Query Response Program!")

    while True:
        # Taking user input as a query
        user_query = input("\nEnter your query (or type 'exit' to quit): ")

        # If the user types 'exit', the program will stop
        if user_query.lower() == 'exit':
            print("Goodbye!")
            break

        # Get the response from OpenAI
        response = get_openai_response(user_query)

        # Display the response
        print(f"\nOpenAI Response: {response}")

if __name__ == "__main__":
    main()
