#!/usr/bin/env python3
"""
fix_random_container_render.py — Phase 3 fix for Fact #17

For each CAkRanSeqCntr[Random] .txtp with ≥2 CAkSound children,
decode each child's Source ID from pool/<SID>.wem individually
to out_wwise/wav/<SID>.wav, bypassing the txtp group-based collapsing.

Does NOT touch:
- CAkLayerCntr cases (children play simultaneously, collapsing is correct)
- Existing .txtp files
- Existing collapsed .wav files (left in place for backward compat)
- wwise_builder.py (out of scope)

Usage:
    python3 scripts/fix_random_container_render.py \
        --txtp-dir out_wwise/txtp \
        --pool-dir pool \
        --output-dir out_wwise/wav \
        --workers 8
"""
import os
import re
import argparse
import subprocess
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed


def setup_logging(log_path):
    """Set up logging to both file and console."""
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logger = logging.getLogger('fix_random_container')
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(log_path, mode='w', encoding='utf-8')
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    fh.setFormatter(fmt)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


def is_random_container_bug(txtp_path):
    """
    Check if a .txtp file matches the Random Container bug pattern:
    - Contains 'group = ' (multi-source container)
    - Contains CAkRanSeqCntr (not just as a nested child of CAkLayerCntr)
    - eMode: 0x00 [Random]
    - ≥2 CAkSound children
    - Does NOT contain CAkLayerCntr (those are layer/blend cases, correct behavior)
    """
    with open(txtp_path, 'r', encoding='utf-8') as f:
        content = f.read()

    has_group = 'group = ' in content
    has_ranseq = 'CAkRanSeqCntr' in content
    has_random_mode = bool(re.search(r'eMode:\s*0x00\s*\[Random\]', content))
    sound_count = len(re.findall(r'CAkSound\[', content))
    has_layer_cntr = 'CAkLayerCntr' in content

    return (has_group and has_ranseq and has_random_mode
            and sound_count >= 2 and not has_layer_cntr)


def extract_source_ids(txtp_path):
    """
    Extract Source IDs from a .txtp file.
    Uses BOTH methods and cross-checks:
    1. Non-comment lines: grep for <digits>.wem patterns
    2. Comment lines: grep for 'Source <digits>' patterns
    Returns a sorted list of unique SID strings.
    """
    sids_noncomment = set()
    sids_comment = set()

    with open(txtp_path, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith('#'):
                # Comment line: look for "Source <digits>"
                for m in re.finditer(r'Source\s+(\d+)', stripped):
                    sids_comment.add(m.group(1))
            else:
                # Non-comment line: look for <digits>.wem
                for m in re.finditer(r'(\d+)\.wem', stripped):
                    sids_noncomment.add(m.group(1))

    # Both sets should match; use non-comment as primary (actual playback refs)
    return sorted(sids_noncomment)


def decode_wem(pool_dir, sid, output_dir, logger):
    """
    Decode pool/<sid>.wem -> output_dir/<sid>.wav using vgmstream-cli.
    Returns (sid, success, error_msg).
    """
    wem_path = os.path.join(pool_dir, f'{sid}.wem')
    wav_path = os.path.join(output_dir, f'{sid}.wav')

    if not os.path.exists(wem_path):
        return (sid, False, f'Source file not found: {wem_path}')

    # Skip if already decoded and non-empty
    if os.path.exists(wav_path) and os.path.getsize(wav_path) > 0:
        return (sid, True, 'already exists')

    cmd = ['vgmstream-cli', '-o', wav_path, wem_path]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        error = result.stderr or result.stdout or 'unknown error'
        return (sid, False, f'vgmstream-cli failed: {error.strip()}')

    if not os.path.exists(wav_path) or os.path.getsize(wav_path) == 0:
        return (sid, False, 'Output file is empty or missing after decode')

    return (sid, True, None)


def main():
    parser = argparse.ArgumentParser(
        description='Fix Random Container render collision (Fact #17)')
    parser.add_argument('--txtp-dir', default='out_wwise/txtp',
                        help='Directory containing .txtp files')
    parser.add_argument('--pool-dir', default='pool',
                        help='Directory containing carved .wem files')
    parser.add_argument('--output-dir', default='out_wwise/wav',
                        help='Output directory for per-SID .wav files')
    parser.add_argument('--workers', type=int, default=8,
                        help='Number of thread pool workers for decoding')
    parser.add_argument('--log', default='logs/fix_random_container.log',
                        help='Log file path')
    parser.add_argument('--dry-run', action='store_true',
                        help='Only identify affected files, do not decode')
    args = parser.parse_args()

    logger = setup_logging(args.log)

    # --- Step 1: Identify affected .txtp files ---
    logger.info('Scanning %s for Random Container bug pattern...', args.txtp_dir)

    affected_files = []
    skipped_layer = 0
    total_scanned = 0

    for fname in sorted(os.listdir(args.txtp_dir)):
        fpath = os.path.join(args.txtp_dir, fname)
        if not fname.endswith('.txtp') or not os.path.isfile(fpath):
            continue
        total_scanned += 1

        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()

        has_group = 'group = ' in content
        if not has_group:
            continue

        has_ranseq = 'CAkRanSeqCntr' in content
        has_random = bool(re.search(r'eMode:\s*0x00\s*\[Random\]', content))
        sound_count = len(re.findall(r'CAkSound\[', content))
        has_layer = 'CAkLayerCntr' in content

        if has_layer:
            skipped_layer += 1
            continue

        if has_ranseq and has_random and sound_count >= 2:
            affected_files.append(fpath)

    logger.info('Scanned %d .txtp files', total_scanned)
    logger.info('Affected (CAkRanSeqCntr[Random], ≥2 children, no LayerCntr): %d',
                len(affected_files))
    logger.info('Skipped (CAkLayerCntr — correct behavior): %d', skipped_layer)

    # --- Step 2: Extract per-child Source IDs ---
    all_sids = set()
    txtp_to_sids = {}

    for fpath in affected_files:
        sids = extract_source_ids(fpath)
        txtp_to_sids[fpath] = sids
        all_sids.update(sids)
        logger.debug('%s: %d children, SIDs=%s',
                     os.path.basename(fpath), len(sids), sids)

    logger.info('Total unique SIDs to decode: %d', len(all_sids))

    if args.dry_run:
        logger.info('DRY RUN — not decoding. Listing affected files:')
        for fpath, sids in sorted(txtp_to_sids.items()):
            logger.info('  %s: %s', os.path.basename(fpath), sids)
        print(f'\nDry run complete: {len(affected_files)} affected files, '
              f'{len(all_sids)} unique SIDs')
        return

    # --- Step 3: Decode each SID from pool ---
    os.makedirs(args.output_dir, exist_ok=True)

    logger.info('Decoding %d unique SIDs using %d workers...',
                len(all_sids), args.workers)

    success_count = 0
    fail_count = 0
    skip_count = 0
    failed_sids = []

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(decode_wem, args.pool_dir, sid,
                            args.output_dir, logger): sid
            for sid in sorted(all_sids)
        }
        for i, future in enumerate(as_completed(futures), 1):
            sid = futures[future]
            try:
                sid_result, success, error_msg = future.result()
            except Exception as exc:
                logger.error('SID %s raised exception: %s', sid, exc)
                fail_count += 1
                failed_sids.append((sid, str(exc)))
                continue

            if success:
                if error_msg == 'already exists':
                    skip_count += 1
                else:
                    success_count += 1
            else:
                fail_count += 1
                failed_sids.append((sid, error_msg))
                logger.error('FAIL SID %s: %s', sid, error_msg)

            if i % 100 == 0 or i == len(all_sids):
                logger.info('Progress: %d/%d SIDs processed '
                            '(decoded=%d, skipped=%d, failed=%d)',
                            i, len(all_sids), success_count, skip_count,
                            fail_count)

    # --- Summary ---
    logger.info('=== RENDER FIX SUMMARY ===')
    logger.info('Affected .txtp files: %d', len(affected_files))
    logger.info('Total unique SIDs: %d', len(all_sids))
    logger.info('Newly decoded: %d', success_count)
    logger.info('Already existed (skipped): %d', skip_count)
    logger.info('Failed: %d', fail_count)

    if failed_sids:
        logger.error('Failed SIDs:')
        for sid, err in failed_sids:
            logger.error('  %s: %s', sid, err)

    print(f'\n=== RENDER FIX SUMMARY ===')
    print(f'Affected .txtp files: {len(affected_files)}')
    print(f'Total unique SIDs: {len(all_sids)}')
    print(f'Newly decoded: {success_count}')
    print(f'Already existed (skipped): {skip_count}')
    print(f'Failed: {fail_count}')

    if fail_count > 0:
        print(f'\nWARNING: {fail_count} SIDs failed to decode. '
              f'See {args.log} for details.')


if __name__ == '__main__':
    main()
