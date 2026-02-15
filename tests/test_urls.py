import pytest
from django.urls import resolve


@pytest.mark.django_db
def test_root_dashboard_route_available_without_language_prefix():
    match = resolve('/')
    assert match.url_name == 'dashboard'
