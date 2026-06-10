import pytest
from unittest.mock import MagicMock
from django.test import RequestFactory


@pytest.mark.django_db
class TestUtilsMiddleware:

    def test_middleware_processes_request(self):
        from utils.middleware import RequestLoggingMiddleware

        factory = RequestFactory()
        request = factory.get("/api/v1/products/")
        get_response = MagicMock(return_value=MagicMock(status_code=200))
        mw = RequestLoggingMiddleware(get_response)
        response = mw(request)
        get_response.assert_called_once_with(request)

    def test_middleware_processes_post(self):
        from utils.middleware import RequestLoggingMiddleware

        factory = RequestFactory()
        request = factory.post("/api/v1/orders/")
        get_response = MagicMock(return_value=MagicMock(status_code=201))
        mw = RequestLoggingMiddleware(get_response)
        mw(request)
        get_response.assert_called_once()

    def test_middleware_with_authenticated_user(self, test_user):
        from utils.middleware import RequestLoggingMiddleware

        factory = RequestFactory()
        request = factory.get("/api/v1/products/")
        request.user = test_user
        get_response = MagicMock(return_value=MagicMock(status_code=200))
        mw = RequestLoggingMiddleware(get_response)
        mw(request)
        get_response.assert_called_once()


class TestLoggingConfig:

    def test_logging_config_importable(self):
        from utils import logging_config

        assert logging_config is not None

    def test_json_formatter_exists(self):
        from utils.logging_config import JSONFormatter

        assert JSONFormatter is not None

    def test_json_formatter_formats_record(self):
        import logging
        from utils.logging_config import JSONFormatter

        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test message",
            args=(),
            exc_info=None,
        )
        result = formatter.format(record)
        import json

        parsed = json.loads(result)
        assert parsed["message"] == "test message"
        assert parsed["level"] == "INFO"

    def test_admin_email_handler_exists(self):
        from utils.logging_config import AdminEmailHandler

        assert AdminEmailHandler is not None

    def test_get_logger_returns_logger(self):
        import logging
        import os
        from unittest.mock import patch

        os.makedirs("logs", exist_ok=True)
        from utils.logging_config import get_logger

        with patch("utils.logging_config.logging.FileHandler"):
            logger = get_logger("test_logger")
            assert isinstance(logger, logging.Logger)


class TestCacheKeys:

    def test_cache_keys_importable(self):
        from utils import cache_keys

        assert cache_keys is not None

    def test_all_keys_are_valid_types(self):
        import utils.cache_keys as ck
        import inspect

        for name in dir(ck):
            if name.startswith("_"):
                continue
            attr = getattr(ck, name)
            # Allow strings, integers (TTL values), and callables
            assert isinstance(attr, (str, int)) or callable(
                attr
            ), f"{name} has unexpected type {type(attr)}"

    def test_key_functions_return_strings(self):
        import utils.cache_keys as ck
        import inspect

        for name in dir(ck):
            if name.startswith("_"):
                continue
            attr = getattr(ck, name)
            if callable(attr) and not inspect.isclass(attr):
                try:
                    result = attr(1)
                    assert isinstance(result, str)
                except TypeError:
                    try:
                        result = attr()
                        assert isinstance(result, str)
                    except TypeError:
                        pass
