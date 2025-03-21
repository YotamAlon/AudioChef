import pytest
import pytest_asyncio
from kivy.core.window import Window
from kivy.tests.common import async_run

from audio_chef.app import AppState

from kivy.tests import UnitKivyApp


def app():
    from audio_chef.main import AudioChefApp

    class TestApp(UnitKivyApp, AudioChefApp):
        pass

    return TestApp()


@pytest.mark.asyncio
@pytest.mark.parametrize("kivy_app", [[app], ], indirect=True)
async def test_add_file(kivy_app):
    async for app in kivy_app: break
    dummy_file = "dummy_file.mp3"

    # Act
    Window.dispatch("on_drop_file", dummy_file.encode(), 0.0, 0.0)

    # Assert
    assert AppState.selected_files[0].filename == dummy_file
