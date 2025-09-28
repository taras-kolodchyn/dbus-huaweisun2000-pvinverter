# Contributing

Thanks for taking the time to contribute! This project is used on embedded devices, so
changes should be conservative and well-tested. Below is a short checklist to keep
things smooth.

## Getting started

1. Install the development dependencies:
   ```bash
   python -m pip install --upgrade pip
   pip install '.[dev]'
   ```
2. Run the linters and unit tests before opening a pull request:
   ```bash
   black --check .
   flake8 .
   pytest --maxfail=1 --disable-warnings -q
   ```
3. (Optional) Smoke test the Docker playground:
   ```bash
   docker compose -f docker-compose.dev.yml up --build
   docker compose -f docker-compose.dev.yml down --volumes --remove-orphans
   ```

## Coding guidelines

- Keep Python code formatted with `black` and follow the existing logging style
  (log via the module logger, avoid bare `print`).
- Avoid breaking backward compatibility with the Venus OS environment—changes
  should continue to work on Python 3.8+ with limited system libraries.
- When adding configuration knobs, expose them via D-Bus or environment
  variables rather than hard-coding.
- Add or update tests whenever you touch behaviour that can be verified without
  hardware. Use dependency injection or fakes to keep tests deterministic.

## Submitting changes

- Open an issue describing the problem/feature before starting major work.
- Reference the issue in your pull request and give a short summary of the
  solution and testing performed.
- Update documentation (README, changelog) when behaviour or user workflows
  change.

Thanks again for helping improve the Huawei SUN2000 D-Bus driver!
