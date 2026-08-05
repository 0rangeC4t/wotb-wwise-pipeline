from waapi import WaapiClient
try:
    client = WaapiClient(url="ws://localhost:8080/waapi")
    
    # Create SoundBank TestBank
    bank_obj = client.call("ak.wwise.core.object.create", {
        "parent": "\\SoundBanks\\Default Work Unit",
        "type": "SoundBank",
        "name": "TestBank",
        "onNameConflict": "merge"
    })
    print("SoundBank created:", bank_obj)
    
    # Add GUI_halloween_2018_perk_afterburner to TestBank
    inclusions = [
        {
            "object": "\\Actor-Mixer Hierarchy\\Default Work Unit\\GUI_halloween_2018_perk_afterburner",
            "filter": ["media"]
        }
    ]
    res = client.call("ak.wwise.core.soundbank.setInclusions", {
        "soundbank": "\\SoundBanks\\Default Work Unit\\TestBank",
        "operation": "replace",
        "inclusions": inclusions
    })
    print("Inclusions set:", res)
    
    # Save project
    client.call("ak.wwise.core.project.save")
    print("Project saved!")
    client.disconnect()
except Exception as e:
    print("Error:", e)
