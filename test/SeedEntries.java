// Pre-analysis script for raw images: disassemble at each given word address, make it a
// function and an external entry point, so auto-analysis has somewhere to start.
// Script args: <word-address> ...  (octal with a leading 0, hex with 0x, or decimal)
//@category Testing

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;

public class SeedEntries extends GhidraScript {

	@Override
	protected void run() throws Exception {
		for (String s : getScriptArgs()) {
			Address a = currentProgram.getAddressFactory().getDefaultAddressSpace()
				.getAddress(Long.decode(s), true);
			disassemble(a);
			createFunction(a, null);
			currentProgram.getSymbolTable().addExternalEntryPoint(a);
		}
	}
}
