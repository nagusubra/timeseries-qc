import json
nb = json.load(open("oilfield_executed.ipynb"))
for i, c in enumerate(nb["cells"]):
    status = "OK" if c.get("execution_count") else "no exec"
    err = ""
    for out in c.get("outputs", []):
        if out.get("output_type") == "error":
            err = " ERROR: " + out.get("ename", "")
    print(f"Cell {i+1} ({c['cell_type']}): {status}{err}")
