import hashlib,json,tempfile,unittest
from pathlib import Path
import numpy as np
from audio_iq import Config,run_loop,replay_iq,receive,pcm_wav,read_wav,fm_demodulate
from ax25_afsk import fcs,ui_frame,afsk,decode

class AudioIQTests(unittest.TestCase):
    def test_known_crc_and_bad_frame(self):
        self.assertEqual(fcs(b'123456789'),0x906e)
        frame=ui_frame();self.assertTrue(decode(afsk(frame)))
        damaged=frame[:-1]+bytes([frame[-1]^1]);self.assertEqual(decode(afsk(damaged)),[])
    def test_fm_recording_and_gain(self):
        with tempfile.TemporaryDirectory() as root:
            t=np.arange(48000)/48000;signal=.15*np.sin(2*np.pi*1000*t)
            report=run_loop(root,signal);folder=Path(root)/report['session']
            iq=replay_iq(folder/'rx.sigmf-data');audio=receive(iq,Config())
            self.assertGreater(np.corrcoef(audio[4800:-4800],signal[4800:-4800])[0,1],.995)
            inverse=receive(np.conj(iq),Config());self.assertLess(np.corrcoef(audio[4800:-4800],inverse[4800:-4800])[0,1],-.995)
            self.assertAlmostEqual(np.std(receive(iq,Config(speaker_gain_db=-6)))/np.std(audio),10**(-6/20),places=5)
            self.assertEqual((folder/'tx.sigmf-data').stat().st_size,192000*8)
            self.assertEqual(hashlib.sha256((folder/'rx.sigmf-data').read_bytes()).hexdigest(),report['RX_IQ_SHA256'])
            self.assertEqual(json.loads((folder/'tx.sigmf-meta').read_text())['global']['core:datatype'],'cf32_le')
    def test_phase_discriminator_known_carrier(self):
        carrier=np.exp(2j*np.pi*1234*np.arange(10000)/192000)
        self.assertTrue(np.allclose(fm_demodulate(carrier,192000,2500)[1:],1234/2500))
    def test_aprs_from_recorded_iq(self):
        with tempfile.TemporaryDirectory() as root:
            report=run_loop(root,mode='aprs',source='F4EGM',information='>IQ roundtrip 578')
            self.assertEqual(report['APRS_frames'][0]['information'],'>IQ roundtrip 578')
            self.assertEqual(report['APRS_frames'][0]['source'],'F4EGM')
            self.assertTrue(report['APRS_frames'][0]['FCS_valid'])
            self.assertFalse(report['SCT_firmware_executed'])
    def test_wav_and_limits(self):
        audio,rate=read_wav(pcm_wav([.1,-.1],48000));self.assertEqual(rate,48000);self.assertEqual(len(audio),2)
        with self.assertRaises(ValueError):Config(deviation_hz=float('nan')).validate()
        with self.assertRaises(ValueError):run_loop('/unused',mode='dmr')
    def test_http_audio_and_traversal(self):
        import threading,urllib.request,urllib.error
        from http.server import ThreadingHTTPServer
        from web_server import Laboratory,Handler
        with tempfile.TemporaryDirectory() as root:
            server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
            server.lab=Laboratory(Path(root),Path(root),Path(root));server.origin=f'http://127.0.0.1:{server.server_port}'
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                req=urllib.request.Request(server.origin+'/api/audio/loop',data=json.dumps(dict(mode='aprs')).encode(),headers={'X-Lab-Token':server.lab.token})
                with urllib.request.urlopen(req) as response:report=json.load(response)
                self.assertTrue(report['APRS_frames'][0]['FCS_valid'])
                with urllib.request.urlopen(server.origin+'/api/audio/'+report['session']+'/received.wav') as response:self.assertEqual(response.read(4),b'RIFF')
                with self.assertRaises(urllib.error.HTTPError):urllib.request.urlopen(server.origin+'/api/audio/'+report['session']+'/input.wav')
                bad=urllib.request.Request(server.origin+'/api/audio/loop',data=b'{"mode":"fm","wav_base64":""}',headers={'X-Lab-Token':server.lab.token})
                with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(bad)
                self.assertEqual(error.exception.code,400)
            finally:server.shutdown();server.server_close();thread.join()

if __name__=='__main__':unittest.main()
