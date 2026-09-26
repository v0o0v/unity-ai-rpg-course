import hashlib
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from pack_frames import pack_frames

class PackFramesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.src = self.root / 'in'; self.src.mkdir()
        self.out = self.root / 'out' / 'sheet.png'
    def tearDown(self): self.temp.cleanup()
    def image(self, name='frame1.png', size=(64,64), fill=(90,80,70,180)):
        p=self.src/name; Image.new('RGBA',size,fill).save(p); return p
    def test_pack_order_alpha_pivot_and_source_preservation(self):
        for n in [10,2,1]: self.image(f'frame{n}.png', fill=(n,20,30,128))
        before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in self.src.iterdir()}
        meta=pack_frames(self.src,self.out,columns=2)
        self.assertEqual([f['source'] for f in meta['frames']],['frame1.png','frame2.png','frame10.png'])
        self.assertEqual(meta['frames'][2]['rectTopLeft']['y'],64)
        self.assertEqual(meta['frames'][0]['pivotNormalizedBottomLeft']['y'],.125)
        with Image.open(self.out) as img:
            self.assertEqual(img.size,(128,128)); self.assertEqual(img.getpixel((0,0)),(1,20,30,128))
        self.assertEqual(before,{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in self.src.iterdir()})
    def test_bad_size_does_not_write(self):
        self.image(size=(32,64))
        with self.assertRaises(ValueError):pack_frames(self.src,self.out)
        self.assertFalse(self.out.exists())
    def test_existing_output_protected(self):
        self.image();pack_frames(self.src,self.out)
        with self.assertRaises(ValueError):pack_frames(self.src,self.out)
        pack_frames(self.src,self.out,force=True)
    def test_blank_frame_explicit_opt_in(self):
        self.image(fill=(0,0,0,0))
        with self.assertRaises(ValueError):pack_frames(self.src,self.out)
        self.assertEqual(pack_frames(self.src,self.out,allow_empty=True)['frameCount'],1)
    def test_bad_pivot(self):
        self.image()
        with self.assertRaises(ValueError):pack_frames(self.src,self.out,pivot=(2,.1))
    def test_output_cannot_pollute_input(self):
        self.image()
        with self.assertRaises(ValueError):pack_frames(self.src,self.src/'sheet.png')
    def test_no_frames(self):
        with self.assertRaises(ValueError):pack_frames(self.src,self.out)
    def test_duplicate_warning(self):
        self.image('frame1.png'); self.image('frame2.png')
        self.assertTrue(any('same pixels' in w for w in pack_frames(self.src,self.out)['warnings']))

if __name__=='__main__':unittest.main(verbosity=2)
