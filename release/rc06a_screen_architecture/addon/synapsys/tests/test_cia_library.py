import hashlib, io, zipfile
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'


def docx(paragraphs):
    body = ''.join('<w:p><w:r><w:t>%s</w:t></w:r></w:p>' % p for p in paragraphs)
    xml = '<?xml version="1.0"?><w:document xmlns:w="%s"><w:body>%s</w:body></w:document>' % (W, body)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr('[Content_Types].xml', '<Types/>')
        z.writestr('word/document.xml', xml)
    return buf.getvalue()


@tagged('post_install', '-at_install', 'synapsys')
class TestCiaLibrary(TransactionCase):

    def test_charter_text_held_bound_to_domain_and_source_hash(self):
        data = docx(['D004 — Value Chains Domain Charter v1.1', 'Purpose: keep every value chain complete.'])
        Canon = self.env['synapsys.canon']
        rec = Canon.hold_charter_extract('D004', 'D004 — Value Chains Domain Charter v1.1', 'v1.1', data,
                                         hashlib.sha256(data).hexdigest())
        self.assertEqual((rec.kind, rec.domain_id.code), ('charter', 'D004'))
        self.assertIn('keep every value chain complete', rec.body)
        self.assertEqual(rec.source_sha256, hashlib.sha256(data).hexdigest())
        self.assertEqual(rec.sha256, hashlib.sha256(rec.body.encode()).hexdigest())
        d4 = self.env['synapsys.domain'].search([('code', '=', 'D004')])
        self.assertIn(rec, d4.canon_ids)

    def test_charter_refused_when_source_bytes_do_not_match_the_library_hash(self):
        data = docx(['x'])
        n = self.env['synapsys.canon'].search_count([])
        with self.assertRaisesRegex(UserError, 'Nothing held'):
            self.env['synapsys.canon'].hold_charter_extract('D004', 'D004 charter', 'v1', data, '0' * 64)
        self.assertEqual(self.env['synapsys.canon'].search_count([]), n)

    def test_v19_charter_rows_link_to_their_domains_by_code(self):
        Canon = self.env['synapsys.canon']
        rows = Canon.create([{'name': 'D006 — Client Portfolios Domain Charter v1.2', 'tier': 'tier_2_governance'},
                             {'name': 'D010 — H’AION Domain Charter v1.2', 'tier': 'tier_2_governance'},
                             {'name': 'SynapSys Enterprise Constitution v3.05', 'tier': 'tier_1_canonical_core'},
                             {'name': 'D002-OCRA method note', 'tier': 'candidate'}])
        linked = rows.link_charters_to_domains()
        self.assertEqual(sorted(linked.mapped('domain_id.code')), ['D006', 'D010'])
        self.assertFalse(rows[2].domain_id)
        self.assertFalse(rows[3].domain_id, 'a method note named D002-… is not a charter')

    def test_intelligence_and_adaptability_have_their_home_beside_canon(self):
        d8 = self.env['synapsys.domain'].search([('code', '=', 'D008')])
        i = self.env['synapsys.intelligence'].create({'name': 'Network node (synthetic)', 'domain_id': d8.id,
                                                      'personal_data': True})
        l = self.env['synapsys.learning'].create({'name': 'Gate held on missing seat records', 'domain_id': d8.id,
                                                  'observation': 'no producer', 'implication': 'seat runner'})
        self.assertIn(i, d8.intelligence_ids)
        self.assertIn(l, d8.learning_ids)

    def test_registry_domain_elements_point_at_the_architecture_domains(self):
        reg = self.env['synapsys.mesh.registry'].search([], limit=1)
        doms = reg.entry_ids.filtered(lambda e: e.cls == 'D')
        self.assertEqual(len(doms), 12)
        self.assertEqual(set(doms.mapped('domain_id.code')), {'D%03d' % i for i in range(12)})
