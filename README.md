> **Ghidra-Rare fork.** This branch adds tested fixes, release builds for the three newest Ghidra
> releases and test suites; see [GHIDRA-RARE.md](GHIDRA-RARE.md) for the test results and
> remaining gaps, and [CREDITS.md](CREDITS.md) for the original author and every change.
> Prebuilt zips for Ghidra 12.1.3, 12.1.4 and 12.2 are on this fork's
> [Releases page](https://github.com/aleph-void/micronova_ghidra/releases). The original README
> follows; the notes marked *Ghidra-Rare* were added.

# Micronova processor module for Ghidra

[![Sponsor Aleph Void](https://img.shields.io/badge/Sponsor-Aleph%20Void-EA4AAA?logo=githubsponsors&logoColor=white)](https://github.com/sponsors/aleph-void)

## Installing

- Download the zip file from the dist directory.

  *Ghidra-Rare:* the zip in `dist/` is the original build for Ghidra 11.3.1. For Ghidra 12.1.3,
  12.1.4 or 12.2 use the zip from the fork's [Releases page](https://github.com/aleph-void/micronova_ghidra/releases).

- Start Ghidra
- Menu File -> Install extensions
- Click the "+" icon, select the downloaded zip file, OK

## Using the extension
- File -> Import file, select a Micronova binary file
- Set options: 
    - Format: Raw binary
	- Language: Micronova default
	- Press Options button, set the address at which the file should be loaded
	
## Note:
In the extension, each address corresponds to a 16-bit word. However, when importing a file, the loading address in 
the "options" dialog is in bytes. In other words, if you want the file loaded at word-address 0100 (0x40), you need to set base address 0x80.

## Building the extension
~~Coming soon..~~

*Ghidra-Rare:* run `gradle buildExtension` with `GHIDRA_INSTALL_DIR` set to your Ghidra
installation; the zip is written to `dist/`.

## Processor (*Ghidra-Rare*)

The module is for the Data General microNOVA (mN601/mN602): the Nova instruction set plus the
microNOVA stack instructions (PSHA, POPA, SAV, RET, MTSP, MTFP, MFSP, MFFP), MUL/DIV, TRAP and
the microNOVA CPU and hand-held console I/O. Locations 1-3 hold the interrupt vectors and 47
(octal) the TRAP vector; `JSR` leaves the return address in AC3.

