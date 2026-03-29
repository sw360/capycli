# Project general coding guidelines

This project implements a comprehensive a Python tool to create and manage
SBOMs and to interact with SW360. The project is structured into multiple modules,
each responsible for specific functionalities such as SBOM generation, SW360 interaction,
and command-line interface (CLI) management.

## General

- Use `poetry` to manage the project.
- Use `requests` for HTTP communication.
- Use `pytest` for unit testing.
- Use `responses` for mocking HTTP requests.

## Code Style

- use `flake8`
- use `isort`
- use type hints
- use `requests` for HTTP communication

## Naming Conventions

- Follow PEP 8 naming conventions
- Use ALL_CAPS for constants

## Code Quality

- Use meaningful variable and function names that clearly describe their purpose
- Include helpful comments for complex logic
- Add error handling for user inputs and API calls
- Use type hints throughout the codebase for better IDE support
- Include docstrings for all public methods
