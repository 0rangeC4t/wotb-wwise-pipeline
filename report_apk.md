# Interactive Music Hierarchy Investigation Report

This report presents the real structure of the Interactive Music Hierarchy objects parsed directly from the soundbanks `music_hangar.bnk` and `apk.bnk`. All data has been extracted from the real HIRC XML representation of these banks with zero assumptions or filled gaps.

## Soundbank: `apk.bnk`
Total parsed objects: **17** (Tracks: 7, Segments: 7, Random/Sequence Containers: 3, Switch Containers: 0)

### 1. Object Hierarchy Tree
- **[RanSeqContainer]** ID: `359976450`
  - **[PlaylistGroup]** 3 children (Loop: `0`, Random/Seq Type: `0x02 [ContinuousRandom]`, Weight: `50000`)
    - **[PlaylistItem]** Segment ID: `201235529` (Loop: `1`, Random/Seq Type: `-1 [None]`, Weight: `50000`)
      - **[Segment]** ID: `201235529` (Duration: `7680.0` ms)
        - **[Track]** ID: `558864082` (Type: `0x00 [Normal]`) -> Source IDs: `783383513` (Loginscreen\\Loginscreen_2021\\login_drone_drums_loop_01.wav -> `SFX\\Loginscreen\\Loginscreen_2021\\login_drone_drums_loop_01_97F42061.wem`)
    - **[PlaylistItem]** Segment ID: `37419850` (Loop: `1`, Random/Seq Type: `-1 [None]`, Weight: `50000`)
      - **[Segment]** ID: `37419850` (Duration: `7680.0` ms)
        - **[Track]** ID: `921557064` (Type: `0x00 [Normal]`) -> Source IDs: `255291834` (Loginscreen\\Loginscreen_2021\\login_drone_drums_loop_02.wav -> `SFX\\Loginscreen\\Loginscreen_2021\\login_drone_drums_loop_02_97F42061.wem`)
    - **[PlaylistItem]** Segment ID: `308239515` (Loop: `1`, Random/Seq Type: `-1 [None]`, Weight: `50000`)
      - **[Segment]** ID: `308239515` (Duration: `7680.04535147392` ms)
        - **[Track]** ID: `686286511` (Type: `0x00 [Normal]`) -> Source IDs: `56953293` (Loginscreen\\Loginscreen_2021\\login_drone_drums_loop_03.wav -> `SFX\\Loginscreen\\Loginscreen_2021\\login_drone_drums_loop_03_97F42061.wem`)
- **[RanSeqContainer]** ID: `517021411`
  - **[PlaylistGroup]** 1 children (Loop: `0`, Random/Seq Type: `0x00 [ContinuousSequence]`, Weight: `50000`)
    - **[PlaylistItem]** Segment ID: `519451801` (Loop: `1`, Random/Seq Type: `-1 [None]`, Weight: `50000`)
      - **[Segment]** ID: `519451801` (Duration: `20000.0` ms)
        - **[Track]** ID: `960691355` (Type: `0x00 [Normal]`) -> Source IDs: `362746063` (Loginscreen\\Loginscreen_2021\\login_drone_war_ambience.wav -> `SFX\\Loginscreen\\Loginscreen_2021\\login_drone_war_ambience_6B513CCE.wem`)
- **[RanSeqContainer]** ID: `543160948`
  - **[PlaylistGroup]** 3 children (Loop: `1`, Random/Seq Type: `0x02 [ContinuousRandom]`, Weight: `50000`)
    - **[PlaylistItem]** Segment ID: `950042432` (Loop: `0`, Random/Seq Type: `-1 [None]`, Weight: `50000`)
      - **[Segment]** ID: `950042432` (Duration: `30720.0` ms)
        - **[Track]** ID: `387347864` (Type: `0x00 [Normal]`) -> Source IDs: `315220599` (Loginscreen\\Loginscreen_2021\\login_drone_music_loop_01.wav -> `SFX\\Loginscreen\\Loginscreen_2021\\login_drone_music_loop_01_97F42061.wem`)
    - **[PlaylistItem]** Segment ID: `737701375` (Loop: `0`, Random/Seq Type: `-1 [None]`, Weight: `50000`)
      - **[Segment]** ID: `737701375` (Duration: `30720.0` ms)
        - **[Track]** ID: `374737966` (Type: `0x00 [Normal]`) -> Source IDs: `393637054` (Loginscreen\\Loginscreen_2021\\login_drone_music_loop_02.wav -> `SFX\\Loginscreen\\Loginscreen_2021\\login_drone_music_loop_02_97F42061.wem`)
    - **[PlaylistItem]** Segment ID: `1037442491` (Loop: `0`, Random/Seq Type: `-1 [None]`, Weight: `50000`)
      - **[Segment]** ID: `1037442491` (Duration: `30720.0` ms)
        - **[Track]** ID: `514718034` (Type: `0x00 [Normal]`) -> Source IDs: `919841421` (Loginscreen\\Loginscreen_2021\\login_drone_music_loop_03.wav -> `SFX\\Loginscreen\\Loginscreen_2021\\login_drone_music_loop_03_97F42061.wem`)


### 2. Segment Markers & Cue Points
#### Segment ID: `1037442491`
- **Duration:** `30720.0` ms
| Marker ID | Position (ms) | Name / Cue Point | Type (Deduced) |
| --- | --- | --- | --- |
| `43573010` | `0.0` | "" | Entry Cue (hash: 43573010) |
| `1539036744` | `30720.0` | "" | Exit Cue (hash: 1539036744) |

#### Segment ID: `201235529`
- **Duration:** `7680.0` ms
| Marker ID | Position (ms) | Name / Cue Point | Type (Deduced) |
| --- | --- | --- | --- |
| `43573010` | `0.0` | "" | Entry Cue (hash: 43573010) |
| `1539036744` | `7680.0` | "" | Exit Cue (hash: 1539036744) |

#### Segment ID: `308239515`
- **Duration:** `7680.04535147392` ms
| Marker ID | Position (ms) | Name / Cue Point | Type (Deduced) |
| --- | --- | --- | --- |
| `43573010` | `0.0` | "" | Entry Cue (hash: 43573010) |
| `1539036744` | `7680.04535147392` | "" | Exit Cue (hash: 1539036744) |

#### Segment ID: `37419850`
- **Duration:** `7680.0` ms
| Marker ID | Position (ms) | Name / Cue Point | Type (Deduced) |
| --- | --- | --- | --- |
| `43573010` | `0.0` | "" | Entry Cue (hash: 43573010) |
| `1539036744` | `7680.0` | "" | Exit Cue (hash: 1539036744) |

#### Segment ID: `519451801`
- **Duration:** `20000.0` ms
| Marker ID | Position (ms) | Name / Cue Point | Type (Deduced) |
| --- | --- | --- | --- |
| `43573010` | `0.0` | "" | Entry Cue (hash: 43573010) |
| `1539036744` | `20000.0` | "" | Exit Cue (hash: 1539036744) |

#### Segment ID: `737701375`
- **Duration:** `30720.0` ms
| Marker ID | Position (ms) | Name / Cue Point | Type (Deduced) |
| --- | --- | --- | --- |
| `43573010` | `0.0` | "" | Entry Cue (hash: 43573010) |
| `1539036744` | `30720.0` | "" | Exit Cue (hash: 1539036744) |

#### Segment ID: `950042432`
- **Duration:** `30720.0` ms
| Marker ID | Position (ms) | Name / Cue Point | Type (Deduced) |
| --- | --- | --- | --- |
| `43573010` | `0.0` | "" | Entry Cue (hash: 43573010) |
| `1539036744` | `30720.0` | "" | Exit Cue (hash: 1539036744) |

### 3. Switch Container Driving Game Syncs
*No Switch Containers present in this soundbank.*

### 4. Transition Rules
#### Rule in `CAkMusicRanSeqCntr` ID: `359976450` (Index 0)
- **Source Segment / Container ID:** `-1`
- **Destination Segment / Container ID:** `-1`
- **Source (Out-Transition) Rule:**
  - Fade-out Time: `0` ms
  - Fade Curve: `0x04 [Linear]`
  - Fade Offset: `0` ms
  - Sync Point: `0x07 [ExitMarker]`
  - Play Post-Exit: `1`
- **Destination (In-Transition) Rule:**
  - Fade-in Time: `0` ms
  - Fade Curve: `0x04 [Linear]`
  - Fade Offset: `0` ms
  - Jump To: `0x00 [StartOfPlaylist]` (ID: `0`)
  - Entry Type: `0x00 [EntryMarker]`
  - Play Pre-Entry: `1`
  - Match Source Cue Name: `0`

#### Rule in `CAkMusicRanSeqCntr` ID: `517021411` (Index 0)
- **Source Segment / Container ID:** `-1`
- **Destination Segment / Container ID:** `-1`
- **Source (Out-Transition) Rule:**
  - Fade-out Time: `0` ms
  - Fade Curve: `0x04 [Linear]`
  - Fade Offset: `0` ms
  - Sync Point: `0x07 [ExitMarker]`
  - Play Post-Exit: `1`
- **Destination (In-Transition) Rule:**
  - Fade-in Time: `0` ms
  - Fade Curve: `0x04 [Linear]`
  - Fade Offset: `0` ms
  - Jump To: `0x00 [StartOfPlaylist]` (ID: `0`)
  - Entry Type: `0x00 [EntryMarker]`
  - Play Pre-Entry: `1`
  - Match Source Cue Name: `0`

#### Rule in `CAkMusicRanSeqCntr` ID: `543160948` (Index 0)
- **Source Segment / Container ID:** `-1`
- **Destination Segment / Container ID:** `-1`
- **Source (Out-Transition) Rule:**
  - Fade-out Time: `0` ms
  - Fade Curve: `0x04 [Linear]`
  - Fade Offset: `0` ms
  - Sync Point: `0x07 [ExitMarker]`
  - Play Post-Exit: `1`
- **Destination (In-Transition) Rule:**
  - Fade-in Time: `0` ms
  - Fade Curve: `0x04 [Linear]`
  - Fade Offset: `0` ms
  - Jump To: `0x00 [StartOfPlaylist]` (ID: `0`)
  - Entry Type: `0x00 [EntryMarker]`
  - Play Pre-Entry: `1`
  - Match Source Cue Name: `0`

### 5. Explicitly Flagged Gaps & Open Questions
- **No driving Game Syncs or Arguments** were found in `apk.bnk`'s Music structures, only independent CAkMusicRanSeqCntr playlist segments. Is there a game code trigger that starts specific events directly, bypassing any State/Switch logic inside the hierarchy itself?
- **Unknown state or switch names:** Since no `CAkMusicSwitchCntr` exists in `apk.bnk`, there are no State/Switch group IDs to resolve in this bank.
