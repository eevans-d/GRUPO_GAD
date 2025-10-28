# -*- coding: utf-8 -*-
"""
Tests para KeyboardFactory.
"""

import pytest
# Saltar estos tests si no está instalado python-telegram-bot
pytest.importorskip("telegram", reason="python-telegram-bot no instalado en este entorno de test")
from src.bot.utils.keyboards import KeyboardFactory


def test_main_menu_buttons():
    """Verifica que el menú principal tenga 5 botones."""
    keyboard = KeyboardFactory.main_menu()
    assert len(keyboard.inline_keyboard) == 5
    assert keyboard.inline_keyboard[0][0].text == "📋 Crear Tarea"
    assert keyboard.inline_keyboard[0][0].callback_data == "menu:crear:start"


def test_task_types_keyboard():
    """Verifica que el selector de tipos tenga 4 opciones."""
    keyboard = KeyboardFactory.task_types()
    assert len(keyboard.inline_keyboard) == 4
    assert keyboard.inline_keyboard[0][0].text == "🔧 OPERATIVO"
    assert keyboard.inline_keyboard[0][0].callback_data == "crear:tipo:OPERATIVO"


def test_confirmation_keyboard():
    """Verifica teclado de confirmación."""
    keyboard = KeyboardFactory.confirmation("finalizar", "T001")
    assert len(keyboard.inline_keyboard) == 1
    assert len(keyboard.inline_keyboard[0]) == 2
    assert "yes" in keyboard.inline_keyboard[0][0].callback_data
    assert "no" in keyboard.inline_keyboard[0][1].callback_data


def test_back_button():
    """Verifica botón de regreso."""
    keyboard = KeyboardFactory.back_button()
    assert len(keyboard.inline_keyboard) == 1
    assert keyboard.inline_keyboard[0][0].text == "🔙 Volver"
    assert keyboard.inline_keyboard[0][0].callback_data == "menu:main"


def test_paginated_list():
    """Verifica lista paginada."""
    items = [(f"Item {i}", f"id_{i}") for i in range(12)]
    
    # Primera página
    keyboard = KeyboardFactory.paginated_list(items, page=0, page_size=5)
    # Debe tener 5 items + navegación (solo siguiente) + volver = 7 filas
    assert len(keyboard.inline_keyboard) == 7
    assert keyboard.inline_keyboard[0][0].text == "Item 0"
    assert "➡️ Siguiente" in keyboard.inline_keyboard[5][0].text
    
    # Página intermedia
    keyboard = KeyboardFactory.paginated_list(items, page=1, page_size=5)
    # 5 items + navegación (anterior y siguiente) + volver = 7 filas
    assert len(keyboard.inline_keyboard) == 7
    assert "⬅️ Anterior" in keyboard.inline_keyboard[5][0].text
    assert "➡️ Siguiente" in keyboard.inline_keyboard[5][1].text
    
    # Última página
    keyboard = KeyboardFactory.paginated_list(items, page=2, page_size=5)
    # 2 items + navegación (solo anterior) + volver = 4 filas
    assert len(keyboard.inline_keyboard) == 4
    assert "⬅️ Anterior" in keyboard.inline_keyboard[2][0].text


def test_callback_data_length_limit():
    """Verifica que callback_data no exceda 64 bytes."""
    test_cases = [
        "menu:crear:start",
        "crear:tipo:OPERATIVO",
        "finalizar:confirm:T001:yes",
        "page:1"
    ]
    
    for callback_data in test_cases:
        assert len(callback_data.encode('utf-8')) <= 64, \
            f"Callback data '{callback_data}' excede límite de 64 bytes"


def test_all_main_menu_callbacks():
    """Verifica todos los callbacks del menú principal."""
    keyboard = KeyboardFactory.main_menu()
    expected_callbacks = [
        "menu:crear:start",
        "menu:finalizar:start",
        "menu:tareas:list:mis",
        "menu:tareas:search",
        "menu:ayuda:general"
    ]
    
    for i, expected in enumerate(expected_callbacks):
        assert keyboard.inline_keyboard[i][0].callback_data == expected
