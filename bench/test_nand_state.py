import tempfile,unittest
from pathlib import Path
from hardware_runner import BlankNand
from nand_state import save,load

class NandCheckpointTests(unittest.TestCase):
    def test_checkpoint_reloads_pages_without_changing_backing_image(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'nand.dat';a=BlankNand();a.overlay={9:b'A'*2112,72:bytes(range(256))*8+bytes(64)}
            save(a,path);b=BlankNand();load(b,path)
            self.assertEqual(b.page_image(9),b'A'*2112);self.assertEqual(b.page_image(72),a.overlay[72])
            self.assertEqual(b.images['nand_main_256MiB.bin'][9*2048],255)
            self.assertIsNone(b.cached_page)
    def test_corruption_and_wrong_capture_are_rejected_before_applying_pages(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'nand.dat';a=BlankNand();a.overlay={9:b'A'*2112};save(a,path)
            b=BlankNand();b.sources={'other':'image'}
            with self.assertRaisesRegex(ValueError,'different backing'):load(b,path)
            self.assertEqual(b.overlay,{})
            b=BlankNand();data=bytearray(path.read_bytes());data[-1]^=1;path.write_bytes(data)
            with self.assertRaisesRegex(ValueError,'checksum'):load(b,path)
            self.assertEqual(b.overlay,{})

if __name__=='__main__':unittest.main()
