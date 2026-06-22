# Contributing to Universal Algorithmic Oracle

Thank you for your interest in contributing! 🙏

## How to Contribute

### 1. Fork the Repository
```bash
# Click "Fork" on GitHub, then:
git clone https://github.com/YOUR_USERNAME/universal-algorithmic_oracle.git
cd universal-algorithmic_oracle
git remote add upstream https://github.com/Alirahimi4321/universal-algorithmic_oracle.git
```

### 2. Create a Branch
```bash
git checkout -b feature/amazing-feature
```

### 3. Make Changes
- Follow existing code style
- Add tests for new features
- Update documentation if needed

### 4. Commit
```bash
git commit -m "feat: add amazing feature"
```

### 5. Push & Create PR
```bash
git push origin feature/amazing-feature
```

## Code Style
- Use type hints
- Follow PEP 8
- Add docstrings to public functions
- Keep functions under 50 lines when possible

## Adding a New Symbolic System

1. Create wrapper in `oracle/symbolic/`:
```python
from oracle.symbolic.base import SymbolicSystemWrapper, SymbolicOutput
from oracle.symbolic.registry import register_system

@register_system
class MyNewSystem(SymbolicSystemWrapper):
    SYSTEM_ID = "my_new_system"
    LIBRARY_BACKEND = "my_library"
    
    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        # Your implementation here
        pass
```

2. Add entry in `config/systems.yaml`
3. Add to `oracle/symbolic/registry.py` module list
4. Add tests in `tests/`

## Reporting Bugs
Use GitHub Issues with the bug report template.

## Questions?
Open a Discussion on GitHub.
