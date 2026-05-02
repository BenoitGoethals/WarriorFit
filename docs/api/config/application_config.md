# Application Configuration

Singleton configuration manager that loads from YAML (`config_dev.yml` or `/etc/WarriorFit/config.yml`), manages database connections, and provides settings access.

## Key Responsibilities

- Load/save YAML configuration
- Setup SQLAlchemy async database connection
- Provide access to settings (DB, mail, HR, PDF paths)

::: warriorfit.config.appliccation_config
    options:
      members_order: source
      show_source: true
      show_docstring_attributes: true
