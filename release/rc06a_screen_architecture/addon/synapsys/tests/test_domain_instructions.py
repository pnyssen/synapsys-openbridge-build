import hashlib, json
from odoo.exceptions import UserError, ValidationError
from odoo.modules.module import get_module_path
from odoo.tests.common import TransactionCase, tagged

WM_SHA = {  # bytes read back from Working Memory MESH_QUEUE/KIT/LANES, 20 Nov 2026
    'CORE_D000_D001_D002_PROFILE_v1.md': 'edb383d21526419735b55979961bc51f06b8bf470039b0910c47cb036b3bf07a',
    'D001_LANE_PROFILE_v1.md': '13bf255bb0c5839fd67ca263abc477caf964155fb2a191a029eb0698576b3478',
    'D003_LANE_PROFILE_v1.md': '7caa36e7b8b08fb2969b8a7f2aedc6af83146e70e3c7476fc874934f3803af7d',
    'D004_LANE_PROFILE_v1.md': '447386a0be4cee21aa1a9103fc47277048d13156d5bc828007f21e60bf7084a8',
    'D005_LANE_PROFILE_v1.md': 'eca7ce84d8ccc8ff07494347aa4b1da483ff42f15b92e1111d76adf1638a2b44',
    'D006_LANE_PROFILE_v1.md': '7d5d1172f1141de374def1fd393af495f87258b12cfe9e60f33886a72c6bdc69',
    'D007_LANE_PROFILE_v1.md': '0337d2e132d196de41826322a7212958ff0630150e57eb7690c7e154b6e6accb',
    'D008_LANE_PROFILE_v1.md': '02c2b54fb31ad1593e64087d0d9bd5d3600a313202b211c808e90d8714a2c987',
    'D009_LANE_PROFILE_v1.md': '0342da264ca800c7b7aa2f2daba182e4b6a6c756af14fe4beaf009a51f476118',
    'D009_LANE_PROFILE_v2.md': '873a8817b56970c0f1111f3c492eaf2360e0c158e5c302391002a4ee08bbb29e',
    'D010_LANE_PROFILE_v1.md': '604c2fcdde727309374163515c72ceb30ea04f6a47f10b7a92ca515bfeeb63b5',
    'D011_LANE_PROFILE_v1.md': '1897dce6e43ec6ddb4552c69c60d98d4f8a63d1e0ad13e39d7e4d28a066ddc79',
}


@tagged('post_install', '-at_install', 'synapsys')
class TestDomainInstructions(TransactionCase):

    def test_every_domain_has_its_seat_instructions_in_the_architecture(self):
        doms = self.env['synapsys.domain'].search([])
        self.assertEqual(len(doms), 12)
        for d in doms:
            self.assertTrue(d.seat_instruction_text, d.code)
            self.assertIn('Core profile', d.seat_instruction_text, d.code)
            self.assertEqual(d.seat_instruction_sha, hashlib.sha256(d.seat_instruction_text.encode()).hexdigest())
        by = {d.code: d for d in doms}
        for code in ('D000', 'D002'):
            self.assertFalse(by[code].instruction_id, code + ' reads the core profile only')
        for code in ('D001', 'D003', 'D004', 'D005', 'D006', 'D007', 'D008', 'D009', 'D010', 'D011'):
            self.assertEqual(by[code].instruction_id.domain_id, by[code], code)

    def test_text_held_here_equals_the_working_memory_mirror(self):
        rows = self.env['synapsys.canon'].search([('kind', '=', 'instruction')])
        self.assertEqual(len(rows), 12)
        for r in rows:
            f = r.mirror_path.split('/')[-1]
            self.assertEqual(r.sha256, WM_SHA[f], f)
            self.assertEqual(hashlib.sha256(r.body.encode('utf-8')).hexdigest(), WM_SHA[f], f)

    def test_d009_current_is_v2_and_v1_is_kept_superseded(self):
        d9 = self.env['synapsys.domain'].search([('code', '=', 'D009')])
        self.assertEqual(d9.instruction_id.version, 'v2')
        self.assertNotIn('a different provider from the Claude lanes', d9.seat_instruction_text)
        v1 = d9.instruction_id.replaces_id
        self.assertEqual((v1.version, v1.state), ('v1', 'superseded'))

    def test_text_cannot_be_edited_in_place_or_mismatched(self):
        r = self.env['synapsys.canon'].search([('kind', '=', 'instruction'), ('domain_id.code', '=', 'D003')])
        with self.assertRaises(UserError):
            r.write({'body': r.body + ' edited'})
        new = r.body + ' edited'
        with self.assertRaises(UserError):  # text and a matching hash together: only the immutability rule stops this
            r.write({'body': new, 'sha256': hashlib.sha256(new.encode('utf-8')).hexdigest()})
        with self.assertRaises(ValidationError):
            self.env['synapsys.canon'].create({'name': 'bad', 'kind': 'instruction', 'body': 'x', 'sha256': '0' * 64})
        r.write({'state': 'adopted'})  # state may move; text may not

    def test_loader_fails_closed_on_a_tampered_file(self):
        from odoo.addons.synapsys import hooks
        real = open
        def fake_open(path, mode='r', *a, **k):
            fh = real(path, mode, *a, **k)
            if 'D005_LANE_PROFILE_v1.md' in str(path) and 'b' in mode:
                data = fh.read() + b' tampered'; fh.close()
                import io; return io.BytesIO(data)
            return fh
        import builtins
        builtins.open, saved = fake_open, builtins.open
        try:
            with self.assertRaisesRegex(UserError, 'does not match its recorded sha256'):
                hooks.load_domain_instructions(self.env)
        finally:
            builtins.open = saved

    def test_registry_domains_match_architecture_domains(self):
        path = get_module_path('synapsys_mesh') + '/data/mesh_registry_v0_2.json'
        reg = json.load(open(path, encoding='utf-8'))
        labels = [e['label'] for e in reg['elements'] if e.get('cls') == 'D']
        names = self.env['synapsys.domain'].search([], order='code').mapped('name')
        self.assertEqual(labels, names, 'one domain list: registry and Architecture must not drift')
