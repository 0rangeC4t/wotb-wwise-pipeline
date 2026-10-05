import json
import sys
from waapi import WaapiClient

def main():
    # Connect to WAAPI
    try:
        client = WaapiClient(url="ws://localhost:8080/waapi")
        print("Connected to WAAPI successfully.")
    except Exception as e:
        print(f"Failed to connect to WAAPI: {e}")
        sys.exit(1)

    try:
        # Find the target MusicPlaylistContainer GUID
        container_res = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicPlaylistContainer"]}
        }, options={"return": ["id", "name"]})
        
        container_guid = None
        for obj in container_res.get("return", []):
            if obj["name"] == "MusicPlaylistContainer_1054648317":
                container_guid = obj["id"]
                break
                
        if not container_guid:
            print("ERROR: MusicPlaylistContainer_1054648317 not found!")
            sys.exit(1)
            
        print(f"Found MusicPlaylistContainer_1054648317 GUID: {container_guid}")

        # 1. Find the root MusicPlaylistItem: query all objects of type MusicPlaylistItem
        playlist_items_res = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicPlaylistItem"]}
        }, options={"return": ["id", "name", "owner"]})
        
        root_guid = None
        for pi in playlist_items_res.get("return", []):
            owner_id = pi.get("owner", {}).get("id")
            if owner_id == container_guid:
                root_guid = pi["id"]
                break
                
        if not root_guid:
            print("ERROR: Root playlist item not found for container.")
            sys.exit(1)
            
        print(f"Found Root MusicPlaylistItem GUID: {root_guid}")

        # Clean up any existing descendants of root_guid first
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

        # 2. Configure Root: set PlaylistItemType=0, PlayMode=0, LoopCount=0
        print("Configuring Root playlist item...")
        client.call("ak.wwise.core.object.setProperty", {
            "object": root_guid,
            "property": "PlaylistItemType",
            "value": 0
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": root_guid,
            "property": "PlayMode",
            "value": 0
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": root_guid,
            "property": "LoopCount",
            "value": 0
        })

        # Build this tree under root:
        
        # --- Group A (PlaylistItemType=0, PlayMode=2 [ContinuousRandom], LoopCount=1, Weight=50.0)
        print("Creating Group A...")
        group_a = client.call("ak.wwise.core.object.create", {
            "parent": root_guid,
            "type": "MusicPlaylistItem",
            "name": "Group_A",
            "onNameConflict": "replace"
        })
        ga_guid = group_a["id"]
        
        client.call("ak.wwise.core.object.setProperty", {"object": ga_guid, "property": "PlaylistItemType", "value": 0})
        client.call("ak.wwise.core.object.setProperty", {"object": ga_guid, "property": "PlayMode", "value": 2})
        client.call("ak.wwise.core.object.setProperty", {"object": ga_guid, "property": "LoopCount", "value": 1})
        client.call("ak.wwise.core.object.setProperty", {"object": ga_guid, "property": "Weight", "value": 50.0})

        # Leaf 1: will link to segment 860825692 (PlaylistItemType=1, LoopCount=1, Weight=60.0)
        print("Creating Leaf 1...")
        leaf_1 = client.call("ak.wwise.core.object.create", {
            "parent": ga_guid,
            "type": "MusicPlaylistItem",
            "name": "Leaf_Seg_860825692",
            "onNameConflict": "replace"
        })
        l1_guid = leaf_1["id"]
        client.call("ak.wwise.core.object.setProperty", {"object": l1_guid, "property": "PlaylistItemType", "value": 1})
        client.call("ak.wwise.core.object.setProperty", {"object": l1_guid, "property": "LoopCount", "value": 1})
        client.call("ak.wwise.core.object.setProperty", {"object": l1_guid, "property": "Weight", "value": 60.0})

        # Leaf 2: will link to segment 195645763 (PlaylistItemType=1, LoopCount=1, Weight=50.0)
        print("Creating Leaf 2...")
        leaf_2 = client.call("ak.wwise.core.object.create", {
            "parent": ga_guid,
            "type": "MusicPlaylistItem",
            "name": "Leaf_Seg_195645763",
            "onNameConflict": "replace"
        })
        l2_guid = leaf_2["id"]
        client.call("ak.wwise.core.object.setProperty", {"object": l2_guid, "property": "PlaylistItemType", "value": 1})
        client.call("ak.wwise.core.object.setProperty", {"object": l2_guid, "property": "LoopCount", "value": 1})
        client.call("ak.wwise.core.object.setProperty", {"object": l2_guid, "property": "Weight", "value": 50.0})


        # --- Group B (PlaylistItemType=0, PlayMode=0 [Sequence], LoopCount=0, Weight=50.0)
        print("Creating Group B...")
        group_b = client.call("ak.wwise.core.object.create", {
            "parent": root_guid,
            "type": "MusicPlaylistItem",
            "name": "Group_B",
            "onNameConflict": "replace"
        })
        gb_guid = group_b["id"]
        
        client.call("ak.wwise.core.object.setProperty", {"object": gb_guid, "property": "PlaylistItemType", "value": 0})
        client.call("ak.wwise.core.object.setProperty", {"object": gb_guid, "property": "PlayMode", "value": 0})
        client.call("ak.wwise.core.object.setProperty", {"object": gb_guid, "property": "LoopCount", "value": 0})
        client.call("ak.wwise.core.object.setProperty", {"object": gb_guid, "property": "Weight", "value": 50.0})

        # --- Group B1 (PlaylistItemType=0, PlayMode=3 [StepRandom], LoopCount=1, Weight=50.0)
        print("Creating Group B1...")
        group_b1 = client.call("ak.wwise.core.object.create", {
            "parent": gb_guid,
            "type": "MusicPlaylistItem",
            "name": "Group_B1",
            "onNameConflict": "replace"
        })
        gb1_guid = group_b1["id"]
        
        client.call("ak.wwise.core.object.setProperty", {"object": gb1_guid, "property": "PlaylistItemType", "value": 0})
        client.call("ak.wwise.core.object.setProperty", {"object": gb1_guid, "property": "PlayMode", "value": 3})
        client.call("ak.wwise.core.object.setProperty", {"object": gb1_guid, "property": "LoopCount", "value": 1})
        client.call("ak.wwise.core.object.setProperty", {"object": gb1_guid, "property": "Weight", "value": 50.0})

        # Leaf 3: will link to segment 797778272 (PlaylistItemType=1, LoopCount=1, Weight=50.0)
        print("Creating Leaf 3...")
        leaf_3 = client.call("ak.wwise.core.object.create", {
            "parent": gb1_guid,
            "type": "MusicPlaylistItem",
            "name": "Leaf_Seg_797778272",
            "onNameConflict": "replace"
        })
        l3_guid = leaf_3["id"]
        client.call("ak.wwise.core.object.setProperty", {"object": l3_guid, "property": "PlaylistItemType", "value": 1})
        client.call("ak.wwise.core.object.setProperty", {"object": l3_guid, "property": "LoopCount", "value": 1})
        client.call("ak.wwise.core.object.setProperty", {"object": l3_guid, "property": "Weight", "value": 50.0})

        # Leaf 4: will link to segment 626154474 (PlaylistItemType=1, LoopCount=2, Weight=50.0)
        print("Creating Leaf 4...")
        leaf_4 = client.call("ak.wwise.core.object.create", {
            "parent": gb1_guid,
            "type": "MusicPlaylistItem",
            "name": "Leaf_Seg_626154474",
            "onNameConflict": "replace"
        })
        l4_guid = leaf_4["id"]
        client.call("ak.wwise.core.object.setProperty", {"object": l4_guid, "property": "PlaylistItemType", "value": 1})
        client.call("ak.wwise.core.object.setProperty", {"object": l4_guid, "property": "LoopCount", "value": 2})
        client.call("ak.wwise.core.object.setProperty", {"object": l4_guid, "property": "Weight", "value": 50.0})


        # --- Group B2 (PlaylistItemType=0, PlayMode=2 [ContinuousRandom], LoopCount=1, Weight=50.0)
        print("Creating Group B2...")
        group_b2 = client.call("ak.wwise.core.object.create", {
            "parent": gb_guid,
            "type": "MusicPlaylistItem",
            "name": "Group_B2",
            "onNameConflict": "replace"
        })
        gb2_guid = group_b2["id"]
        
        client.call("ak.wwise.core.object.setProperty", {"object": gb2_guid, "property": "PlaylistItemType", "value": 0})
        client.call("ak.wwise.core.object.setProperty", {"object": gb2_guid, "property": "PlayMode", "value": 2})
        client.call("ak.wwise.core.object.setProperty", {"object": gb2_guid, "property": "LoopCount", "value": 1})
        client.call("ak.wwise.core.object.setProperty", {"object": gb2_guid, "property": "Weight", "value": 50.0})

        # Leaf 5: will link to segment 195645763 (PlaylistItemType=1, LoopCount=1, Weight=25.0)
        print("Creating Leaf 5...")
        leaf_5 = client.call("ak.wwise.core.object.create", {
            "parent": gb2_guid,
            "type": "MusicPlaylistItem",
            "name": "Leaf_Seg_195645763_b2",
            "onNameConflict": "replace"
        })
        l5_guid = leaf_5["id"]
        client.call("ak.wwise.core.object.setProperty", {"object": l5_guid, "property": "PlaylistItemType", "value": 1})
        client.call("ak.wwise.core.object.setProperty", {"object": l5_guid, "property": "LoopCount", "value": 1})
        client.call("ak.wwise.core.object.setProperty", {"object": l5_guid, "property": "Weight", "value": 25.0})

        # Leaf 6: will link to segment 860825692 (PlaylistItemType=1, LoopCount=1, Weight=75.0)
        print("Creating Leaf 6...")
        leaf_6 = client.call("ak.wwise.core.object.create", {
            "parent": gb2_guid,
            "type": "MusicPlaylistItem",
            "name": "Leaf_Seg_860825692_b2",
            "onNameConflict": "replace"
        })
        l6_guid = leaf_6["id"]
        client.call("ak.wwise.core.object.setProperty", {"object": l6_guid, "property": "PlaylistItemType", "value": 1})
        client.call("ak.wwise.core.object.setProperty", {"object": l6_guid, "property": "LoopCount", "value": 1})
        client.call("ak.wwise.core.object.setProperty", {"object": l6_guid, "property": "Weight", "value": 75.0})

        # 4. Save the project via ak.wwise.core.project.save.
        client.call("ak.wwise.core.project.save")
        print("Project saved successfully.")

        # Prepare final output structure
        output_data = [
            {"leaf_index": 1, "segment": 860825692, "id": l1_guid},
            {"leaf_index": 2, "segment": 195645763, "id": l2_guid},
            {"leaf_index": 3, "segment": 797778272, "id": l3_guid},
            {"leaf_index": 4, "segment": 626154474, "id": l4_guid},
            {"leaf_index": 5, "segment": 195645763, "id": l5_guid},
            {"leaf_index": 6, "segment": 860825692, "id": l6_guid}
        ]
        
        print("\n=== LEAF MAPPING JSON ===")
        print(json.dumps(output_data, indent=2))
        print("=========================\n")

    except Exception as e:
        print(f"Error during execution: {e}")
        sys.exit(1)
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()
