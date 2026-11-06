"""Windows-style status-file sharing failures must not become USB disconnects."""
import json,unittest,time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import test_web_server as web_tests
from cps_bridge import Client

class StatusAccessTests(unittest.TestCase):
    setUp=web_tests.WebServerTests.setUp
    tearDown=web_tests.WebServerTests.tearDown
    request=web_tests.WebServerTests.request
    def ready(self):
        self.lab.process=SimpleNamespace(poll=lambda:None)
        state=dict(state='ready',session='same',received_hex='41',received_total=1,received_base=0,sent_total=0,queued_bytes=0)
        (self.lab.run/'usb_cdc.json').write_text(json.dumps(state));self.lab.cdc_last_status=state;self.lab.cdc_start_requested=True;self.lab.cdc_last_seen=time.monotonic()
    def test_locked_file_does_not_affect_memory_state(self):
        self.ready()
        try:
            with patch.object(Path,'read_text',side_effect=PermissionError(13,'sharing violation')):
                with self.request('/api/usb/cdc') as response:state=json.load(response)
            self.assertEqual(state['state'],'ready');self.assertEqual(state['session'],'same')
            self.assertEqual(state['status_source'],'worker_pipe_memory')
        finally:self.lab.process=None
    def test_client_ignores_locked_file_without_reconnecting(self):
        self.ready();client=Client(self.url);client.session='same';client.cursor=0
        read_text=Path.read_text;attempts=[]
        def locked_once(path,*args,**kwargs):
            if path.name=='usb_cdc.json' and not attempts:
                attempts.append(True);raise PermissionError(13,'sharing violation')
            return read_text(path,*args,**kwargs)
        try:
            with patch.object(Path,'read_text',locked_once),patch.object(self.lab,'command') as command:
                self.assertEqual(client.read(),b'A')
                self.assertEqual(client.read(),b'')
            command.assert_not_called();self.assertEqual(client.transient_status_reads,0);self.assertEqual(client.session,'same')
        finally:self.lab.process=None
    def test_missing_status_file_is_not_needed(self):
        self.ready();(self.lab.run/'usb_cdc.json').unlink()
        try:
            state=self.lab.cdc_status();self.assertEqual(state['state'],'ready');self.assertEqual(state['status_source'],'worker_pipe_memory')
        finally:self.lab.process=None
    def test_write_retries_a_locked_status_read_but_queues_command_only_once(self):
        self.ready();read_text=Path.read_text;attempts=[]
        def locked_once(path,*args,**kwargs):
            if path.name=='usb_cdc.json' and not attempts:
                attempts.append(True);raise PermissionError(13,'sharing violation')
            return read_text(path,*args,**kwargs)
        try:
            with patch.object(Path,'read_text',locked_once),patch.object(self.lab,'command',return_value=77) as command:
                with self.request('/api/usb/write',b'{"session":"same","hex":"02"}',self.lab.token) as response:
                    self.assertEqual(json.load(response)['sequence'],77)
            self.assertEqual(command.call_count,1)
        finally:self.lab.process=None
    def test_genuine_disconnect_remains_a_failure_with_a_reason(self):
        client=Client.__new__(Client);client.session='same';client.cursor=0
        client.get=lambda path:dict(state='disconnected',session='same',disconnect_reason='USB_CDC_STOP requested')
        with self.assertRaisesRegex(RuntimeError,'USB_CDC_STOP requested'):client.read()
    def test_locked_status_retry_is_bounded(self):
        client=Client.__new__(Client);client.get=lambda path:dict(state='unavailable',retryable=True,error='PermissionError')
        with patch('cps_bridge.time.monotonic',side_effect=[0,6]):
            with self.assertRaisesRegex(RuntimeError,'Suivi USB illisible'):client.cdc_status()

if __name__=='__main__':unittest.main()
