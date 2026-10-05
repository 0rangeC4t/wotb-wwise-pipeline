import os
import sys
import subprocess
import time
from waapi import WaapiClient
import pprint

def main():
    container_guid = "{16B7D483-CD90-49D7-ACF2-6B97BD875095}" # MusicPlaylistContainer_1054648317
    
    # Connect to WAAPI
    try:
        client = WaapiClient(url="ws://localhost:8080/waapi")
        print("Connected to WAAPI successfully.")
    except Exception as e:
        print(f"Failed to connect to WAAPI: {e}")
        sys.exit(1)
        
    try:
        # Find the root playlist item owned by our container
        res = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicPlaylistItem"]}
        }, options={"return": ["id", "name", "type", "owner", "parent", "path"]})
        
        root_guid = None
        for pi in res.get("return", []):
            owner_id = pi.get("owner", {}).get("id")
            if owner_id == container_guid:
                root_guid = pi["id"]
                break
                
        if not root_guid:
            print("ERROR: Root playlist item not found for container.")
            sys.exit(1)
            
        print(f"Found root playlist item: {root_guid}")
        
        # Query descendants of root playlist item to clean them up (starting fresh)
        # Note: WAAPI transform "select": ["descendants"] is useful here
        desc_res = client.call("ak.wwise.core.object.get", {
            "from": {"id": [root_guid]},
            "transform": [{"select": ["descendants"]}]
        }, options={"return": ["id", "name", "type"]})
        
        descendants = desc_res.get("return", [])
        if descendants:
            print(f"Cleaning up {len(descendants)} existing playlist items...")
            for d in descendants:
                try:
                    client.call("ak.wwise.core.object.delete", {"object": d["id"]})
                    print(f"Deleted old item: {d['name']} ({d['id']})")
                except Exception as e:
                    print(f"Failed to delete {d['name']}: {e}")
            client.call("ak.wwise.core.project.save")
            
        # Configure Root group: LoopCount=0, PlayMode=0 (Sequence Continuous), PlaylistItemType=0 (Group)
        print("Configuring Root playlist item...")
        client.call("ak.wwise.core.object.setProperty", {
            "object": root_guid,
            "property": "PlaylistItemType",
            "value": 0
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": root_guid,
            "property": "PlayMode",
            "value": 0 # Sequence Continuous
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": root_guid,
            "property": "LoopCount",
            "value": 0
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": root_guid,
            "property": "Weight",
            "value": 50.0
        })
        
        # 1. Create Group A under Root (ContinuousRandom, Loop=1, Weight=50.0)
        print("Creating Group A...")
        group_a = client.call("ak.wwise.core.object.create", {
            "parent": root_guid,
            "type": "MusicPlaylistItem",
            "name": "Group_A_Random",
            "onNameConflict": "replace"
        })
        ga_guid = group_a["id"]
        client.call("ak.wwise.core.object.setProperty", {
            "object": ga_guid,
            "property": "PlaylistItemType",
            "value": 0 # Group
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": ga_guid,
            "property": "PlayMode",
            "value": 2 # Random Continuous
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": ga_guid,
            "property": "LoopCount",
            "value": 1
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": ga_guid,
            "property": "Weight",
            "value": 50.0
        })
        
        # Create Segment Item 860825692 under Group A (Loop=1, Weight=60.0)
        print("Adding Segment Item 860825692 to Group A...")
        seg_item_860825692_a = client.call("ak.wwise.core.object.create", {
            "parent": ga_guid,
            "type": "MusicPlaylistItem",
            "name": "Item_Seg_860825692",
            "onNameConflict": "replace"
        })
        sia_guid = seg_item_860825692_a["id"]
        client.call("ak.wwise.core.object.setProperty", {
            "object": sia_guid,
            "property": "PlaylistItemType",
            "value": 1 # Segment
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": sia_guid,
            "property": "LoopCount",
            "value": 1
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": sia_guid,
            "property": "Weight",
            "value": 60.0
        })
        
        # Create Segment Item 195645763 under Group A (Loop=1, Weight=50.0)
        print("Adding Segment Item 195645763 to Group A...")
        seg_item_195645763_a = client.call("ak.wwise.core.object.create", {
            "parent": ga_guid,
            "type": "MusicPlaylistItem",
            "name": "Item_Seg_195645763",
            "onNameConflict": "replace"
        })
        sib_guid = seg_item_195645763_a["id"]
        client.call("ak.wwise.core.object.setProperty", {
            "object": sib_guid,
            "property": "PlaylistItemType",
            "value": 1 # Segment
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": sib_guid,
            "property": "LoopCount",
            "value": 1
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": sib_guid,
            "property": "Weight",
            "value": 50.0
        })
        
        # 2. Create Group B under Root (ContinuousSequence, Loop=0, Weight=50.0)
        print("Creating Group B...")
        group_b = client.call("ak.wwise.core.object.create", {
            "parent": root_guid,
            "type": "MusicPlaylistItem",
            "name": "Group_B_Sequence",
            "onNameConflict": "replace"
        })
        gb_guid = group_b["id"]
        client.call("ak.wwise.core.object.setProperty", {
            "object": gb_guid,
            "property": "PlaylistItemType",
            "value": 0 # Group
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": gb_guid,
            "property": "PlayMode",
            "value": 0 # Sequence Continuous
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": gb_guid,
            "property": "LoopCount",
            "value": 0
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": gb_guid,
            "property": "Weight",
            "value": 50.0
        })
        
        # Create Group B1 under Group B (StepRandom, Loop=1, Weight=50.0)
        print("Creating Group B1...")
        group_b1 = client.call("ak.wwise.core.object.create", {
            "parent": gb_guid,
            "type": "MusicPlaylistItem",
            "name": "Group_B1_StepRandom",
            "onNameConflict": "replace"
        })
        gb1_guid = group_b1["id"]
        client.call("ak.wwise.core.object.setProperty", {
            "object": gb1_guid,
            "property": "PlaylistItemType",
            "value": 0 # Group
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": gb1_guid,
            "property": "PlayMode",
            "value": 3 # Random Step
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": gb1_guid,
            "property": "LoopCount",
            "value": 1
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": gb1_guid,
            "property": "Weight",
            "value": 50.0
        })
        
        # Create Segment Item 797778272 under Group B1 (Loop=1, Weight=50.0)
        print("Adding Segment Item 797778272 to Group B1...")
        seg_item_797778272_b1 = client.call("ak.wwise.core.object.create", {
            "parent": gb1_guid,
            "type": "MusicPlaylistItem",
            "name": "Item_Seg_797778272",
            "onNameConflict": "replace"
        })
        sib1a_guid = seg_item_797778272_b1["id"]
        client.call("ak.wwise.core.object.setProperty", {
            "object": sib1a_guid,
            "property": "PlaylistItemType",
            "value": 1 # Segment
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": sib1a_guid,
            "property": "LoopCount",
            "value": 1
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": sib1a_guid,
            "property": "Weight",
            "value": 50.0
        })
        
        # Create Segment Item 626154474 under Group B1 (Loop=2, Weight=50.0)
        print("Adding Segment Item 626154474 to Group B1...")
        seg_item_626154474_b1 = client.call("ak.wwise.core.object.create", {
            "parent": gb1_guid,
            "type": "MusicPlaylistItem",
            "name": "Item_Seg_626154474",
            "onNameConflict": "replace"
        })
        sib1b_guid = seg_item_626154474_b1["id"]
        client.call("ak.wwise.core.object.setProperty", {
            "object": sib1b_guid,
            "property": "PlaylistItemType",
            "value": 1 # Segment
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": sib1b_guid,
            "property": "LoopCount",
            "value": 2
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": sib1b_guid,
            "property": "Weight",
            "value": 50.0
        })
        
        # Create Group B2 under Group B (ContinuousRandom, Loop=1, Weight=50.0)
        print("Creating Group B2...")
        group_b2 = client.call("ak.wwise.core.object.create", {
            "parent": gb_guid,
            "type": "MusicPlaylistItem",
            "name": "Group_B2_ContinuousRandom",
            "onNameConflict": "replace"
        })
        gb2_guid = group_b2["id"]
        client.call("ak.wwise.core.object.setProperty", {
            "object": gb2_guid,
            "property": "PlaylistItemType",
            "value": 0 # Group
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": gb2_guid,
            "property": "PlayMode",
            "value": 2 # Random Continuous
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": gb2_guid,
            "property": "LoopCount",
            "value": 1
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": gb2_guid,
            "property": "Weight",
            "value": 50.0
        })
        
        # Create Segment Item 195645763 under Group B2 (Loop=1, Weight=25.0)
        print("Adding Segment Item 195645763 to Group B2...")
        seg_item_195645763_b2 = client.call("ak.wwise.core.object.create", {
            "parent": gb2_guid,
            "type": "MusicPlaylistItem",
            "name": "Item_Seg_195645763",
            "onNameConflict": "replace"
        })
        sib2a_guid = seg_item_195645763_b2["id"]
        client.call("ak.wwise.core.object.setProperty", {
            "object": sib2a_guid,
            "property": "PlaylistItemType",
            "value": 1 # Segment
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": sib2a_guid,
            "property": "LoopCount",
            "value": 1
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": sib2a_guid,
            "property": "Weight",
            "value": 25.0
        })
        
        # Create Segment Item 860825692 under Group B2 (Loop=1, Weight=75.0)
        print("Adding Segment Item 860825692 to Group B2...")
        seg_item_860825692_b2 = client.call("ak.wwise.core.object.create", {
            "parent": gb2_guid,
            "type": "MusicPlaylistItem",
            "name": "Item_Seg_860825692",
            "onNameConflict": "replace"
        })
        sib2b_guid = seg_item_860825692_b2["id"]
        client.call("ak.wwise.core.object.setProperty", {
            "object": sib2b_guid,
            "property": "PlaylistItemType",
            "value": 1 # Segment
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": sib2b_guid,
            "property": "LoopCount",
            "value": 1
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": sib2b_guid,
            "property": "Weight",
            "value": 75.0
        })
        
        # Save project
        client.call("ak.wwise.core.project.save")
        print("Project saved via WAAPI.")
        
    except Exception as e:
        print(f"Error during tree building: {e}")
        sys.exit(1)
    finally:
        client.disconnect()
        
    # Reboot Wwise to inject references on disk
    print("Running reboot_wwise.py to reboot Wwise and inject Segment ObjectRefs...")
    subprocess.run(["python3", "scripts/reboot_wwise.py"], check=True)
    print("Finished successfully.")

if __name__ == "__main__":
    main()
