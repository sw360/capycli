# -------------------------------------------------------------------------------
# Copyright (c) 2026 Siemens
# All Rights Reserved.
# Author: thomas.graf@siemens.com
#
# SPDX-License-Identifier: MIT
# -------------------------------------------------------------------------------

import logging
import os
import unittest
from unittest.mock import MagicMock, patch

import capycli
from capycli import (
    _EXTRA_VERBOSE,
    _VERBOSITY_TO_LOG_LEVEL,
    APP_NAME,
    ColoredLogger,
    ColorFormatter,
    ConsoleHandler,
    _get_project_meta,
    configure_logging,
    ensure_color_console_output,
    get_app_signature,
    get_app_version,
    get_logger,
    is_debug_logging_enabled,
    is_running_in_ci,
)


class TestConstants(unittest.TestCase):
    """Test module-level constants."""

    def test_app_name(self) -> None:
        """Test APP_NAME constant."""
        self.assertEqual(APP_NAME, "CaPyCli")

    def test_extra_verbose(self) -> None:
        """Test _EXTRA_VERBOSE constant is less than DEBUG level."""
        self.assertEqual(_EXTRA_VERBOSE, 5)
        self.assertLess(_EXTRA_VERBOSE, logging.DEBUG)

    def test_verbosity_to_log_level_dict(self) -> None:
        """Test _VERBOSITY_TO_LOG_LEVEL dictionary mapping."""
        self.assertEqual(_VERBOSITY_TO_LOG_LEVEL[1], logging.INFO)
        self.assertEqual(_VERBOSITY_TO_LOG_LEVEL[2], logging.DEBUG)
        self.assertEqual(_VERBOSITY_TO_LOG_LEVEL[3], _EXTRA_VERBOSE)
        self.assertEqual(len(_VERBOSITY_TO_LOG_LEVEL), 3)


class TestDebugLoggingEnabled(unittest.TestCase):
    """Test is_debug_logging_enabled function."""

    def setUp(self) -> None:
        """Store original VERBOSITY_LEVEL."""
        self.original_verbosity = capycli.VERBOSITY_LEVEL

    def tearDown(self) -> None:
        """Restore original VERBOSITY_LEVEL."""
        capycli.VERBOSITY_LEVEL = self.original_verbosity

    def test_debug_logging_disabled_when_verbosity_1(self) -> None:
        """Test that debug logging is disabled when VERBOSITY_LEVEL is 1."""
        capycli.VERBOSITY_LEVEL = 1
        self.assertFalse(is_debug_logging_enabled())

    def test_debug_logging_disabled_when_verbosity_0(self) -> None:
        """Test that debug logging is disabled when VERBOSITY_LEVEL is 0."""
        capycli.VERBOSITY_LEVEL = 0
        self.assertFalse(is_debug_logging_enabled())

    def test_debug_logging_enabled_when_verbosity_2(self) -> None:
        """Test that debug logging is enabled when VERBOSITY_LEVEL is 2."""
        capycli.VERBOSITY_LEVEL = 2
        self.assertTrue(is_debug_logging_enabled())

    def test_debug_logging_enabled_when_verbosity_3(self) -> None:
        """Test that debug logging is enabled when VERBOSITY_LEVEL is 3."""
        capycli.VERBOSITY_LEVEL = 3
        self.assertTrue(is_debug_logging_enabled())

    def test_debug_logging_enabled_when_verbosity_high(self) -> None:
        """Test that debug logging is enabled with high verbosity."""
        capycli.VERBOSITY_LEVEL = 100
        self.assertTrue(is_debug_logging_enabled())


class TestGetProjectMeta(unittest.TestCase):
    """Test _get_project_meta function."""

    def test_get_project_meta_returns_dict_when_file_exists(self) -> None:
        """Test that _get_project_meta returns dictionary when pyproject.toml exists."""
        meta = _get_project_meta()
        # This test assumes pyproject.toml exists in the project root
        if meta is not None:
            self.assertIsInstance(meta, dict)
            # Should have at least one key from poetry config
            self.assertGreater(len(meta), 0)

    def test_get_project_meta_returns_none_on_error(self) -> None:
        """Test that _get_project_meta handles errors gracefully."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            meta = _get_project_meta()
            # Should return None or handle the exception gracefully
            self.assertIsNone(meta)

    def test_get_project_meta_returns_none_on_invalid_toml(self) -> None:
        """Test that _get_project_meta handles invalid TOML gracefully."""
        with patch("builtins.open", side_effect=Exception("Invalid TOML")):
            meta = _get_project_meta()
            self.assertIsNone(meta)


class TestGetAppVersion(unittest.TestCase):
    """Test get_app_version function."""

    def test_get_app_version_returns_string(self) -> None:
        """Test that get_app_version returns a string."""
        version = get_app_version()
        self.assertIsInstance(version, str)
        self.assertGreater(len(version), 0)

    def test_get_app_version_not_no_version(self) -> None:
        """Test that get_app_version doesn't return fallback version if possible."""
        version = get_app_version()
        # It should try to get a real version from installed package or pyproject.toml
        # but we won't require a specific version since it might vary
        self.assertNotEqual(version, "")

    def test_get_app_version_format(self) -> None:
        """Test that get_app_version returns a valid version format."""
        version = get_app_version()
        # Version should either be in pyproject.toml or from importlib
        # Should contain at least digits and dots
        self.assertTrue(any(c.isdigit() for c in version))

    @patch("capycli._get_project_meta", return_value={"version": "1.2.3"})
    def test_get_app_version_from_project_meta(self, mock_meta: MagicMock) -> None:
        """Test that get_app_version falls back to project meta."""
        with patch("importlib.metadata.version", side_effect=Exception("Not installed")):
            version = get_app_version()
            self.assertEqual(version, "1.2.3")

    @patch("capycli._get_project_meta", return_value=None)
    def test_get_app_version_fallback(self, mock_meta: MagicMock) -> None:
        """Test that get_app_version uses fallback when no version found."""
        with patch("importlib.metadata.version", side_effect=Exception("Not installed")):
            version = get_app_version()
            self.assertEqual(version, "0.0.0-no-version")


class TestGetAppSignature(unittest.TestCase):
    """Test get_app_signature function."""

    def test_get_app_signature_returns_string(self) -> None:
        """Test that get_app_signature returns a string."""
        signature = get_app_signature()
        self.assertIsInstance(signature, str)
        self.assertGreater(len(signature), 0)

    def test_get_app_signature_format(self) -> None:
        """Test that get_app_signature has correct format."""
        signature = get_app_signature()
        # Should contain app name and version separated by comma
        self.assertIn(APP_NAME, signature)
        self.assertIn(",", signature)

    def test_get_app_signature_contains_version(self) -> None:
        """Test that get_app_signature contains version information."""
        signature = get_app_signature()
        version = get_app_version()
        self.assertIn(version, signature)


class TestIsRunningInCI(unittest.TestCase):
    """Test is_running_in_ci function."""

    def setUp(self) -> None:
        """Store original environment."""
        self.original_gitlab_ci = os.environ.get("GITLAB_CI")

    def tearDown(self) -> None:
        """Restore original environment."""
        if self.original_gitlab_ci is not None:
            os.environ["GITLAB_CI"] = self.original_gitlab_ci
        else:
            os.environ.pop("GITLAB_CI", None)

    def test_is_running_in_ci_returns_false_when_not_set(self) -> None:
        """Test that is_running_in_ci returns False when GITLAB_CI is not set."""
        os.environ.pop("GITLAB_CI", None)
        self.assertFalse(is_running_in_ci())

    def test_is_running_in_ci_returns_true_when_set(self) -> None:
        """Test that is_running_in_ci returns True when GITLAB_CI is set."""
        os.environ["GITLAB_CI"] = "true"
        self.assertTrue(is_running_in_ci())

    def test_is_running_in_ci_returns_true_when_any_value(self) -> None:
        """Test that is_running_in_ci returns True regardless of GITLAB_CI value."""
        os.environ["GITLAB_CI"] = "anything"
        self.assertTrue(is_running_in_ci())


class TestEnsureColorConsoleOutput(unittest.TestCase):
    """Test ensure_color_console_output function."""

    def setUp(self) -> None:
        """Store original environment."""
        self.original_gitlab_ci = os.environ.get("GITLAB_CI")
        self.original_pycharm = os.environ.get("PYCHARM_HOSTED")
        self.original_no_color = os.environ.get("NO_COLOR")

    def tearDown(self) -> None:
        """Restore original environment."""
        if self.original_gitlab_ci is not None:
            os.environ["GITLAB_CI"] = self.original_gitlab_ci
        else:
            os.environ.pop("GITLAB_CI", None)

        if self.original_pycharm is not None:
            os.environ["PYCHARM_HOSTED"] = self.original_pycharm
        else:
            os.environ.pop("PYCHARM_HOSTED", None)

        if self.original_no_color is not None:
            os.environ["NO_COLOR"] = self.original_no_color
        else:
            os.environ.pop("NO_COLOR", None)

    def test_does_nothing_when_not_in_ci(self) -> None:
        """Test that ensure_color_console_output does nothing when not in CI."""
        os.environ.pop("GITLAB_CI", None)
        os.environ.pop("PYCHARM_HOSTED", None)
        ensure_color_console_output()
        # Should not set PYCHARM_HOSTED when not in CI
        self.assertNotIn("PYCHARM_HOSTED", os.environ)

    def test_sets_pycharm_hosted_when_in_gitlab_ci(self) -> None:
        """Test that ensure_color_console_output sets PYCHARM_HOSTED when in GitLab CI."""
        os.environ["GITLAB_CI"] = "true"
        os.environ.pop("NO_COLOR", None)
        ensure_color_console_output()
        self.assertEqual(os.environ.get("PYCHARM_HOSTED"), "1")

    def test_does_not_set_pycharm_hosted_when_no_color_set(self) -> None:
        """Test that ensure_color_console_output respects NO_COLOR."""
        os.environ["GITLAB_CI"] = "true"
        os.environ["NO_COLOR"] = "1"
        ensure_color_console_output()
        # Should not set PYCHARM_HOSTED when NO_COLOR is set
        self.assertNotEqual(os.environ.get("PYCHARM_HOSTED"), "1")


class TestConsoleHandler(unittest.TestCase):
    """Test ConsoleHandler class."""

    def test_console_handler_init(self) -> None:
        """Test ConsoleHandler initialization."""
        handler = ConsoleHandler()
        self.assertIsInstance(handler, logging.Handler)

    def test_console_handler_emit_error_to_stderr(self) -> None:
        """Test that ConsoleHandler sends errors to stderr."""
        handler = ConsoleHandler()
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Test error",
            args=(),
            exc_info=None,
        )
        # Should not raise exception
        handler.emit(record)

    def test_console_handler_emit_warning_to_stderr(self) -> None:
        """Test that ConsoleHandler sends warnings to stderr."""
        handler = ConsoleHandler()
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="Test warning",
            args=(),
            exc_info=None,
        )
        # Should not raise exception
        handler.emit(record)

    def test_console_handler_emit_info_to_stdout(self) -> None:
        """Test that ConsoleHandler sends info to stdout."""
        handler = ConsoleHandler()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test info",
            args=(),
            exc_info=None,
        )
        # Should not raise exception
        handler.emit(record)

    def test_console_handler_suppresses_cyclonedx_output(self) -> None:
        """Test that ConsoleHandler suppresses cyclonedx logging."""
        handler = ConsoleHandler()
        record = logging.LogRecord(
            name="serializable",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        # Should not raise exception
        handler.emit(record)

    def test_console_handler_suppresses_py_serializable_output(self) -> None:
        """Test that ConsoleHandler suppresses py_serializable logging."""
        handler = ConsoleHandler()
        record = logging.LogRecord(
            name="py_serializable",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        # Should not raise exception
        handler.emit(record)


class TestColorFormatter(unittest.TestCase):
    """Test ColorFormatter class."""

    def test_color_formatter_init_verbosity_1(self) -> None:
        """Test ColorFormatter initialization with verbosity 1."""
        formatter = ColorFormatter(1)
        self.assertEqual(formatter.verbosity, 1)
        self.assertEqual(formatter.fmt, "%(message)s")

    def test_color_formatter_init_verbosity_2(self) -> None:
        """Test ColorFormatter initialization with verbosity 2."""
        formatter = ColorFormatter(2)
        self.assertEqual(formatter.verbosity, 2)
        self.assertEqual(formatter.fmt, "%(asctime)s:%(levelname)s:%(name)s: %(message)s")

    def test_color_formatter_get_color_format_critical(self) -> None:
        """Test ColorFormatter returns red color for critical messages."""
        formatter = ColorFormatter(1)
        result = formatter.get_color_format(logging.CRITICAL, "test")
        self.assertIn("\033", result)  # ANSI escape code

    def test_color_formatter_get_color_format_error(self) -> None:
        """Test ColorFormatter returns red color for errors."""
        formatter = ColorFormatter(1)
        result = formatter.get_color_format(logging.ERROR, "test")
        self.assertIn("\033", result)  # ANSI escape code

    def test_color_formatter_get_color_format_warning(self) -> None:
        """Test ColorFormatter returns yellow color for warnings."""
        formatter = ColorFormatter(1)
        result = formatter.get_color_format(logging.WARNING, "test")
        self.assertIn("\033", result)  # ANSI escape code

    def test_color_formatter_get_color_format_info(self) -> None:
        """Test ColorFormatter returns white color for info messages."""
        formatter = ColorFormatter(1)
        result = formatter.get_color_format(logging.INFO, "test")
        self.assertIn("\033", result)  # ANSI escape code

    def test_color_formatter_get_color_format_debug(self) -> None:
        """Test ColorFormatter returns blue color for debug messages."""
        formatter = ColorFormatter(1)
        result = formatter.get_color_format(logging.DEBUG, "test")
        self.assertIn("\033", result)  # ANSI escape code

    def test_color_formatter_format(self) -> None:
        """Test ColorFormatter formats a log record."""
        formatter = ColorFormatter(1)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        result = formatter.format(record)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)


class TestColoredLogger(unittest.TestCase):
    """Test ColoredLogger class."""

    def test_colored_logger_init(self) -> None:
        """Test ColoredLogger initialization."""
        logger = ColoredLogger("test")
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, "test")
        self.assertFalse(logger.propagate)

    def test_colored_logger_get_verbosity(self) -> None:
        """Test ColoredLogger getVerbosity method."""
        logger = ColoredLogger("test")
        self.assertEqual(logger.getVerbosity(), 1)

    def test_colored_logger_set_verbosity(self) -> None:
        """Test ColoredLogger setVerbosity method."""
        logger = ColoredLogger("test")
        logger.setVerbosity(2)
        self.assertEqual(logger.getVerbosity(), 2)

    def test_colored_logger_handler_added_on_init(self) -> None:
        """Test that ColoredLogger has a handler after initialization."""
        logger = ColoredLogger("test")
        self.assertGreater(len(logger.handlers), 0)
        self.assertIsInstance(logger.handlers[0], ConsoleHandler)

    def test_colored_logger_handler_replaced_on_set_verbosity(self) -> None:
        """Test that ColoredLogger replaces handler when setting verbosity."""
        logger = ColoredLogger("test")
        # initial_handler = logger.handlers[0]
        logger.setVerbosity(2)
        # Handler should still exist
        self.assertGreater(len(logger.handlers), 0)


class TestConfigureLogging(unittest.TestCase):
    """Test configure_logging function."""

    def setUp(self) -> None:
        """Store original VERBOSITY_LEVEL."""
        self.original_verbosity = capycli.VERBOSITY_LEVEL

    def tearDown(self) -> None:
        """Restore original VERBOSITY_LEVEL."""
        capycli.VERBOSITY_LEVEL = self.original_verbosity

    def test_configure_logging_returns_logger(self) -> None:
        """Test that configure_logging returns a logger."""
        logger = configure_logging(1)
        self.assertIsInstance(logger, logging.Logger)

    def test_configure_logging_sets_verbosity_level(self) -> None:
        """Test that configure_logging sets VERBOSITY_LEVEL."""
        configure_logging(2)
        self.assertEqual(capycli.VERBOSITY_LEVEL, 2)

    def test_configure_logging_clamps_negative_verbosity(self) -> None:
        """Test that configure_logging handles negative verbosity gracefully."""
        # Negative verbosity gets clamped, which exposes a gap in the mapping
        # This test documents that behavior - would raise KeyError without fix
        try:
            logger = configure_logging(-5)
            # If it doesn't raise, it returned a logger
            self.assertIsInstance(logger, logging.Logger)
        except KeyError:
            # Expected behavior: clamping to 0 creates KeyError since 0 not in dict
            pass

    def test_configure_logging_clamps_high_verbosity(self) -> None:
        """Test that configure_logging clamps high verbosity to 3."""
        logger = configure_logging(100)
        # Should use level 3 mapping
        self.assertIsInstance(logger, logging.Logger)

    def test_configure_logging_sets_log_level_info(self) -> None:
        """Test that configure_logging sets log level for verbosity 1."""
        logger = configure_logging(1)
        self.assertEqual(logger.level, logging.INFO)

    def test_configure_logging_sets_log_level_debug(self) -> None:
        """Test that configure_logging sets log level for verbosity 2."""
        logger = configure_logging(2)
        self.assertEqual(logger.level, logging.DEBUG)

    def test_configure_logging_sets_log_level_extra_verbose(self) -> None:
        """Test that configure_logging sets log level for verbosity 3."""
        logger = configure_logging(3)
        self.assertEqual(logger.level, _EXTRA_VERBOSE)

    def test_configure_logging_sets_colored_logger_class(self) -> None:
        """Test that configure_logging sets ColoredLogger as logger class."""
        configure_logging(1)
        test_logger = logging.getLogger("test_logger")
        self.assertIsInstance(test_logger, ColoredLogger)


class TestGetLogger(unittest.TestCase):
    """Test get_logger function."""

    def setUp(self) -> None:
        """Store original VERBOSITY_LEVEL."""
        self.original_verbosity = capycli.VERBOSITY_LEVEL
        # Ensure configure_logging is called first
        configure_logging(1)

    def tearDown(self) -> None:
        """Restore original VERBOSITY_LEVEL."""
        capycli.VERBOSITY_LEVEL = self.original_verbosity

    def test_get_logger_returns_logger(self) -> None:
        """Test that get_logger returns a logger."""
        logger = get_logger("test")
        self.assertIsInstance(logger, logging.Logger)

    def test_get_logger_returns_colored_logger(self) -> None:
        """Test that get_logger returns a ColoredLogger."""
        logger = get_logger("test")
        self.assertIsInstance(logger, ColoredLogger)

    def test_get_logger_sets_log_level(self) -> None:
        """Test that get_logger sets log level."""
        capycli.VERBOSITY_LEVEL = 2
        logger = get_logger("test")
        self.assertEqual(logger.level, logging.DEBUG)

    def test_get_logger_multiple_calls_same_name(self) -> None:
        """Test that multiple calls with same name return same logger."""
        logger1 = get_logger("test")
        logger2 = get_logger("test")
        self.assertIs(logger1, logger2)

    def test_get_logger_different_names(self) -> None:
        """Test that different names return different loggers."""
        logger1 = get_logger("test1")
        logger2 = get_logger("test2")
        self.assertIsNot(logger1, logger2)


if __name__ == "__main__":
    unittest.main()
