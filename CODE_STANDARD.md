# Coding Standards

This project follows a simple guideline to keep input/output operations separate from business logic.

1. **Pure functions for logic** – Calculations, data transformations and API wrappers should be implemented as functions that accept arguments and return data without performing file or network I/O on their own.
2. **I/O in CLI layers** – Reading configuration files, loading CSV data, sending requests or writing results should be handled in small wrappers or in the `main()` functions of scripts.
3. **Testability** – Separating logic from I/O makes it easier to write unit tests. Aim to design functions so they can be tested without external resources.
4. **Documentation** – Keep this policy in mind when adding new modules or scripts. Update this file if exceptions are required.

Following these rules keeps the codebase maintainable and easier to extend.
