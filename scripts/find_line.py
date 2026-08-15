with open("wproj/TestProject/Interactive Music Hierarchy/Default Work Unit.wwu", "r", encoding="utf-8") as f:
    lines = f.readlines()

target = 'Name="MusicSegment_860825692"'
for idx, line in enumerate(lines):
    if target in line:
        print(f"Line {idx+1}: {line.strip()}")
        # Print 50 lines before and after
        start = max(0, idx - 10)
        end = min(len(lines), idx + 80)
        with open("wwu_segment_section.txt", "w", encoding="utf-8") as out:
            for i in range(start, end):
                out.write(f"{i+1} | {lines[i]}")
        print("Wrote wwu_segment_section.txt")
        break
