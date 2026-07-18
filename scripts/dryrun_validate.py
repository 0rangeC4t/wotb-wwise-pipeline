import subprocess
import os

import argparse

def dryrun_validate():
    parser = argparse.ArgumentParser(description="Dry-run validate .txtp files using vgmstream-cli.")
    parser.add_argument('--txtp-dir', default='out_wwise/txtp', help='Directory containing .txtp files')
    parser.add_argument('--report', default='logs/report_dryrun.log', help='Path to output report log file')
    args = parser.parse_args()

    txtp_dir = args.txtp_dir
    report_log = args.report
    os.makedirs(os.path.dirname(report_log) or 'logs', exist_ok=True)
    
    if not os.path.exists(txtp_dir):
        print(f"Error: {txtp_dir} does not exist. Run generate_txtp.py first.")
        return
        
    txtp_files = []
    for root, dirs, files in os.walk(txtp_dir):
        for file in files:
            if file.endswith('.txtp'):
                txtp_files.append(os.path.join(root, file))
                
    print(f"Found {len(txtp_files)} .txtp files to dry-run validate...")
    
    ok_count = 0
    missing_count = 0
    missing_details = []
    
    for i, path in enumerate(txtp_files):
        # Run vgmstream-cli -m -i to read metadata and check source file existence
        # -m: print metadata only, don't decode
        # -i: ignore looping information and play the whole stream once
        cmd = ['vgmstream-cli', '-m', '-i', path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Check returncode as the primary criteria for failure
        if result.returncode != 0:
            missing_count += 1
            missing_details.append(path)
        else:
            ok_count += 1
            
        if (i+1) % 100 == 0:
            print(f"Validated {i+1}/{len(txtp_files)} files...")
            
    # Write report
    with open(report_log, 'w', encoding='utf-8') as f:
        f.write(f"OK: {ok_count}\n")
        f.write(f"MISSING_SOURCE: {missing_count}\n")
        if missing_details:
            f.write("\nList of .txtp files missing source .wem files:\n")
            for item in missing_details:
                f.write(f"{item}\n")
                
    print(f"Dry-run validation complete. OK: {ok_count}, MISSING_SOURCE: {missing_count}.")
    print(f"Report written to {report_log}")

if __name__ == '__main__':
    dryrun_validate()
