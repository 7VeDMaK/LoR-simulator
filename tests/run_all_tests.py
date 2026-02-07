import unittest
import sys
import os
import threading
import logging


def setup_test_environment():
    """Настройка окружения для подавления варнингов Streamlit."""
    os.environ["STREAMLIT_LOG_LEVEL"] = "error"
    logging.getLogger("streamlit").setLevel(logging.ERROR)
    logging.getLogger("streamlit.runtime.scriptrunner_utils.script_run_context").setLevel(logging.ERROR)

    try:
        from streamlit.runtime.scriptrunner import add_script_run_context
        for thread in threading.enumerate():
            add_script_run_context(thread)
    except ImportError:
        pass

    # Добавляем корень проекта в sys.path
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def run_suite():
    setup_test_environment()

    loader = unittest.TestLoader()
    # Указываем директорию с тестами относительно этого файла
    start_dir = os.path.dirname(__file__)

    suite = loader.discover(start_dir, pattern='test_*.py')

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if not result.wasSuccessful():
        sys.exit(1)


if __name__ == "__main__":
    run_suite()