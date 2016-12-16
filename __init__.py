from binaryninja import *


# get the function where an address is in
def get_function_for(bv, address):
    function = bv.get_function_at(bv.platform, address)
    if function == None:
        function_address = bv.get_previous_function_start_before(address)
        function = bv.get_function_at(bv.platform, function_address)
    return function


#check if xref is a call
def is_xref_a_call(bv, xref):
    function = xref.function
    low_level_il = function.get_low_level_il_at(bv.platform.arch, xref.address)
    il = function.low_level_il[low_level_il]
    return il.operation_name == "LLIL_CALL"


def get_path_recursive(bv, function, db):
    if function.start not in db.keys():
        db[function.start] = {}

    for xref in bv.get_code_refs(function.start):
        if is_xref_a_call(bv, xref):
            if xref.function.start not in db[function.start].keys():
                db[function.start][xref.function.start] = []

            db[function.start][xref.function.start].append(xref)

    for function_address in db[function.start].keys():
        next_function = get_function_for(bv, function_address)
        get_path_recursive(bv, next_function, db)


def get_ordered_calls(bv, function, target_function, db, calls_list):
    for function_callme_address in db[function.start].keys():
        caller = get_function_for(bv, function_callme_address)
        get_ordered_calls(bv, caller, target_function, db, calls_list)
        xrefs = db[function.start][function_callme_address]
        calls_list.append([caller, function, xrefs])
        if function.start == target_function.start:
            calls_list.append([])
            

def print_calls(bv, calls_list):
    output = ''
    padlen = 0
    for entry in calls_list:
        if len(entry) > 0:
            caller, callee, xrefs = entry
            xrefs_formated = []
            for xref in xrefs:
                address = hex(xref.address).strip('L')
                if address not in xrefs_formated:
                    xrefs_formated.append(address)

            pad = " "*padlen
            output += "%s%s calls %s at: %s\n" %(pad, caller.name, callee.name, str(xrefs_formated))
            padlen += 2
        else:
            padlen = 0
            output += "\n"

    show_plain_text_report("Calls", output)


def get_call_path_to(bv, function):
    db = {}
    get_path_recursive(bv, function, db)    
    calls_list = []
    get_ordered_calls(bv, function, function, db, calls_list)
    print_calls(bv, calls_list)


def xref_call_finder(bv, function):
    get_call_path_to(bv, function)


PluginCommand.register_for_function("Xref Call Finder", "", xref_call_finder)



