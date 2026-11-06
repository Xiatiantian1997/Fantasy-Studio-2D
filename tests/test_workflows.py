import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from workflows import build_workflow
from server import upload_reference


BASE = {
    'checkpoint': 'animagine-xl-4.0-opt.safetensors',
    'prompt': 'portrait of an adult woman',
    'negative': 'blur',
    'size': 'portrait',
    'steps': 28,
    'cfg': 6,
    'seed': 42,
}


class WorkflowTests(unittest.TestCase):
    def test_txt2img(self):
        w = build_workflow(BASE)
        self.assertEqual(w['4']['class_type'], 'EmptyLatentImage')
        self.assertEqual(w['5']['inputs']['denoise'], 1.0)
        self.assertEqual(w['5']['inputs']['latent_image'], ['4', 0])
        self.assertEqual(w['4']['inputs']['width'], 768)

    def test_img2img(self):
        w = build_workflow(dict(BASE, mode='img2img', strength=.45, upload_name='studio_abcdef.png'))
        self.assertEqual(w['4']['class_type'], 'LoadImage')
        self.assertEqual(w['8']['class_type'], 'ImageScale')
        self.assertEqual(w['9']['class_type'], 'VAEEncode')
        self.assertEqual(w['5']['inputs']['denoise'], .45)
        self.assertEqual(w['5']['inputs']['latent_image'], ['9', 0])

    def test_lora(self):
        w = build_workflow(dict(BASE, lora='my-lora.safetensors'))
        self.assertEqual(w['2']['inputs']['clip'], ['10', 1])
        self.assertEqual(w['5']['inputs']['model'], ['10', 0])
        self.assertEqual(w['10']['inputs']['strength_model'], .75)

    def test_bad_input(self):
        for bad in (dict(BASE, steps=200), dict(BASE, checkpoint=''),
                    dict(BASE, prompt=''), dict(BASE, mode='other'),
                    dict(BASE, mode='img2img')):
            with self.assertRaises(ValueError):
                build_workflow(bad)

    def test_invalid_image(self):
        with self.assertRaises(ValueError):
            upload_reference('data:image/png;base64,dGVzdA==')


if __name__ == '__main__':
    unittest.main()
