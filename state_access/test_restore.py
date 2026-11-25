"""CPU contracts for restricted loading, record mapping and real CLIP topology."""
import copy
import os
import pickle
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
import torch
import restore as r


class RestoreTests(unittest.TestCase):
    def test_manifest_keeps_logical_aliases(self):
        rows = r.manifest_rows()
        self.assertEqual(len(rows), 396)
        self.assertEqual(len({x['unit'] for x in rows if x['family'] != 'methods_fixed24'}), 42)
        self.assertEqual(len({x['unit'] for x in rows if x['family'] == 'methods_fixed24'}), 24)
        a = r.select(rows, 'scientific_core', 'cifar100__lora_both__s42', 'frozen_baseline')
        b = r.select(rows, 'scientific_core', 'cifar100__lora_both__s42', 'epoch_000')
        self.assertEqual(r.payload_record(a), r.payload_record(b))
        self.assertNotEqual(a['state'], b['state'])
        self.assertEqual(r.resolve_payload(a, r.HERE), r.resolve_payload(b, r.HERE))

    def test_transport_index_cannot_escape_root(self):
        for name in ('../x', '/x', 'C:/x', 'a\\x'):
            with self.assertRaises(ValueError):
                r.inside(r.HERE, name)
        with tempfile.TemporaryDirectory() as folder:
            row = r.manifest_rows()[0]
            index = Path(folder) / 'index.json'
            index.write_text(r.json.dumps({r.payload_record(row)['sha256']: 'states/one.pt'}))
            self.assertEqual(r.resolve_payload(row, folder, index), Path(folder) / 'states/one.pt')

    def test_state_index_alias_uses_hash_object_and_rejects_wrong_binding(self):
        row = r.manifest_rows()[0]
        record = r.payload_record(row)
        entry = dict(member=row['local_logical_member'], family=row['family'], alias=True,
                     object=None, **record)
        materialized = dict(member='another/logical/role', family=row['family'], alias=False,
                            object='states/' + record['sha256'] + '.pt', **record)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'StateIndex.json'
            def write(entries):
                path.write_text(r.json.dumps({'logical_state_records': entries}))
            write([entry, materialized])
            self.assertEqual(r.resolve_payload(row, folder, path),
                             Path(folder) / materialized['object'])
            for entries in ([entry], [entry, entry, materialized],
                            [dict(entry, bytes=1), materialized],
                            [entry, dict(materialized, object='../outside.pt')]):
                write(entries)
                with self.assertRaises(ValueError):
                    r.resolve_payload(row, folder, path)

    def save_load(self, state, mutation=None):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'test.pt'
            torch.save(state, path)
            expected = {'sha256': r.sha(path), 'bytes': path.stat().st_size}
            if mutation:
                mutation(expected)
            return r.safe_load(path, expected)

    def test_numpy_rng_restricted_roundtrip(self):
        original = np.random.get_state()
        value, count = self.save_load({'rng': {'numpy': original}})
        self.assertEqual(count, 1)
        np.testing.assert_array_equal(original[1], value['rng']['numpy'][1])
        self.assertFalse(torch.cuda.is_initialized())

    def test_numpy_elsewhere_or_wrong_shape_is_rejected(self):
        for state in ({'caption': np.zeros(624, np.uint32)},
                      {'rng': np.zeros(623, np.uint32)}, {'rng': np.zeros(624, np.float64)}):
            with self.assertRaises((ValueError, pickle.UnpicklingError)):
                self.save_load(state)

    def test_hash_size_and_unapproved_global_reject_before_load(self):
        with patch.object(torch, 'load', side_effect=AssertionError('Must reject first')):
            for mutation in (lambda d: d.update(sha256='0' * 64), lambda d: d.update(bytes=1)):
                with self.assertRaisesRegex(ValueError, 'size/SHA'):
                    self.save_load({'x': torch.ones(2)}, mutation)
            with self.assertRaisesRegex(ValueError, 'Unexpected pickle global'):
                self.save_load({'function': os.system})

    def test_caller_allowlist_is_not_inherited(self):
        before = torch.serialization.get_safe_globals()
        with torch.serialization.safe_globals([os.system]):
            with self.assertRaisesRegex(ValueError, 'Unexpected pickle global'):
                self.save_load({'function': os.system})
        self.assertEqual(torch.serialization.get_safe_globals(), before)

    def test_no_partial_copy_on_invalid_last_tensor(self):
        model = torch.nn.Linear(2, 3)
        old = copy.deepcopy(model.state_dict())
        saved = {k: torch.ones_like(v) for k, v in model.named_parameters()}
        saved['bias'] = torch.ones(4)
        with self.assertRaises(ValueError):
            r.copy_trainables(model, saved)
        for k, value in old.items():
            self.assertTrue(torch.equal(model.state_dict()[k], value))
        saved['bias'] = torch.ones(3)
        r.copy_trainables(model, saved)
        self.assertTrue(all(torch.equal(p, saved[k]) for k, p in model.named_parameters()))

    def test_method_actual_copy_and_fixed_buffer_checks(self):
        from transformers import CLIPConfig, CLIPTextConfig, CLIPVisionConfig, CLIPModel
        _, method = r.modules()
        t = CLIPTextConfig(vocab_size=24, hidden_size=64, intermediate_size=80,
            num_hidden_layers=12, num_attention_heads=1, max_position_embeddings=8,
            bos_token_id=1, eos_token_id=2, pad_token_id=0)
        v = CLIPVisionConfig(hidden_size=64, intermediate_size=80,
            num_hidden_layers=12, num_attention_heads=1, image_size=14, patch_size=2)
        config = CLIPConfig(text_config=t.to_dict(), vision_config=v.to_dict(), projection_dim=512)
        for arm in method.ARMS:
            model = method.MethodCLIP(CLIPModel(config), arm)
            opt, sched = method.optimizers(model, 1, weight_decay=.01, betas=(.9, .999), eps=1e-8)
            state = method.capture(model, opt, sched, {}, epoch=0, step=0, cursor=0, order=[])
            for key in state['trainable']:
                state['trainable'][key].fill_(.25)
            method._validate_state(state, model, {})
            r.copy_trainables(model, state['trainable'])
            bad = copy.deepcopy(state)
            bad['buffers'][next(iter(bad['buffers']))].fill_(999)
            with self.assertRaises(ValueError):
                method._validate_state(bad, model, {})


if __name__ == '__main__':
    torch.set_num_threads(2)
    unittest.main(verbosity=2)
