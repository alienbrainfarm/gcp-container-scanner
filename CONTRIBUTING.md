# Contributing Guide

Thank you for contributing to the GCP Container Vulnerability Scanner! This guide explains how to develop, test, and submit changes.

## Development Setup

```bash
# Clone repository
git clone <repo-url>
cd gcp-container-scanner

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies with dev extras
pip install -r requirements.txt
pip install -e ".[dev]"

# Set up pre-commit hooks (optional)
pre-commit install
```

## Project Structure

```
src/
├── app.py                    # Main orchestrator
├── cli.py                    # CLI entry point
├── server.py                 # Cloud Run Flask app
├── config/
│   └── settings.py          # Config management
├── models/
│   └── vulnerability.py      # Data classes
├── scanners/
│   ├── base.py              # Abstract scanner
│   └── gcp_scanner.py       # GCP implementation
└── reporters/
    ├── base.py              # Abstract reporter
    └── confluence_reporter.py # Confluence implementation

tests/
├── test_models.py
├── test_gcp_scanner.py
├── test_confluence_reporter.py
└── conftest.py
```

## Making Changes

### Creating a New Scanner

To add support for new vulnerability sources:

1. **Create scanner class** in `src/scanners/new_scanner.py`:

```python
from src.scanners.base import BaseScanner
from src.models import ScanResult
from typing import List

class NewScanner(BaseScanner):
    """Scanner using New Service."""
    
    def __init__(self):
        """Initialize scanner."""
        pass
    
    def scan_image(self, image_uri: str) -> ScanResult:
        """Scan image for vulnerabilities."""
        # Implementation here
        pass
    
    def list_images(self) -> List[str]:
        """List available images."""
        # Implementation here
        pass
```

2. **Export in** `src/scanners/__init__.py`:

```python
from .new_scanner import NewScanner

__all__ = ["NewScanner", "GCPContainerScanner", "BaseScanner"]
```

3. **Create tests** in `tests/test_new_scanner.py`:

```python
import pytest
from src.scanners import NewScanner

@pytest.fixture
def scanner():
    return NewScanner()

def test_scan_image(scanner):
    result = scanner.scan_image("test:latest")
    assert result is not None
```

4. **Use in app** by updating `src/app.py`:

```python
from src.scanners import NewScanner

class ContainerVulnerabilityScanner:
    def __init__(self, scanner_name="gcp"):
        if scanner_name == "new":
            self.scanner = NewScanner()
        else:
            self.scanner = GCPContainerScanner()
```

### Creating a New Reporter

To add support for new reporting destinations:

1. **Create reporter class** in `src/reporters/new_reporter.py`:

```python
from src.reporters.base import BaseReporter
from src.models import ScanResult
from typing import List

class NewReporter(BaseReporter):
    """Reporter for New Service."""
    
    def __init__(self):
        """Initialize reporter."""
        pass
    
    def report(self, scan_results: List[ScanResult]) -> bool:
        """Generate and publish report."""
        # Implementation here
        return True
```

2. **Export in** `src/reporters/__init__.py`
3. **Create tests** in `tests/test_new_reporter.py`
4. **Use in app** by updating `src/app.py`

## Code Standards

### Style Guide

- Follow PEP 8
- Use type hints for all functions
- Max line length: 100 characters
- Use 4 spaces for indentation

### Example:

```python
"""Module docstring."""

from typing import List, Optional
from datetime import datetime
from src.models import ScanResult

def process_results(
    results: List[ScanResult],
    filter_severity: Optional[str] = None,
) -> dict:
    """Process scan results and return summary.
    
    Args:
        results: List of scan results
        filter_severity: Optional severity filter
        
    Returns:
        Summary dictionary
    """
    summary = {
        "total": len(results),
        "timestamp": datetime.utcnow().isoformat(),
    }
    return summary
```

### Comments

- Use docstrings for functions/classes
- Use comments for complex logic
- Keep comments up to date with code

```python
def complex_function(data: List[dict]) -> dict:
    """Process complex data structure."""
    # First, filter items by status
    filtered = [item for item in data if item.get("status") == "active"]
    
    # Then aggregate results
    result = {item["id"]: item["value"] for item in filtered}
    
    return result
```

## Testing

### Running Tests

```bash
# All tests
pytest tests/

# Specific file
pytest tests/test_models.py

# With coverage
pytest tests/ --cov=src --cov-report=html

# Verbose output
pytest tests/ -v

# Match test names
pytest tests/ -k "test_scan"
```

### Writing Tests

```python
"""Tests for feature_name."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.module import ClassName

@pytest.fixture
def setup():
    """Setup test fixtures."""
    return ClassName()

def test_basic_functionality(setup):
    """Test basic functionality."""
    result = setup.method()
    assert result is not None

@pytest.mark.parametrize("input,expected", [
    ("test1", "output1"),
    ("test2", "output2"),
])
def test_with_parameters(input, expected):
    """Test with multiple inputs."""
    assert process(input) == expected

def test_with_mock():
    """Test with mocked dependencies."""
    with patch("src.module.external_call") as mock_call:
        mock_call.return_value = "mocked_value"
        result = function_using_external()
        assert result == "mocked_value"
        mock_call.assert_called_once()
```

### Code Coverage

Aim for >80% coverage:

```bash
# Generate coverage report
pytest tests/ --cov=src --cov-report=html

# View report
open htmlcov/index.html
```

## Documentation

### Docstring Format

Use Google-style docstrings:

```python
def scan_image(self, image_uri: str, timeout: int = 300) -> ScanResult:
    """Scan container image for vulnerabilities.
    
    Args:
        image_uri: Full URI of the container image (e.g., 
            us-central1-docker.pkg.dev/project/repo/image:tag)
        timeout: Scan timeout in seconds (default: 300)
        
    Returns:
        ScanResult containing vulnerabilities and summary
        
    Raises:
        ValueError: If image_uri is invalid
        TimeoutError: If scan exceeds timeout
        
    Example:
        >>> scanner = GCPContainerScanner()
        >>> result = scanner.scan_image("image:latest")
        >>> print(f"Found {result.summary.total} vulnerabilities")
    """
    pass
```

### README Updates

Update README.md if your changes:
- Add/remove features
- Change configuration options
- Modify deployment process
- Add new dependencies

## git Workflow

### Before Starting

```bash
# Update local repo
git fetch origin
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/descriptive-name
```

### Commit Messages

Format: `<type>: <description>`

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`

Examples:
```
feat: add Trivy scanner integration
fix: handle missing Confluence space key
docs: update deployment instructions
test: improve gcp_scanner coverage
refactor: simplify vulnerability filtering
```

### Pushing Changes

```bash
# Push to remote
git push origin feature/descriptive-name

# Create pull request on GitHub
# Fill in description and reference any issues
```

## Pull Request Process

1. **Create PR** with clear title and description
2. **Add tests** for new functionality
3. **Update docs** if needed
4. **Pass CI/CD** checks
5. **Code review** approval
6. **Merge** to main

### PR Checklist

- [ ] Tests pass locally (`pytest tests/`)
- [ ] Code coverage maintained (>80%)
- [ ] Docstrings added/updated
- [ ] README updated if needed
- [ ] No breaking changes documented
- [ ] Commits are descriptive

## Release Process

1. Update version in `src/__init__.py`
2. Update CHANGELOG.md
3. Create git tag: `git tag v1.2.3`
4. Push tag: `git push origin v1.2.3`
5. Publish: `python setup.py sdist bdist_wheel`

## Questions?

- Check [README.md](README.md) for architecture details
- Look at existing code for patterns
- Open a discussion issue
- Ask in pull request comments

## License

By contributing, you agree your code will be licensed under the same license as the project.

Thank you! 🎉
