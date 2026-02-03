# Contributing to DMS (Document Management System)

Thank you for your interest in contributing to the DMS project! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Welcome all constructive feedback
- Focus on the code, not the person
- Help others learn and grow

## Getting Started

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- Git
- Basic knowledge of FastAPI and SQLAlchemy

### Development Setup

1. **Fork the repository**
   ```bash
   # Click "Fork" on GitHub
   ```

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/dms.git
   cd dms
   ```

3. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Set up development environment**
   ```bash
   # Create virtual environment
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   pip install -r tests/requirements.txt
   ```

5. **Configure development environment**
   ```bash
   cp .env.production .env
   # Edit .env with development values
   nano .env
   ```

6. **Start services**
   ```bash
   sudo docker compose up -d db
   ```

## Development Workflow

### Making Changes

1. **Create feature branch** from `main` or `develop`
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make your changes**
   - Follow the existing code style
   - Add comments for complex logic
   - Write tests for new features

3. **Run tests**
   ```bash
   # Run all tests
   python -m pytest tests/
   
   # Run specific test
   python -m pytest tests/test_api.py -v
   
   # Security tests
   bash test_security.sh
   ```

4. **Run linting** (if configured)
   ```bash
   # Check code style
   flake8 app/
   pylint app/
   ```

5. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: Add meaningful feature description"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/my-feature
   ```

7. **Create Pull Request**
   - Go to GitHub and click "Create Pull Request"
   - Fill in the PR template
   - Reference any related issues

## Commit Message Guidelines

Use clear, descriptive commit messages:

```
type: Short description (50 chars max)

Longer explanation of the changes if needed.
Explain the "why" not just the "what".

Fixes #issue_number
```

### Commit Types
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, semicolons, etc.)
- `refactor:` Code refactoring without feature changes
- `perf:` Performance improvements
- `test:` Adding or updating tests
- `chore:` Build process, dependencies, etc.

Example:
```bash
git commit -m "feat: Add rate limiting to authentication endpoints

- Implement custom rate limiting middleware
- 5 requests per minute per IP
- Return 429 Too Many Requests when exceeded
- Add tests for rate limiting

Fixes #42"
```

## Pull Request Process

### Before Submitting

1. **Update your branch** with latest changes
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all tests**
   ```bash
   python -m pytest tests/ -v
   bash test_security.sh
   ```

3. **Check code quality**
   - No hardcoded secrets
   - Proper error handling
   - Comments for complex logic

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
- [ ] Tested locally
- [ ] All tests pass
- [ ] New tests added

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated
```

### PR Review Guidelines

- Maintainers will review within 2-3 days
- Respond to feedback promptly
- Ask questions if anything is unclear
- Once approved, a maintainer will merge

## Reporting Issues

### Bug Reports

Include:
- Clear, descriptive title
- Steps to reproduce
- Expected behavior
- Actual behavior
- Screenshots/logs if applicable
- Environment details (OS, Docker version, Python version)

### Feature Requests

Include:
- Clear description of the feature
- Use case/motivation
- Proposed implementation (optional)
- Examples/mockups (if applicable)

## Documentation

### Code Comments
- Comment "why", not "what"
- Use clear, concise language
- Update comments when code changes

### Documentation Files
- Update relevant markdown files
- Keep API documentation current
- Add examples for new features

### Docstrings
```python
def my_function(param1: str, param2: int) -> dict:
    """
    Brief description of what function does.
    
    Longer explanation if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When something goes wrong
        
    Example:
        >>> result = my_function("test", 42)
        >>> result['key']
        'value'
    """
    pass
```

## Testing Guidelines

### Write Tests For:
- New features
- Bug fixes
- Critical functionality
- Edge cases

### Test File Structure
```python
import pytest
from app.routers import documents

class TestDocuments:
    """Test document endpoints"""
    
    def test_get_documents(self, client, admin_token):
        """Test retrieving document list"""
        response = client.get(
            "/api/documents/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
    def test_create_document(self, client, admin_token):
        """Test creating a new document"""
        response = client.post(
            "/api/documents/",
            json={"title": "Test", "content": "Content"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 201
```

## Code Style

### Python
- Follow PEP 8
- Use type hints
- Max line length: 100 characters
- 4 spaces for indentation

### FastAPI
- Use dependency injection
- Proper error handling with HTTPException
- Comprehensive docstrings
- Input validation with Pydantic

### Security
- Never commit secrets
- Use environment variables
- Validate all inputs
- Use secure password hashing
- Add authentication where needed

## Setting Up Pre-commit Hooks (Optional)

```bash
pip install pre-commit
pre-commit install
```

Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
  - repo: https://github.com/PyCQA/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
```

## Building and Testing Locally

```bash
# Build Docker image
docker compose build --no-cache

# Run services
docker compose up -d

# Run tests
python -m pytest tests/ -v

# Security tests
bash test_security.sh

# View logs
docker compose logs -f app

# Stop services
docker compose down
```

## Documentation Structure

```
docs/
├── README.md (main documentation)
├── INSTALLATION.md
├── CONFIGURATION.md
├── API.md
└── TROUBLESHOOTING.md
```

## Areas for Contribution

- [ ] Feature development
- [ ] Bug fixes
- [ ] Documentation improvements
- [ ] Test coverage
- [ ] Performance optimization
- [ ] Security hardening
- [ ] UI/UX improvements
- [ ] Translation (i18n)

## Release Process

1. Update version in `main.py` and `setup.py`
2. Update `CHANGELOG.md`
3. Create git tag: `git tag v1.0.0`
4. Push to repository
5. Create GitHub Release

## Questions?

- Check [DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md)
- Open a GitHub Discussion
- Email the maintainers
- Join our community

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Acknowledgments

Thank you for contributing to make DMS better! 🎉

---

Happy coding! 👨‍💻👩‍💻
