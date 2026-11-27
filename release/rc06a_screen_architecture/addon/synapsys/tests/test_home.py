from odoo.tests.common import HttpCase, tagged


@tagged('post_install', '-at_install', 'synapsys')
class TestHome(HttpCase):
    """The SynapSys Home page renders the real architecture in plain words."""

    def test_home_shows_strategies_domains_and_purposes(self):
        self.authenticate('admin', 'admin')
        html = self.make_jsonrpc_request('/synapsys/home/data', {})
        for text in ('nine strategies', 'Balanced Life', 'Stewardship', 'twelve domains', 'Value Chains',
                     'Keeps every value chain complete', 'Rulebook in place', 'K-12'):
            self.assertIn(text, html)
        self.assertNotIn('No rulebook yet', html)
        self.assertEqual(html.count('class="ss-dom"'), 12)
