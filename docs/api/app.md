# Application Entry Point

The main application module initializes the DI container, registers pages with role-based access, and manages the broker lifecycle.

## Classes

### PageSpec

A dataclass defining a page: what it is (UI + server) and who may see it.

### FitnessWarriorApp

Main application class — sets up logging, builds the Shiny UI, registers page servers, and handles authentication.

::: warriorfit.app
    options:
      members_order: source
      show_source: true
      show_docstring_attributes: true
