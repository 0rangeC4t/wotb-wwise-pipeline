import os
import subprocess
import argparse
from concurrent.futures import ThreadPoolExecutor

def render_wav():
    parser = argparse.ArgumentParser(description="Render .txtp files to .wav files using vgmstream-cli.")
    parser.add_argument('--txtp-dir', default='out_wwise/txtp', help='Directory containing .txtp files')
    parser.add_argument('--output', default='out_wwise/wav', help='Output directory for .wav files')
    parser.add_argument('--report', default='logs/report_dryrun.log', help='Path to dryrun report log file')
    parser.add_argument('--limit', type=int, default=None, help='Limit the number of files to render (for testing)')
    parser.add_argument('--workers', type=int, default=8, help='Number of thread pool workers')
    args = parser.parse_args()

    txtp_dir = args.txtp_dir
    output_dir = args.output
    report_log = args.report
    limit = args.limit
    workers = args.workers

    if not os.path.exists(txtp_dir):
        print(f"Error: {txtp_dir} does not exist.")
        return

    # Parse report_dryrun.log to find missing/failed files to skip
    missing_files = set()
    if os.path.exists(report_log):
        with open(report_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        is_missing_section = False
        for line in lines:
            line = line.strip()
            if "List of .txtp files missing source" in line:
                is_missing_section = True
                continue
            if is_missing_section and line:
                missing_files.add(os.path.abspath(line))

    # Find all .txtp files
    all_txtp = []
    for root, _, files in os.walk(txtp_dir):
        for file in files:
            if file.endswith('.txtp'):
                all_txtp.append(os.path.join(root, file))

    # Filter out missing source files
    ok_txtp = []
    for path in all_txtp:
        if os.path.abspath(path) not in missing_files:
            ok_txtp.append(path)

    print(f"Total .txtp found: {len(all_txtp)}")
    print(f"Skipping (missing source): {len(missing_files)}")
    print(f"Ready to render: {len(ok_txtp)}")

    if limit is not None:
        ok_txtp = ok_txtp[:limit]
        print(f"Limiting render to {limit} files for testing.")

    if not ok_txtp:
        print("No files to render.")
        return

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs('logs', exist_ok=True)

    errors_log = 'logs/render_errors.log'
    # Clear previous error log if any
    if os.path.exists(errors_log):
        os.remove(errors_log)

    success_count = 0
    fail_count = 0
    failed_details = []

    def render_one(txtp_path):
        nonlocal success_count, fail_count
        # Determine output wav path preserving structure relative to txtp_dir
        rel_path = os.path.relpath(txtp_path, txtp_dir)
        wav_rel_path = os.path.splitext(rel_path)[0] + '.wav'
        wav_out_path = os.path.join(output_dir, wav_rel_path)

        os.makedirs(os.path.dirname(wav_out_path), exist_ok=True)

        cmd = ['vgmstream-cli', '-o', wav_out_path, txtp_path]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return False, txtp_path, result.stderr or result.stdout
        else:
            # Verify file exists and has size > 0
            if os.path.exists(wav_out_path) and os.path.getsize(wav_out_path) > 0:
                return True, txtp_path, None
            else:
                return False, txtp_path, "Output file is empty or missing"

    print(f"Starting render using ThreadPoolExecutor with {workers} workers...")
    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = executor.map(render_one, ok_txtp)
        for i, (success, path, error_msg) in enumerate(results):
            if success:
                success_count += 1
            else:
                fail_count += 1
                failed_details.append((path, error_msg))
            
            if (i+1) % 100 == 0 or (i+1) == len(ok_txtp):
                print(f"Progress: {i+1}/{len(ok_txtp)} files processed...")

    # Write errors log if any
    if failed_details:
        with open(errors_log, 'w', encoding='utf-8') as f:
            for path, err in failed_details:
                f.write(f"FAIL: {path}\nReason: {err}\n\n")
        print(f"Errors logged to {errors_log}")

    print("\n=== RENDER SUMMARY ===")
    print(f"Rendered: {success_count}/{len(ok_txtp)}")
    print(f"Failed: {fail_count}")

if __name__ == '__main__':
    render_wav()
