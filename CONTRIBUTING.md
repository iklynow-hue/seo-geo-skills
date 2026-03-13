# Contributing to SGEO

Thank you for your interest in contributing to the SGEO project! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help maintain a welcoming environment

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone <your-fork-url>`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Install dependencies: `pip install -r requirements.txt`

## Development Setup

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Git

### Installation
```bash
# Install in development mode
pip install -e .

# Install development dependencies
pip install pytest black flake8 mypy
```

## Making Changes

### Code Style
- Follow PEP 8 guidelines
- Use type hints for function signatures
- Add docstrings to all public functions
- Keep functions focused and under 50 lines when possible
- Use meaningful variable names

### Testing
Before submitting a PR:
```bash
# Run linting
flake8 scripts/

# Run type checking
mypy scripts/

# Format code
black scripts/

# Run tests (when available)
pytest tests/
```

### Commit Messages
Follow conventional commits format:
```
type(scope): brief description

Longer description if needed

Fixes #issue-number
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
- `feat(schema): add support for VideoObject schema`
- `fix(robots): handle missing robots.txt gracefully`
- `docs(readme): update installation instructions`

## Pull Request Process

1. **Update documentation** - If you change functionality, update relevant docs
2. **Add tests** - Include tests for new features or bug fixes
3. **Update CHANGELOG.md** - Add your changes under [Unreleased]
4. **Keep PRs focused** - One feature or fix per PR
5. **Write clear descriptions** - Explain what and why, not just how

### PR Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How was this tested?

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Tests added/updated
```

## Reporting Issues

### Bug Reports
Include:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages/stack traces
- Relevant code snippets

### Feature Requests
Include:
- Use case description
- Proposed solution
- Alternative solutions considered
- Impact on existing functionality

## Priority Areas

Current priorities (see CODE-REVIEW.md for details):

### P0 (Critical)
- Rate limit handling for API calls
- Error handling standardization
- Progress indicators for long operations

### P1 (High Priority)
- Integration test suite
- Configuration file support
- Batch processing mode

### P2 (Nice to Have)
- Performance optimizations (MinHash, connection pooling)
- Report comparison feature
- Additional schema types

## Script Development Guidelines

### Adding New Scripts

1. **Follow the template**:
```python
#!/usr/bin/env python3
"""
Brief description of what this script does.

Usage:
    python script_name.py <url>
    python script_name.py <url> --json
"""

import argparse
import json
import sys

def main():
    parser = argparse.ArgumentParser(description="...")
    parser.add_argument("url", help="URL to analyze")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    # Implementation
    result = analyze(args.url)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        # Human-readable output
        print(f"Analysis Results for {args.url}")
        # ...

if __name__ == "__main__":
    main()
```

2. **Error handling**:
```python
result = {
    "url": url,
    "data": {},
    "error": None,
}

try:
    # Analysis logic
except requests.exceptions.RequestException as e:
    result["error"] = f"Request failed: {e}"
    return result
```

3. **Rate limiting**:
```python
import time

max_retries = 3
for attempt in range(max_retries):
    try:
        response = requests.get(url)
        if response.status_code == 429:
            wait_time = (attempt + 1) * 3
            time.sleep(wait_time)
            continue
        break
    except requests.exceptions.RequestException:
        if attempt == max_retries - 1:
            raise
```

4. **Update generate_report.py** - Add your script to the SCRIPT_MAPPING

5. **Update SKILL.md** - Document when to use your script

## Documentation

### README.md
- Keep installation instructions up to date
- Add examples for new features
- Update command reference

### SKILL.md
- Add new commands to the command table
- Update orchestration logic if needed
- Document new MECE categories

### Code Comments
- Explain "why", not "what"
- Document complex algorithms
- Note any workarounds or limitations

## Questions?

- Check existing issues and PRs
- Review CODE-REVIEW.md for known issues
- Ask in issue comments before starting major work

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
