import io,json,tempfile,threading,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from cdc_channel import encode,decode
from usb_cdc_runtime import publish
from usb_cdc import CdcHost
from usbd_host import UsbdHost
from web_server import Laboratory

class CdcChannelTests(unittest.TestCase):
    def state(self,data=b'ABC',total=None):
        return dict(state='ready',session='s',received_base=0,received_total=len(data) if total is None else total,received_hex=data.hex(),sent_total=0)
    def test_frames_preserve_full_bounded_history_and_detect_missing_bytes(self):
        data=bytes(range(256))*256;state=self.state(data);state['recent_events']=['not needed in stream']
        self.assertEqual(decode(encode(state))['received_hex'],data.hex());self.assertNotIn('recent_events',decode(encode(state)))
        with self.assertRaisesRegex(ValueError,'length mismatch'):decode(encode(self.state(b'ABC',4)))
        self.assertIsNone(decode('ordinary log line\n'))
    def test_old_worker_cannot_replace_new_session_state(self):
        with tempfile.TemporaryDirectory() as root:
            lab=Laboratory(Path(root),Path(root),Path(root));process=object();lab.process=process
            log=io.StringIO();lab.accept_worker_line(process,lab.engine_instance,encode(self.state()),log)
            self.assertEqual(lab.cdc_last_status['session'],'s')
            new=object();lab.process=new
            lab.accept_worker_line(process,lab.engine_instance,encode(dict(self.state(),session='old')),log)
            self.assertEqual(lab.cdc_last_status['session'],'s')
            lab.accept_worker_line(new,lab.engine_instance,'normal log\n',log);self.assertEqual(log.getvalue(),'normal log\n')
            lab.process=None
    def test_active_pipe_publication_never_opens_a_status_file(self):
        messages=[];cdc=CdcHost(UsbdHost());r=SimpleNamespace(cdc=cdc,cdc_sink=messages.append,live_directory=Path('/unused'))
        with patch.object(Path,'write_text',side_effect=PermissionError('locked')) as writer:
            publish(r,force=True);publish(r,force=True)
        writer.assert_not_called();self.assertEqual(len(messages),2)
    def test_parallel_readers_get_consistent_memory_snapshots(self):
        with tempfile.TemporaryDirectory() as root:
            lab=Laboratory(Path(root),Path(root),Path(root));process=SimpleNamespace(poll=lambda:None);lab.process=process;errors=[]
            def writer():
                for n in range(1,501):lab.accept_worker_line(process,lab.engine_instance,encode(self.state(bytes([n%256])*n)),io.StringIO())
            def reader():
                for _ in range(500):
                    value=lab.cdc_status()
                    if value['state']=='ready' and len(bytes.fromhex(value['received_hex']))!=value['received_total']:errors.append('torn state')
            workers=[threading.Thread(target=writer),threading.Thread(target=reader),threading.Thread(target=reader)]
            for worker in workers:worker.start()
            for worker in workers:worker.join()
            self.assertEqual(errors,[]);self.assertEqual(lab.cdc_last_status['received_total'],500);lab.process=None

if __name__=='__main__':unittest.main()
