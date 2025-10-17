# Commit Message Convention

Maniforge uses [Conventional Commits](https://www.conventionalcommits.org/) for automatic semantic versioning.

## Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

## Types

### Version Bumps

- `feat:` - New feature → **Minor version bump** (0.1.0 → 0.2.0)
- `fix:` - Bug fix → **Patch version bump** (0.1.0 → 0.1.1)
- `perf:` - Performance improvement → **Patch version bump** (0.1.0 → 0.1.1)
- `feat!:` or `fix!:` - Breaking change → **Major version bump** (0.1.0 → 1.0.0)

### No Version Bump

- `docs:` - Documentation only
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding/updating tests
- `build:` - Build system changes
- `ci:` - CI configuration changes
- `chore:` - Other changes

## Examples

### Feature (Minor)
```bash
git commit -m "feat: add NFS storage support"
git commit -m "feat(storage): implement S3 backend"
```

### Fix (Patch)
```bash
git commit -m "fix: resolve port binding issue"
git commit -m "fix(network): handle hostNetwork properly"
```

### Breaking Change (Major)
```bash
git commit -m "feat!: redesign configuration format"

git commit -m "feat: switch to new config format

BREAKING CHANGE: configuration file structure has changed"
```

### No Release
```bash
git commit -m "docs: update README installation section"
git commit -m "style: format code with black"
git commit -m "chore: update dependencies"
```

## Multi-line Commits

```bash
git commit -m "feat: add ingress support

- Automatic subdomain generation
- TLS certificate configuration
- Custom annotations support

Closes #42"
```

## Workflow

1. Make changes
2. Stage files: `git add .`
3. Commit with conventional format: `git commit -m "feat: your feature"`
4. Push to main: `git push origin main`
5. Automatic release triggers based on commit types

## Tips

- Use present tense: "add feature" not "added feature"
- Use imperative: "move cursor" not "moves cursor"
- Keep first line under 72 characters
- Reference issues: "Fixes #123" or "Closes #456"
- Breaking changes: use `!` or `BREAKING CHANGE:` in footer

## Release Notes

The CHANGELOG.md is automatically generated from commit messages. Write clear, user-facing descriptions.

**Good:**
```
feat: add support for external secrets
fix: resolve crash when namespace is empty
```

**Bad:**
```
feat: update code
fix: stuff
```
