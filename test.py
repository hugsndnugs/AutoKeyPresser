import unittest
from unittest.mock import patch, MagicMock
import time

# Assuming you have a class or function called 'AutoKeyPresser' with a method '_press_key_loop'
from autokeypresser import AutoKeyPresser  # Update this import based on actual structure

class TestAutoKeyPresser(unittest.TestCase):
    def setUp(self):
        self.key = 'a'
        self.interval = 0.1
        self.presser = AutoKeyPresser(self.key, self.interval)

    @patch('autokeypresser.keyboard.press_and_release')
    def test_press_key_once(self, mock_press):
        self.presser.running = True
        self.presser._press_key_loop(press_once=True)
        mock_press.assert_called_once_with(self.key)

    @patch('autokeypresser.keyboard.press_and_release')
    def test_press_key_multiple(self, mock_press):
        self.presser.running = True

        def stop_after_delay():
            time.sleep(0.3)
            self.presser.running = False

        from threading import Thread
        Thread(target=stop_after_delay).start()
        self.presser._press_key_loop()

        self.assertGreaterEqual(mock_press.call_count, 2)

if __name__ == '__main__':
    unittest.main()
