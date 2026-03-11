from __future__ import annotations

from cryptography.fernet import Fernet


def main() -> None:
    print("Generated Fernet session key for LINKEDIN_SESSION_KEY:")
    print(Fernet.generate_key().decode("utf-8"))


if __name__ == "__main__":
    main()
