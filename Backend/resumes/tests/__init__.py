"""
Test package for resumes app

This package contains comprehensive tests for:
- Models (test_models.py)
- Serializers (test_serializers.py) 
- Views (test_views.py)
- URLs (test_urls.py)
- Utils (test_utils.py)

Run all tests with:
python manage.py test resumes

Run specific test files with:
python manage.py test resumes.tests.test_models
python manage.py test resumes.tests.test_serializers
python manage.py test resumes.tests.test_views
python manage.py test resumes.tests.test_urls
python manage.py test resumes.tests.test_utils

Run with coverage:
coverage run --source='.' manage.py test resumes
coverage report
coverage html
"""