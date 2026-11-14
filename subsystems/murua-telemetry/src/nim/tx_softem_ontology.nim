# ffp: FFP-MURUA-NIM edge-agent nim
## TianxiaOS / Murua Nim Symbolic AST Grammar & Postal Ontology Gate
## Fast System-1 constraint evaluation under 10ms.

type
  CarrierRule* = object
    carrier*: string
    hasBarcode*: bool
    hasEdi*: bool
    claimsLockerDelivery*: bool
    claimsSmsPin*: bool

proc validateRule*(rule: CarrierRule): bool =
  # Strict FAOS Rule: Unbarcoded post without EDI hook CANNOT inject into parcel lockers
  if not rule.hasBarcode and not rule.hasEdi:
    if rule.claimsLockerDelivery or rule.claimsSmsPin:
      return false
  return true

proc main() =
  echo "=== [NIM] Murua Symbolic Ontology & AST Validator ==="

  let invalidRule = CarrierRule(
    carrier: "Omniva",
    hasBarcode: false,
    hasEdi: false,
    claimsLockerDelivery: true,
    claimsSmsPin: true
  )

  let validRule = CarrierRule(
    carrier: "Omniva",
    hasBarcode: true,
    hasEdi: true,
    claimsLockerDelivery: true,
    claimsSmsPin: true
  )

  let res1 = validateRule(invalidRule)
  let res2 = validateRule(validRule)

  echo "Rule 1 (Untracked -> Locker OCR): Valid = ", res1, " (Rejected as Hallucination: ", not res1, ")"
  echo "Rule 2 (S10 Tracked -> Locker):   Valid = ", res2, " (Accepted: ", res2, ")"

  if not res1 and res2:
    echo "=== [NIM] All Symbolic Ontology Tests PASSED ==="
  else:
    echo "[!] [NIM] Validation FAILURE"
    quit(1)

when isMainModule:
  main()
