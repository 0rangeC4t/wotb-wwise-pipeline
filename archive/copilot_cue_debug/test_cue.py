import os
import sys
import json
from waapi import WaapiClient

def test():
    ports = [8080, 8090, 11987, 11988, 42571]
    client = None
    for port in ports:
        try:
            url = f"ws://localhost:{port}/waapi"
            print(f"Trying to connect to: {url}...")
            client = WaapiClient(url=url)
            print(f"Connected to WAAPI successfully on port {port}!")
            break
        except Exception as e:
            print(f"Failed on port {port}: {e}")
            
    if not client:
        print("Could not connect to WAAPI on any probed port!")
        return

    try:
        # 1. Create a test segment
        print("Creating test segment...")
        seg_res = client.call("ak.wwise.core.object.create", {
            "parent": "\\Interactive Music Hierarchy\\Default Work Unit",
            "type": "MusicSegment",
            "name": "TEST_SEG_WITH_AUDIO",
            "onNameConflict": "replace"
        })
        seg_id = seg_res["id"]

        # 2. Create track under segment
        print("Creating track...")
        track_res = client.call("ak.wwise.core.object.create", {
            "parent": seg_id,
            "type": "MusicTrack",
            "name": "TEST_TRACK",
            "onNameConflict": "replace"
        })
        track_id = track_res["id"]

        # 3. Import a real audio file (from wav_music)
        wav_file = os.path.abspath("out_wwise/wav_music/56953293.wav")
        wine_wav_path = "Z:" + wav_file.replace("/", "\\")
        print(f"Importing audio: {wine_wav_path}")
        
        # We need the full path in interactive music hierarchy
        track_path = "\\Interactive Music Hierarchy\\Default Work Unit\\TEST_SEG_WITH_AUDIO\\TEST_TRACK"
        import_res = client.call("ak.wwise.core.audio.import", {
            "importOperation": "useExisting",
            "imports": [
                {
                    "audioFile": wine_wav_path,
                    "objectPath": track_path,
                    "objectType": "MusicTrack"
                }
            ]
        })
        print("Import response:", json.dumps(import_res, indent=2))

        # Save project
        client.call("ak.wwise.core.project.save")

        # 4. Get cues for this segment
        cues_res = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicCue"]}
        }, options={"return": ["id", "name", "path"]})
        
        for cue in cues_res.get("return", []):
            if "TEST_SEG_WITH_AUDIO" in cue["path"]:
                print(f"Found cue: {cue['name']} (id: {cue['id']})")
                print("Setting 'TimeMs' on cue...")
                try:
                    client.call("ak.wwise.core.object.setProperty", {
                        "object": cue["id"],
                        "property": "TimeMs",
                        "value": 2500.0
                    })
                    print("Successfully set TimeMs to 2500.0!")
                except Exception as ex:
                    print(f"Failed to set TimeMs: {ex}")

        # Clean up
        print("Cleaning up test segment...")
        client.call("ak.wwise.core.object.delete", {"object": seg_id})
        client.call("ak.wwise.core.project.save")
        print("Cleaned up and saved.")

    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        client.disconnect()

if __name__ == "__main__":
    test()
