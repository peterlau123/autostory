# How to contribute

## Branch Naming Convention

Please use the following branch naming convention:

- `feature/<description>` - for new features
- `bugfix/<description>` - for bug fixes
- `hotfix/<description>` - for critical fixes to production
- `refactor/<description>` - for code refactoring
- `docs/<description>` - for documentation changes

Example: `feature/add-user-authentication`

## Commit Message Convention

We follow [Conventional Commits](https://conventionalcommits.org/) specification.

Format: `<type>(<scope>): <description>`

### Types:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code (white-space, formatting, etc)
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `build`: Changes that affect the build system or external dependencies
- `ci`: Changes to our CI configuration files and scripts
- `chore`: Other changes that don't modify src or test files

### Examples:
- `feat: add user authentication`
- `fix: resolve login timeout issue`
- `docs: update API documentation`

### Breaking Changes:
Append `!` after type/scope: `feat!: change API response format`

Pre-commit hooks will validate commit messages automatically.

## Dependencies

We use `poetry` to manage the [dependencies](https://github.com/python-poetry/poetry).
If you dont have `poetry`, you should install with `make poetry-download`.

To install dependencies and prepare [`pre-commit`](https://pre-commit.com/) hooks you would need to run `install` command:

```bash
make install
make pre-commit-install
```

To activate your `virtualenv` run `poetry shell`.

## Code Formatting

We use **Black** as the primary Python code formatter with a line length of 88 characters.

### Auto-formatting

Pre-commit hooks automatically format your code before each commit using:
- **Black**: Code formatting
- **isort**: Import sorting
- **pyupgrade**: Python syntax upgrades

To manually format code:

```bash
make codestyle
```

### Checks

Many checks are configured for this project. Command `make check-codestyle` will check black, isort and darglint.
The `make check-safety` command will look at the security of your code.

Command `make lint` applies all checks.

### Before submitting

Before submitting your code please do the following steps:

1. Add any changes you want
1. Add tests for the new changes
1. Edit documentation if you have changed something significant
1. Run `make codestyle` to format your changes.
1. Run `make lint` to ensure that types, security and docstrings are okay.

## Other help

You can contribute by spreading a word about this library.
It would also be a huge contribution to write
a short article on how you are using this project.
You can also share your best practices with us.
