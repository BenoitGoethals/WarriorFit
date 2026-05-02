# Dependency Injection Usage Guide

## Overview

The WarriorFit application has been refactored to use `dependency-injector` for managing dependencies between repositories and services. This improves testability, maintainability, and follows SOLID principles.

## Architecture

### Container (`warriorfit/core/container.py`)

The `Container` class is the central DI configuration that defines:
- **Configuration**: Singleton `ApplicationConfig`
- **Repositories**: All repositories are singletons that receive config via DI
- **Services**: All services are singletons that receive their dependencies via DI

### Key Components

1. **Repositories** - Data access layer
   - `UserRepository`
   - `ServicemenRepository`
   - `FitnessTestRepository`
   - `CrossRepository`
   - `MarchRepository`
   - `ReservationRepository`
   - `MomRepository`

2. **Services** - Business logic layer
   - `UserService`
   - `ServiceTest`
   - `ServiceCross`
   - `ServiceMarch`
   - `ReserveFitnessRoomService`

## Usage Examples

### 1. Using Services from Container (Recommended)

```python
from warriorfit.core.container import Container

# Create or get the container
container = Container()

# Get service instances
user_service = container.user_service()
test_service = container.test_service()
cross_service = container.cross_service()

# Use the services
users = await user_service.get_all_users()
```

### 2. Using Services in Application (app.py)

```python
class FitnessWarriorApp:
    _container = Container()

    @classmethod
    def get_container(cls):
        return cls._container

# In server function
container = FitnessWarriorApp.get_container()
user_service = container.user_service()
```

### 3. Legacy Instantiation (Still Supported)

For backward compatibility, all services and repositories can still be instantiated directly:

```python
from warriorfit.services.service_user import UserService

# This still works - creates dependencies internally
user_service = UserService()
```

## Benefits

1. **Testability**: Easy to inject mock dependencies for unit tests
2. **Single Responsibility**: Each class focuses on its core responsibility
3. **Maintainability**: Clear dependency graph
4. **Flexibility**: Easy to swap implementations
5. **Singleton Management**: Repositories and services are singletons by default

## Migration Notes

- All existing code continues to work due to backward compatibility
- Services accept `None` for dependencies and create them if not provided
- Gradually migrate code to use container for better dependency management

## Testing with DI

```python
from warriorfit.core.container import Container
from warriorfit.data.repositories.user_repository import UserRepository

# Override dependencies for testing
container = Container()
container.user_repository.override(MockUserRepository())

# Now services will use the mock
user_service = container.user_service()
```

## Best Practices

1. **Use the container** when you need multiple services or in application entry points
2. **Don't create container instances everywhere** - use `FitnessWarriorApp.get_container()`
3. **Keep backward compatibility** until full migration is complete
4. **Test with DI** - inject mocks through the container for easier testing
