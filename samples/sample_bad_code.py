# Demo semua antipattern — dipakai oleh main.py (CLI)
g_counter = 0

def p(a, b, c, d, e, f, lst=[]):
    global g_counter
    g_counter += 1
    try:
        for item in a:
            if item:
                for sub in item:
                    if sub > 0:
                        if sub < 100:
                            if len(lst) < 50:
                                lst.append(sub * 365)
                                print("Added:", sub)
    except:
        pass
    for x in b:
        if x > 0:
            for y in c:
                if y < 0:
                    for z in d:
                        if z == 0:
                            print("zero")

def q(a, b, c, d, e, f, lst=[]):
    global g_counter
    g_counter += 1
    try:
        for item in a:
            if item:
                for sub in item:
                    if sub > 0:
                        if sub < 100:
                            if len(lst) < 50:
                                lst.append(sub * 365)
                                print("Added:", sub)
    except:
        pass
