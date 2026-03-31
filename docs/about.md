# About WarriorFit

WarriorFit is a comprehensive fitness tracking and management application built with Python and Shiny. It provides tools
for managing workouts, tracking progress, and analyzing fitness data.

## Project Overview

WarriorFit is designed to help users:

- Track their fitness activities and workouts
- Monitor progress over time
- Analyze performance metrics
- Manage training schedules

## Technology Stack

### Core Technologies

- **Python 3.13**: Modern Python runtime
- **Shiny**: Interactive web application framework
- **UV**: Fast Python package manager and dependency resolver
- **Docker**: Containerized deployment

### Documentation

- **MkDocs**: Static site generator
- **Material for MkDocs**: Modern documentation theme
- **MkDocstrings**: API documentation from Python docstrings
- **Swagger Plugin**: API specification rendering

## Deployment

WarriorFit supports containerized deployment using Docker:

### Production Environment

- **Container**: `warriorfit-app`
- **Image**: `warriorfit-app:prod`
- **Port**: 8500 (external) → 8000 (internal)
- **Environment**: `production`
- **Auto-restart**: Enabled with `unless-stopped` policy
- **Configuration**: Mounted from `/etc/WarriorFit/config_prod.yml`
- **Security**: Requires `WF_SECRET_KEY` environment variable

### Deployment Script

The project includes `deploy-prod.sh` for automated production deployment:
