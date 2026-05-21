# KOII Project Manifest

This `koii.md` is the primary manifest the KOII agent reads on startup.
It should describe project-level goals, allowed operations, and important notes.

Example:

# Project: MyApp

- description: Example project where KOII agents can run tests, review code, and deploy.
- primary_agent: reviewer
- allowed_commands:
  - git
  - docker
  - systemctl

# Usage

Place configuration under `.koii/`.
KOII will automatically read `koii.md` each time it starts.
