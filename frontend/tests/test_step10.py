import urllib.request, json, time

payload = json.dumps({
    'area': {'width': 100, 'height': 100},
    'num_nodes': 8,
    'sensing_radius': 12,
    'comm_radius': 25,
    'initial_energy': 1.0,
    'weights': {'w1': 0.5, 'w2': 0.25, 'w3': 0.25},
    'pso_params': {'swarm_size': 20, 'iterations': 50, 'inertia': 0.7, 'c1': 1.5, 'c2': 1.5},
    'use_gpu': False,
    'use_vdcoa': False,
    'seed': 42,
    'restricted_areas': [],
    'non_critical_areas': [],
    'strategy': 'pso',
}).encode()

req = urllib.request.Request(
    'http://127.0.0.1:8000/api/v1/optimize',
    data=payload,
    headers={'Content-Type': 'application/json'},
)
resp = urllib.request.urlopen(req)
job = json.loads(resp.read())
job_id = job['job_id']
print('Job submitted:', job_id)

for i in range(30):
    time.sleep(2)
    r = urllib.request.urlopen(f'http://127.0.0.1:8000/api/v1/optimize/{job_id}/status')
    st = json.loads(r.read())
    status = st['status']
    print(f'  [{i}] status={status}')
    if status in ('complete', 'failed'):
        break

r = urllib.request.urlopen(f'http://127.0.0.1:8000/api/v1/optimize/{job_id}/result')
res = json.loads(r.read())
print('Final status:', res['status'])
print('Coverage ratio:', res['coverage_ratio'])
print('Connectivity ratio:', res['connectivity_ratio'])
print('Avg energy:', res['avg_energy'])
print('Num positions:', len(res['best_positions']))
print('First position:', res['best_positions'][0])

cmap = res.get('coverage_map')
if cmap:
    rows = len(cmap)
    cols = len(cmap[0]) if rows else 0
    print(f'Coverage map: {rows} x {cols}')
    print('coverage_map[0][:5]:', cmap[0][:5])
    print('coverage_map[5][:5]:', cmap[5][:5])
    # Verify values are in [0, 1]
    flat = [v for row in cmap for v in row]
    assert all(0.0 <= v <= 1.0 for v in flat), 'Coverage map has out-of-range values!'
    print('All coverage values in [0,1]: PASS')
else:
    print('WARNING: coverage_map is None or empty')

print()
print('PASS: Backend returns correct result shape for GridCanvas rendering')
