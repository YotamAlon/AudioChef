from utils.State import state


class TestState:
    def test_get_set_prop(self):
        state.set_prop('test_key', 'test_value')
        assert state.get_prop('test_key') == 'test_value'
