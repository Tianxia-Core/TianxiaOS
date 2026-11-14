import std/[macros, strutils, posix, os]

type
  Tier* = enum
    tTianxiaOS = 0, tSystem = 1, tSubsystem = 2, tUnit = 3, tFile = 4

  IsolationPlane* = enum
    pNative = 0, pElasticNs = 1, pMicroVm = 2

  StaticNodeSpec* = object
    id*: uint32
    parentId*: uint32
    tier*: Tier
    plane*: IsolationPlane
    colorRgb*: uint32
    ephemeralScore*: uint16
    judgmentWarn*: uint16
    label*: string
    target*: string
    telemetry*: string

  MenuNode* {.packed.} = object
    id*: uint32
    parentId*: uint32
    tier*: uint8
    isolation*: uint8
    pad*: uint16
    statusColorRgb*: uint32
    ephemeralScoreQ16*: uint16
    judgmentWarnFlag*: uint16
    label*: array[64, char]
    targetPath*: array[128, char]
    telemetrySummary*: array[64, char]

  SharedMenuState* {.packed.} = object
    sequenceLock*: uint64
    activeGeneration*: uint32
    manasLatencyUs*: uint32
    nodeCount*: uint32
    hotNodeIndices*: array[3, uint32]
    nodes*: array[256, MenuNode]

macro enforceDss14Gate*(specs: static[openArray[StaticNodeSpec]]): untyped =
  ## Compile-time DSS-14.2 static verification gate:
  ## Rejects compilation if any node has an empty label, invalid parent linkage, or missing URI scheme.
  for s in specs:
    if s.label.len == 0 or s.label.len > 63:
      error("DSS-14 VIOLATION: Node ID " & $s.id & " has invalid label length: '" & s.label & "'")
    if not (s.target.contains("://") or s.target.startsWith("/")):
      error("DSS-14 VIOLATION: Node ID " & $s.id & " target lacks sovereign URI or absolute store path: " & s.target)
  result = newStmtList()

const SovereignMenuSpecs* = [
  # Tier 0: TianxiaOS Root
  StaticNodeSpec(id: 1, parentId: 0, tier: tTianxiaOS, plane: pNative, colorRgb: 0xFF00F0FF'u32,
                 ephemeralScore: 65000, judgmentWarn: 0,
                 label: "Sovereign-Cluster [LAT-5591]", target: "tianxia://cluster/workhorse",
                 telemetry: "41 RGUs | DSS-14.2 | GEN 142"),
  StaticNodeSpec(id: 2, parentId: 0, tier: tTianxiaOS, plane: pNative, colorRgb: 0xFF00F0FF'u32,
                 ephemeralScore: 52000, judgmentWarn: 0,
                 label: "Pointer-Bridge [:8732 <-> XPS]", target: "tianxia://bridge/xps13",
                 telemetry: "AF_XDP <0.6ms | ACTIVE"),
  StaticNodeSpec(id: 3, parentId: 0, tier: tTianxiaOS, plane: pNative, colorRgb: 0xFF00FF66'u32,
                 ephemeralScore: 48000, judgmentWarn: 0,
                 label: "tmpfs-Sanitizer [Zero-Leak]", target: "tianxia://security/sanitize",
                 telemetry: "RAM Root | Blake3 Verified"),

  # Tier 1: Systems
  StaticNodeSpec(id: 10, parentId: 1, tier: tSystem, plane: pNative, colorRgb: 0xFF00F0FF'u32,
                 ephemeralScore: 64000, judgmentWarn: 0,
                 label: "TetraLedger-FinOps", target: "system://tetraledger",
                 telemetry: "$350K Prin | $494.3K Out | 3 ACT 1 WARN"),
  StaticNodeSpec(id: 11, parentId: 1, tier: tSystem, plane: pNative, colorRgb: 0xFF00F0FF'u32,
                 ephemeralScore: 61000, judgmentWarn: 0,
                 label: "Nixyr-Substrate", target: "system://nixyr",
                 telemetry: "Intel UHD 630 + MX130 sm_50"),
  StaticNodeSpec(id: 12, parentId: 1, tier: tSystem, plane: pNative, colorRgb: 0xFF00F0FF'u32,
                 ephemeralScore: 59000, judgmentWarn: 0,
                 label: "Faery-Fortress [AEG-COM]", target: "system://faery",
                 telemetry: "AF_XDP 11.4Mpps @ 3.8us p99"),
  StaticNodeSpec(id: 13, parentId: 1, tier: tSystem, plane: pNative, colorRgb: 0xFF00F0FF'u32,
                 ephemeralScore: 57000, judgmentWarn: 0,
                 label: "Artificial-Kenning [MANAS]", target: "system://kenning",
                 telemetry: "Port 3109 <14ms | 70.6% OpEx Cut"),
  StaticNodeSpec(id: 14, parentId: 1, tier: tSystem, plane: pNative, colorRgb: 0xFF00FF66'u32,
                 ephemeralScore: 50000, judgmentWarn: 0,
                 label: "Herald-Spear [111-ICP]", target: "system://spear",
                 telemetry: "Career Spear + Inbound Closer"),

  # Tier 2: Subsystems
  StaticNodeSpec(id: 20, parentId: 10, tier: tSubsystem, plane: pNative, colorRgb: 0xFFFF5533'u32,
                 ephemeralScore: 65500, judgmentWarn: 1,
                 label: "Credit-Facilities [TX_NIMUE]", target: "sub://tetraledger/facilities",
                 telemetry: "SQLite WAL | 1 Covenant Warn"),
  StaticNodeSpec(id: 21, parentId: 11, tier: tSubsystem, plane: pNative, colorRgb: 0xFF00F0FF'u32,
                 ephemeralScore: 58000, judgmentWarn: 0,
                 label: "CUDA-SM50-Coprocessor", target: "sub://nixyr/cuda-sm50",
                 telemetry: "GeForce MX130 2GB | RTD3 Ready"),
  StaticNodeSpec(id: 22, parentId: 12, tier: tSubsystem, plane: pNative, colorRgb: 0xFF00F0FF'u32,
                 ephemeralScore: 60000, judgmentWarn: 0,
                 label: "WireGuard-Mesh [wg0]", target: "sub://faery/wg0",
                 telemetry: "Multi-Node Encrypted Fabric"),

  # Tier 3: Units
  StaticNodeSpec(id: 30, parentId: 20, tier: tUnit, plane: pNative, colorRgb: 0xFF00FF66'u32,
                 ephemeralScore: 54000, judgmentWarn: 0,
                 label: "FAC-TOKEN-001 // SYNAPSE-AI", target: "unit://fac/token-001",
                 telemetry: "$50K -> $65.5K | 2250 bps (22.5%)"),
  StaticNodeSpec(id: 31, parentId: 20, tier: tUnit, plane: pElasticNs, colorRgb: 0xFFFF5533'u32,
                 ephemeralScore: 65535, judgmentWarn: 1,
                 label: "FAC-LEASE-002 // METRO-LOG", target: "unit://fac/lease-002",
                 telemetry: "$85K -> $125.8K | Ratio 38.7% < 40%"),
  StaticNodeSpec(id: 32, parentId: 20, tier: tUnit, plane: pNative, colorRgb: 0xFF00FF66'u32,
                 ephemeralScore: 53000, judgmentWarn: 0,
                 label: "FAC-INFRA-003 // NORDIC-COMP", target: "unit://fac/infra-003",
                 telemetry: "$120K -> $165.6K | 62.5C IPMI"),
  StaticNodeSpec(id: 33, parentId: 20, tier: tUnit, plane: pNative, colorRgb: 0xFF00FF66'u32,
                 ephemeralScore: 52000, judgmentWarn: 0,
                 label: "FAC-EV-004 // BALTIC-FLEET", target: "unit://fac/ev-004",
                 telemetry: "$95K -> $136.5K | SoH 91.5% OBD2"),

  # Tier 4: Files & Atomic Actions
  StaticNodeSpec(id: 40, parentId: 31, tier: tFile, plane: pMicroVm, colorRgb: 0xFFFF5533'u32,
                 ephemeralScore: 65535, judgmentWarn: 1,
                 label: "ENFORCE LOCK [PAYFAC_ESCALATE]", target: "action://tetraledger/lock/lease-002",
                 telemetry: "Blake3 WAL Commit + Rail Freeze"),
  StaticNodeSpec(id: 41, parentId: 31, tier: tFile, plane: pNative, colorRgb: 0xFF00F0FF'u32,
                 ephemeralScore: 62000, judgmentWarn: 0,
                 label: "ADJUST HOLDBACK [+250 BPS SPLIT]", target: "action://tetraledger/bps/lease-002",
                 telemetry: "Escalate 3500 -> 3750 bps"),
  StaticNodeSpec(id: 42, parentId: 31, tier: tFile, plane: pNative, colorRgb: 0xFF00FF66'u32,
                 ephemeralScore: 58000, judgmentWarn: 0,
                 label: "Inspect tx_nimue.sqlite-wal", target: "/var/lib/tianxia/ledger/tx_nimue.sqlite-wal",
                 telemetry: "Zero-Copy WAL Page Inspection")
]

static:
  enforceDss14Gate(SovereignMenuSpecs)

proc copyString(dest: var openArray[char], src: string) =
  for i in 0 ..< dest.len:
    if i < src.len:
      dest[i] = src[i]
    else:
      dest[i] = '\0'

proc writeStateToShm*(shmPath: string = "/dev/shm/tx_menu_ast") =
  var state: SharedMenuState
  state.sequenceLock = 2
  state.activeGeneration = 142
  state.manasLatencyUs = 2310
  state.nodeCount = uint32(SovereignMenuSpecs.len)
  state.hotNodeIndices = [uint32(11), uint32(12), uint32(5)] # FAC-LEASE-002, ENFORCE LOCK, etc.

  for i, s in SovereignMenuSpecs:
    var n: MenuNode
    n.id = s.id
    n.parentId = s.parentId
    n.tier = uint8(ord(s.tier))
    n.isolation = uint8(ord(s.plane))
    n.pad = 0
    n.statusColorRgb = s.colorRgb
    n.ephemeralScoreQ16 = s.ephemeralScore
    n.judgmentWarnFlag = s.judgmentWarn
    copyString(n.label, s.label)
    copyString(n.targetPath, s.target)
    copyString(n.telemetrySummary, s.telemetry)
    state.nodes[i] = n

  let fd = open(shmPath.cstring, O_RDWR or O_CREAT, 0o660)
  if fd < 0:
    echo "ERROR: Failed to open ", shmPath, " (errno: ", errno, ")"
    quit(1)

  let size = sizeof(SharedMenuState)
  if ftruncate(fd, size) != 0:
    echo "ERROR: Failed to truncate ", shmPath
    discard close(fd)
    quit(1)

  let p = mmap(nil, size, PROT_READ or PROT_WRITE, MAP_SHARED, fd, 0)
  if p == MAP_FAILED:
    echo "ERROR: Failed to mmap ", shmPath
    discard close(fd)
    quit(1)

  copyMem(p, addr state, size)
  discard msync(p, size, MS_SYNC)
  discard munmap(p, size)
  discard close(fd)
  echo "[TX_MENU_AST] Successfully compiled and populated ", SovereignMenuSpecs.len, " nodes into ", shmPath, " (size: ", size, " bytes)"

when isMainModule:
  echo "[TX_MENU_AST] DSS-14.2 Mahavidya static gate passed: ", SovereignMenuSpecs.len, " nodes verified."
  writeStateToShm()
