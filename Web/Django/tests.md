### 🧪 Types of Tests

To achieve **complete and effective test coverage**, the following types of tests are implemented:

- **Unit Tests**
  - Verify individual units of code such as **functions, methods, or classes**
  - Ensure each unit behaves as expected **in isolation**, without relying on other parts of the system
  - **Examples:** Service functions, Utility methods, Model methods (business logic)

- **Integration Tests**
  - Validate how **different components interact** with each other
  - In Django REST Framework, this typically includes:
    - Correct data flow between layers (**View ↔ Serializer ↔ Model**)
    - Database read/write operations
    - Authentication and permission handling
  - Ensure components integrate correctly as a whole

- **Functional (API) Tests**
  - Focus on **end-to-end functionality** from the user’s perspective
  - Verify that users can successfully: Create, Read, Update, Delete (CRUD) resources through the API

- **Regression Tests**
  - Ensure that **new code changes do not break existing functionality**
  - Should be executed regularly, especially after: Adding new features, Fixing bugs

- **Performance Tests**
  - Evaluate application behavior under **load and stress conditions**
  - Useful for:
    - Identifying performance bottlenecks
    - Measuring response times and throughput
    - Ensuring the system can handle expected traffic levels

## 🧪 Test Setup
### 📦 Testing Dependencies

Install the required testing packages:

```bash
pip install pytest pytest-django coverage pytest-mock factory-boy
```
### ⚙️ pytest Configuration
Create a pytest.ini file at the project root:
```
[pytest]
DJANGO_SETTINGS_MODULE = tests.settings  # Dedicated settings for tests
python_files = test_*.py  # Test file naming convention
addopts = -ra -q  # Cleaner test output
```
🧩 Test Settings
Create a separate Django settings module for tests:
```
tests/
└── settings.py
    from .base import *
    
    DEBUG = False
    
    PASSWORD_HASHERS = [
        "django.contrib.auth.hashers.MD5PasswordHasher",
    ]
    
    EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
```
### 🧱 Test Directory Structure
Recommended structure:
```
project/
├── pytest.ini
├── conftest.py              # Global fixtures
├── tests/
│   └── settings.py
├── apps/
│   ├── accounts/
│   │   └── tests/
│   │       ├── factories.py
│   │       └── test_models.py
```
### 🧪 Global Fixtures (conftest.py)
```
import pytest
from rest_framework.test import APIClient
from accounts.tests.factories import UserFactory

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user():
    return UserFactory()

@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client
```

### 🏗 Factory Setup (factory-boy)
Factories are used to generate consistent and realistic test data.
```
# Example factory:

import factory
from accounts.models import User

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@test.com")
    first_name = "Test"
    last_name = "User"
    is_active = True
```
### 🧠 Mocking with pytest-mock
Use pytest-mock to isolate external dependencies such as emails, payments, or third-party APIs.
```
# Example

def test_notification_sent(mocker):
    mocker.patch(
        "fraud.services.send_notification",
        return_value=True
    )
```
### ▶️ Running Tests
Run the full test suite:
```
pytest
```
Run tests with coverage:
```
coverage run -m pytest
coverage report --include="apps/*" --show-missing
coverage html
```





