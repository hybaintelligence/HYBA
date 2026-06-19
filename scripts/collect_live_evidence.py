"""Live ViaBTC evidence collection — connect, get job, measure throughput, save packet."""
import asyncio, json, os, sys, time, multiprocessing

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python_backend'))

from pythia_mining.pool_profiles import build_profile
from pythia_mining.live_stratum_session import LiveStratumSession
from pythia_mining.stratum_client import MiningJob
from pythia_mining.mining_validation import validate_share


def search_chunk(args):
    """Worker: SHA-256d search over a nonce range. Returns (nonce, block_hash) or None."""
    job_dict, extranonce2, nonce_start, nonce_end, time_limit = args
    job = MiningJob(**job_dict)
    t0 = time.monotonic()
    for nonce in range(nonce_start, nonce_end):
        if (nonce - nonce_start) % 50_000 == 0 and time.monotonic() - t0 > time_limit:
            return None
        try:
            r = validate_share(job, nonce, extranonce2)
            if r.valid:
                return (nonce, r.block_hash)
        except Exception:
            pass
    return None


async def main():
    profile = build_profile(
        'viabtc', name='ViaBTC BTC',
        url='stratum+tcp://btc.viabtc.io:3333',
        username='PYTHIA.001', password='Password123',
        stratum_version=1, tls_required=False,
    )

    session = LiveStratumSession(profile)
    print('Connecting to btc.viabtc.io:3333 ...')
    t_connect = time.time()
    await session.connect()
    handshake = await session.subscribe_and_authorize()
    connect_ms = round((time.time() - t_connect) * 1000, 1)

    print(f'Authorized: {handshake.authorized}  extranonce1={handshake.extranonce1}  connect_ms={connect_ms}')

    extranonce1      = handshake.extranonce1
    extranonce2_size = int(handshake.extranonce2_size)
    difficulty       = 16384.0
    current_job      = None

    for _ in range(40):
        try:
            event, payload = await session.read_event(timeout=2.0)
            if event == 'mining.set_difficulty':
                difficulty = float(payload.difficulty)
            elif event == 'mining.notify':
                target_limit = int('00000000ffff' + '0' * 52, 16)
                pool_target  = max(1, int(target_limit / difficulty))
                current_job  = MiningJob(
                    job_id=payload.job_id,
                    prevhash=payload.prevhash,
                    coinbase_parts=(payload.coinbase1, payload.coinbase2),
                    merkle_branch=payload.merkle_branch,
                    version=payload.version,
                    nbits=payload.nbits,
                    ntime=payload.ntime,
                    target=pool_target,
                    extranonce1=extranonce1,
                    extranonce2_size=extranonce2_size,
                )
                break
        except Exception:
            pass

    if not current_job:
        print(json.dumps({'error': 'no job received from pool'}))
        await session.close()
        return

    print(f'Job {current_job.job_id} | difficulty={difficulty} | prevhash={current_job.prevhash[:16]}...')

    ncpus        = min(multiprocessing.cpu_count(), 8)
    sprint_secs  = 60
    chunk_size   = 500_000
    extranonce2  = '00' * extranonce2_size

    job_dict = dict(
        job_id=current_job.job_id,
        prevhash=current_job.prevhash,
        coinbase_parts=current_job.coinbase_parts,
        merkle_branch=current_job.merkle_branch,
        version=current_job.version,
        nbits=current_job.nbits,
        ntime=current_job.ntime,
        target=current_job.target,
        extranonce1=extranonce1,
        extranonce2_size=extranonce2_size,
    )

    ranges = [
        (job_dict, extranonce2, i * chunk_size, (i + 1) * chunk_size, sprint_secs)
        for i in range(ncpus)
    ]

    print(f'Searching {ncpus} workers × {chunk_size:,} nonces ({sprint_secs}s limit) ...')
    t0 = time.time()

    with multiprocessing.Pool(processes=ncpus) as pool:
        results = pool.map(search_chunk, ranges)

    elapsed      = time.time() - t0
    total_nonces = ncpus * chunk_size
    hashrate     = total_nonces / elapsed
    found        = [r for r in results if r is not None]

    if found:
        nonce, block_hash = found[0]
        nonce_hex = nonce.to_bytes(4, byteorder='little').hex()
        submit = await session.submit_share(
            job_id=current_job.job_id,
            extranonce2=extranonce2,
            ntime=current_job.ntime,
            nonce=nonce_hex,
        )
        evidence = {
            'evidence_type': 'live_share_found_and_submitted',
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'pool': 'btc.viabtc.io:3333',
            'worker': 'PYTHIA.001',
            'authorized': handshake.authorized,
            'extranonce1': extranonce1,
            'job_id': current_job.job_id,
            'nonce': nonce,
            'nonce_hex': nonce_hex,
            'block_hash': block_hash,
            'difficulty': difficulty,
            'pool_accepted': submit.accepted,
            'pool_error': str(submit.error) if submit.error else None,
            'nonces_searched': total_nonces,
            'elapsed_seconds': round(elapsed, 3),
            'hashrate_hps': round(hashrate, 0),
            'workers': ncpus,
        }
    else:
        evidence = {
            'evidence_type': 'live_session_authenticated_job_received',
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'pool': 'btc.viabtc.io:3333',
            'worker': 'PYTHIA.001',
            'authorized': handshake.authorized,
            'extranonce1': extranonce1,
            'extranonce2_size': extranonce2_size,
            'job_id': current_job.job_id,
            'job_prevhash': current_job.prevhash,
            'job_nbits': current_job.nbits,
            'job_ntime': current_job.ntime,
            'job_merkle_branch_count': len(current_job.coinbase_parts),
            'difficulty': difficulty,
            'pool_target_hex': hex(current_job.target),
            'connect_ms': connect_ms,
            'nonces_searched': total_nonces,
            'elapsed_seconds': round(elapsed, 3),
            'hashrate_hps': round(hashrate, 0),
            'workers': ncpus,
            'share_found': False,
            'audit_note': (
                f'Authenticated + job received. Share requires ~{int(difficulty*2**32):,} '
                f'hashes on average. Python CPU at {round(hashrate/1e3,1)}kH/s — '
                f'ASIC required for practical share finding at this difficulty.'
            ),
        }

    print(json.dumps(evidence, indent=2))

    os.makedirs('artifacts/live_evidence', exist_ok=True)
    fname = f'artifacts/live_evidence/viabtc_session_{int(time.time())}.json'
    with open(fname, 'w') as f:
        json.dump(evidence, f, indent=2)
    print(f'\nEvidence packet saved: {fname}')

    await session.close()


if __name__ == '__main__':
    multiprocessing.set_start_method('fork', force=True)
    asyncio.run(main())
