from core.database import initialize_vector_db

if __name__ == "__main__":
    print("Initializing vector databases...")

    # Initialize the Mechatronic Engineer's vector database
    initialize_vector_db("data/mechatronics", "path_to_mechatronic_db")
    print("Mechatronic database initialized successfully.")

    # Initialize the Python Coder's vector database
    initialize_vector_db("data/python", "path_to_python_db")
    print("Python database initialized successfully.")
