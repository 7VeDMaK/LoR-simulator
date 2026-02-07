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

    # Определяем корень проекта (на уровень выше папки tests)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    return project_root


def run_suite():
    project_root = setup_test_environment()

    loader = unittest.TestLoader()
    # Папка, в которой ищем тесты
    start_dir = os.path.join(project_root, 'tests')

    # Чтобы unittest заходил в подпапки, start_dir должен быть импортируемым.
    # Мы указываем top_level_dir как корень проекта.
    suite = loader.discover(
        start_dir=start_dir,
        pattern='test_*.py',
        top_level_dir=project_root
    )

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if not result.wasSuccessful():
        sys.exit(1)


if __name__ == "__main__":
    run_suite()