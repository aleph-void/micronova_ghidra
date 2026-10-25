// Runs the p-code semantic tests produced by emu_tests.py in Ghidra's p-code emulator.
// The program must be emu.bin imported raw at address 0.
// Script args: <tests.txt> <outfile>
//   tests.txt lines: <name> <start-hex> <stop-hex> <init|-> <expect>
//   init/expect items, comma separated: <reg>=<hex> or @<word-addr-hex>=<hex> (one 16-bit word).
//@category Testing

import java.io.PrintStream;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;

import ghidra.app.emulator.EmulatorHelper;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.lang.Register;

public class EmuCheck extends GhidraScript {

	@Override
	protected void run() throws Exception {
		String[] args = getScriptArgs();
		PrintStream out = new PrintStream(args[1]);
		int pass = 0, fail = 0;
		for (String line : Files.readAllLines(Path.of(args[0]))) {
			line = line.trim();
			if (line.isEmpty() || line.startsWith("#")) continue;
			String[] f = line.split("\\s+");
			String err = runOne(f);
			if (err == null) {
				pass++;
				out.println("PASS " + f[0]);
			}
			else {
				fail++;
				out.println("FAIL " + f[0] + ": " + err);
			}
		}
		out.printf("emulator tests: %d passed, %d failed%n", pass, fail);
		out.close();
	}

	// word address in the default (word-addressed) space
	private Address wa(long w) throws Exception {
		return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(w, true);
	}

	private String runOne(String[] f) throws Exception {
		Address start = wa(Long.parseUnsignedLong(f[1], 16));
		Address stop = wa(Long.parseUnsignedLong(f[2], 16));
		EmulatorHelper emu = new EmulatorHelper(currentProgram);
		try {
			for (String r : new String[] { "AC0", "AC1", "AC2", "AC3", "SP", "FP", "C", "ION", "MASK" }) {
				if (currentProgram.getRegister(r) != null) {
					emu.writeRegister(r, 0);
				}
			}
			emu.writeRegister("SP", 0x1000);
			if (!f[3].equals("-")) {
				for (String kv : f[3].split(",")) {
					String[] p = kv.split("=");
					long v = Long.parseUnsignedLong(p[1], 16);
					if (p[0].startsWith("@")) {
						emu.writeMemory(wa(Long.parseUnsignedLong(p[0].substring(1), 16)),
							new byte[] { (byte) (v >> 8), (byte) v });
					}
					else if (currentProgram.getRegister(p[0]) != null) {
						emu.writeRegister(p[0], BigInteger.valueOf(v));
					}
				}
			}
			emu.writeRegister(emu.getPCRegister(), start.getAddressableWordOffset());
			int steps = 0;
			while (!emu.getExecutionAddress().equals(stop) && steps < 1000) {
				if (!emu.step(monitor)) {
					return "emulation stopped at " + emu.getExecutionAddress() + ": " + emu.getLastError();
				}
				steps++;
			}
			if (!emu.getExecutionAddress().equals(stop)) {
				return "did not reach " + stop + " in 1000 steps (at " + emu.getExecutionAddress() + ")";
			}
			StringBuilder bad = new StringBuilder();
			for (String kv : f[4].split(",")) {
				String[] p = kv.split("=");
				BigInteger want = new BigInteger(p[1], 16);
				BigInteger got;
				if (p[0].startsWith("@")) {
					byte[] b = emu.readMemory(wa(Long.parseUnsignedLong(p[0].substring(1), 16)), 2);
					got = BigInteger.valueOf(((b[0] & 0xff) << 8) | (b[1] & 0xff));
				}
				else {
					Register r = currentProgram.getRegister(p[0]);
					if (r == null) {
						bad.append(" no register " + p[0]);
						continue;
					}
					BigInteger mask = BigInteger.ONE.shiftLeft(r.getBitLength()).subtract(BigInteger.ONE);
					want = want.and(mask);
					got = emu.readRegister(r).and(mask);
				}
				if (!want.equals(got)) bad.append(String.format(" %s=%x (want %x)", p[0], got, want));
			}
			return bad.length() == 0 ? null : bad.toString().trim();
		}
		finally {
			emu.dispose();
		}
	}
}
