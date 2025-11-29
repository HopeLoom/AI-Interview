# Contributing to AI Interview Simulation Platform

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect different viewpoints and experiences

## Getting Started

1. **Fork the repository**
2. **Clone your fork:**
   ```bash
   git clone https://github.com/your-username/AI-Interview.git
   cd AI-Interview
   ```
3. **Set up development environment** (see [SETUP.md](./SETUP.md))
4. **Create a branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### 1. Make Your Changes

- Write clear, readable code
- Follow existing code style
- Add comments for complex logic
- Update documentation as needed

### 2. Test Your Changes

**Frontend:**
```bash
npm run check  # TypeScript type checking
npm run dev    # Test in browser
```

**Backend:**
```bash
cd backend
pytest        # Run tests
```

### 3. Commit Your Changes

Use clear, descriptive commit messages:

```bash
git commit -m "Add feature: description of what you added"
git commit -m "Fix bug: description of what you fixed"
```

**Commit Message Guidelines:**
- Use present tense ("Add feature" not "Added feature")
- Be specific and concise
- Reference issues if applicable: "Fix #123: description"

### 4. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear title and description
- Reference to related issues
- Screenshots (if UI changes)
- Testing notes

## Code Style

### TypeScript/React (Frontend)

- Use TypeScript for type safety
- Follow React best practices
- Use functional components with hooks
- Prefer named exports
- Use meaningful variable names

**Example:**
```typescript
// Good
export function InterviewLayout({ config }: InterviewLayoutProps) {
  const [status, setStatus] = useState<InterviewStatus>('idle');
  // ...
}

// Avoid
export const InterviewLayout = (props: any) => {
  // ...
}
```

### Python (Backend)

- Follow PEP 8 style guide
- Use type hints where possible
- Write docstrings for functions/classes
- Use meaningful variable names
- Keep functions focused and small

**Example:**
```python
async def get_company(
    company_id: str,
    db_service: InterviewConfigurationDatabase = Depends(get_db_service)
) -> Dict[str, Any]:
    """
    Get company details by ID
    
    Args:
        company_id: Company ID
        db_service: Database service instance
        
    Returns:
        Company profile dictionary
    """
    # ...
```

## Project Structure

### Frontend (`client/`)
```
client/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/          # Page components
│   ├── contexts/       # React context providers
│   ├── hooks/          # Custom React hooks
│   ├── services/       # API service layer
│   └── lib/            # Utility functions
```

### Backend (`backend/`)
```
backend/
├── routers/                    # API route handlers
├── master_agent/               # Master agent orchestration
├── panelist_agent/            # AI panelist agents
├── interview_configuration/   # Configuration management
├── core/                      # Core functionality
│   ├── database/             # Database abstraction
│   ├── memory/               # Agent memory systems
│   └── prompting/            # Prompt strategies
└── server/                    # WebSocket server
```

## Areas for Contribution

### High Priority
- **Documentation**: Improve setup guides, API docs, architecture docs
- **Testing**: Add unit tests, integration tests, E2E tests
- **Error Handling**: Improve error messages and recovery
- **Performance**: Optimize database queries, reduce bundle size

### Medium Priority
- **Features**: New interview types, evaluation metrics
- **UI/UX**: Improve user experience, accessibility
- **Examples**: More example configurations in `onboarding_data/`
- **Tools**: Development tools, debugging utilities

### Nice to Have
- **Internationalization**: Multi-language support
- **Themes**: Customizable UI themes
- **Plugins**: Plugin system for extensions
- **Analytics**: Usage analytics and insights

## Pull Request Process

1. **Update Documentation**
   - Update README.md if needed
   - Add/update code comments
   - Update CHANGELOG.md (if exists)

2. **Ensure Tests Pass**
   - All existing tests should pass
   - Add tests for new features
   - Ensure no TypeScript errors

3. **Code Review**
   - Address review comments
   - Keep PR focused (one feature/fix per PR)
   - Respond to feedback promptly

4. **Merge**
   - Maintainer will merge after approval
   - PR will be squashed and merged

## Reporting Issues

### Bug Reports

Include:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment (OS, Node version, Python version)
- Screenshots/logs if applicable

### Feature Requests

Include:
- Clear description of the feature
- Use case/justification
- Proposed implementation (if you have ideas)
- Examples/mockups if applicable

## Questions?

- Open an issue for questions
- Check existing issues and discussions
- Contact: info@hopeloom.com

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🎉

