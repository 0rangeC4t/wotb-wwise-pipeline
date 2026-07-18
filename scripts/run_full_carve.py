import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../core'))

from index_parser import parse_akpk, parse_didx
from carve_core import carve_by_index

import argparse

def run_carve():
    parser = argparse.ArgumentParser(description="Carve all .pck and .bnk archives.")
    parser.add_argument('--input', default='input/WwiseSound', help='Input WwiseSound directory')
    parser.add_argument('--output', default='pool', help='Output pool directory')
    args = parser.parse_args()
    
    wwisesound_dir = args.input
    pool_dir = args.output
    os.makedirs(pool_dir, exist_ok=True)
    
    # 1. Recursively find all .pck and .bnk files
    files_to_process = []
    for root, dirs, files in os.walk(wwisesound_dir):
        for file in files:
            filepath = os.path.join(root, file)
            if file.endswith('.pck'):
                files_to_process.append((filepath, 'pck'))
            elif file.endswith('.bnk'):
                files_to_process.append((filepath, 'bnk'))
                
    total_carved_count = 0
    total_error_count = 0
    unique_carved_ids = set()
    fid_to_archive = {}
    
    errors_log_path = 'logs/carve_errors.log'
    collisions_log_path = 'logs/carve_collisions.log'
    
    os.makedirs('logs', exist_ok=True)
    if os.path.exists(errors_log_path):
        os.remove(errors_log_path)
    if os.path.exists(collisions_log_path):
        os.remove(collisions_log_path)

    print(f"Scanning {len(files_to_process)} archive files...")
    
    for filepath, ftype in files_to_process:
        try:
            if ftype == 'pck':
                index = parse_akpk(filepath)
            else:
                index = parse_didx(filepath)
                
            if not index:
                continue
                
            carved = carve_by_index(filepath, index)
            for fid, data in carved.items():
                out_path = os.path.join(pool_dir, f"{fid}.wem")
                new_size = len(data)
                if os.path.exists(out_path):
                    old_size = os.path.getsize(out_path)
                    if old_size != new_size:
                        old_archive = fid_to_archive.get(fid, "unknown")
                        collision_log = f"ID: {fid}, old_file: {old_archive}, new_file: {filepath}, old_size: {old_size}, new_size: {new_size}\n"
                        with open(collisions_log_path, 'a', encoding='utf-8') as cf:
                            cf.write(collision_log)
                
                with open(out_path, 'wb') as out_f:
                    out_f.write(data)
                fid_to_archive[fid] = filepath
                unique_carved_ids.add(fid)
                total_carved_count += 1
                
        except Exception as e:
            total_error_count += 1
            with open(errors_log_path, 'a', encoding='utf-8') as ef:
                ef.write(f"File: {filepath}, Error: {e}\n")
            
    print(f"Scanned {len(files_to_process)} archives, {total_error_count} failed (see logs/carve_errors.log), carved {total_carved_count} files, {len(unique_carved_ids)} unique IDs")

if __name__ == '__main__':
    run_carve()
