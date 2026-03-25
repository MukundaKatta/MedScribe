# Contributing to MedScribe

Thank you for your interest in contributing to MedScribe! This document provides guidelines for contributing to the project.

## Disclaimer

MedScribe is for **research and educational purposes only**. It is NOT validated for clinical use. Please keep this in mind when contributing features or documentation.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Install development dependencies:

```bash
pip install -e ".[dev]"
```

4. Create a feature branch:

```bash
git checkout -b feature/your-feature-name
```

## Development Workflow

### Running Tests

```bash
make test
```

### Linting and Formatting

```bash
make lint
make format
```

### Type Checking

```bash
make type-check
```

## Code Guidelines

- **Python 3.11+** — Use modern Python features (type hints, `|` union syntax, etc.)
- **Pydantic v2** — Use Pydantic models for structured data
- **Regex-based NLP** — This project intentionally avoids ML model dependencies. All text processing should use regex patterns and heuristic rules.
- **Type annotations** — All public functions must have type annotations
- **Docstrings** — All public functions and classes must have docstrings

## Adding New Patterns

When adding new medical regex patterns to `src/medscribe/utils.py`:

1. Add comprehensive test cases in `tests/test_core.py`
2. Use named capture groups for clarity
3. Include comments explaining what the pattern matches
4. Test against realistic clinical text samples

## Pull Request Process

1. Ensure all tests pass: `make all`
2. Update documentation if adding new features
3. Add tests for any new functionality
4. Keep PRs focused — one feature or fix per PR
5. Write a clear PR description explaining the change

## Reporting Issues

When reporting bugs, please include:

- Python version
- MedScribe version
- A minimal reproducible example
- Expected vs. actual behavior

## Code of Conduct

Be respectful, constructive, and inclusive. We are building tools to help developers work with medical text, and we welcome contributors from all backgrounds.

## License

By contributing to MedScribe, you agree that your contributions will be licensed under the MIT License.
