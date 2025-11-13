# Backend
- For route specific changes, ensure that you re-run the openAPI script via `scripts/generate_openapi.py`
- Ensure robust and well implemented changes, without backwards compatibility or fall backs, unless explicitly requested by the user.

# Frontend
- If the backend openAPI script has been executed, `yarn gen:sdk` must also be executed and its updated auto-generated files used.
- Ensure robust and well implemented changes, without backwards compatibility or fall backs, unless explicitly requested by the user.

# Workflow
- Ensure to clean-up unnecessary, or obsolete files when you're done.
- Do not create new documentation files unless explicitly asked to do so.
- Ensure robust and well implemented changes, without backwards compatibility or fall backs, unless explicitly requested by the user.