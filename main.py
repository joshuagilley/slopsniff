import os


def main():
    timeout = os.getenv("TIMEOUT_SECONDS", "30")
    print(f"Configured timeout: {timeout}s")
    print("Hello from slopsniff!")


if __name__ == "__main__":
    main()
