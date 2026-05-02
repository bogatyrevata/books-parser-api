# conftest.py (в корне проекта, рядом с database.py)
import sys
import os

# Добавляем корень проекта в путь поиска модулей
sys.path.insert(0, os.path.dirname(__file__))

