// ffp: FFP-ACPI-DELL-BRT6 declarative asl
// Dell Latitude 5591 DSDT \_SB.PCI0.PEG0.PEGP.BRT6 AE_NOT_FOUND Remediation SSDT
// Defines missing \_SB.PCI0.PEG0.PEGP.LCD device node so EC _Q66 -> NEVT -> SMIE -> SMEE -> EV5
// completes cleanly without aborting brightness & Dell WMI hotkey dispatch.
DefinitionBlock ("", "SSDT", 2, "TIANXI", "PEGLCDFX", 0x00000001)
{
    External (\_SB_.PCI0.PEG0.PEGP, DeviceObj)

    Scope (\_SB.PCI0.PEG0.PEGP)
    {
        Device (LCD)
        {
            Name (_ADR, 0x0110)
        }
    }
}
