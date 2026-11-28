"""Build navigator_integration_contract.json from the pinned ALL61 inputs. Deterministic: re-running yields identical bytes."""
import hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_matrix as M, navigator_contract as N

def main(out=os.path.join(HERE, 'navigator_integration_contract.json')):
    fx = lambda n: os.path.join(HERE, 'fixtures', n)
    base, snap = json.load(open(fx('baseline.json'))), json.load(open(fx('live_snapshot.json')))
    rows = M.build(base, snap)
    pins = {'baseline_sha256': hashlib.sha256(open(fx('baseline.json'), 'rb').read()).hexdigest(),
            'live_snapshot_sha256': hashlib.sha256(open(fx('live_snapshot.json'), 'rb').read()).hexdigest(),
            'source_checkpoint_commit': '7873234a3e45989f16b59b6b8d3836aec417299a'}
    c = N.build_contract(rows, snap, pins['baseline_sha256'], pins)
    open(out, 'w').write(json.dumps(c, indent=1, sort_keys=True) + '\n')
    return c

if __name__ == '__main__':
    c = main(); print(c['counts'], c['contract_sha256_over_menus'])
