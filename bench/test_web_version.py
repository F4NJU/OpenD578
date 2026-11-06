"""Prevent an old in-memory server from being mistaken for the updated bench."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bench_version import APPLICATION, BUILD_FILES, build_id, server_matches
import web_launcher
from web_endpoint import record_endpoint


class WebVersionTests(unittest.TestCase):
    def test_old_server_in_same_directory_is_not_reused(self):
        config = dict(root_id='same-path', application='D578 local bench V11')
        self.assertFalse(server_matches(config, 'same-path', 'new-build'))

    def test_previous_v11_1_without_fingerprint_is_not_reused(self):
        config = dict(root_id='same-path', application=APPLICATION)
        self.assertFalse(server_matches(config, 'same-path', 'new-build'))

    def test_same_version_with_stale_code_is_not_reused(self):
        config = dict(root_id='same-path', application=APPLICATION, build_id='old-build')
        self.assertFalse(server_matches(config, 'same-path', 'new-build'))

    def test_only_matching_version_path_and_build_are_reused(self):
        config = dict(root_id='same-path', application=APPLICATION, build_id='new-build')
        self.assertTrue(server_matches(config, 'same-path', 'new-build'))
        self.assertFalse(server_matches(config, 'other-path', 'new-build'))

    def test_replacing_preparation_code_changes_fingerprint(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for name in BUILD_FILES:
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'first')
            old=build_id(root)
            (root/'prepare_inputs.py').write_bytes(b'updated')
            self.assertNotEqual(build_id(root),old)

    def test_occupied_old_port_starts_new_server_without_closing_old_one(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch.object(web_launcher,'ROOT',root), \
                 patch.object(web_launcher,'build_id',return_value='new-build'), \
                 patch.object(web_launcher,'reusable_server',return_value=False), \
                 patch.object(web_launcher.socket,'socket') as socket, \
                 patch.object(web_launcher.subprocess,'Popen') as start:
                socket.return_value.__enter__.return_value.bind.side_effect=OSError('occupied')
                web_launcher.main()
            command=start.call_args.args[0]
            self.assertEqual(command[command.index('--port')+1],'0')
            self.assertIn('--open-browser',command)
            self.assertEqual(Path(command[1]),root/'web_server.py')

    def test_matching_server_opens_browser_without_starting_another_process(self):
        with patch.object(web_launcher,'build_id',return_value='matching'), \
             patch.object(web_launcher,'read_endpoint',side_effect=ValueError('no remembered endpoint')), \
             patch.object(web_launcher,'reusable_server',return_value=True), \
             patch.object(web_launcher.webbrowser,'open') as open_browser, \
             patch.object(web_launcher.subprocess,'Popen') as start:
            web_launcher.main()
        start.assert_not_called()
        open_browser.assert_called_once_with('http://127.0.0.1:8765')

    def test_matching_server_on_remembered_random_port_is_reused(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);url='http://127.0.0.1:54321'
            record_endpoint(root,url,'matching')
            with patch.object(web_launcher,'ROOT',root), \
                 patch.object(web_launcher,'build_id',return_value='matching'), \
                 patch.object(web_launcher,'reusable_server',return_value=True), \
                 patch.object(web_launcher.webbrowser,'open') as open_browser, \
                 patch.object(web_launcher.subprocess,'Popen') as start:
                web_launcher.main()
            start.assert_not_called();open_browser.assert_called_once_with(url)


if __name__ == '__main__':
    unittest.main()
