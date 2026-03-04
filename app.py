from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# -------------------------------
# Utility Functions
# -------------------------------

def to_32bit_binary(value):
    return format(value & 0xFFFFFFFF, '032b')

def group_binary(binary_str):
    return ' '.join(binary_str[i:i+4] for i in range(0, 32, 4))

# -------------------------------
# Error Diagnosis Module
# Pattern-based AI diagnosis for common RISC instruction errors

# -------------------------------
# Performance Metrics
# Global counters to track instruction execution statistics

metrics = {
    "total_instructions": 0,
    "stall_cycles": 0,
    "branch_mispredictions": 0
}


def reset_metrics():
    """Reset all performance counters to zero."""
    metrics["total_instructions"] = 0
    metrics["stall_cycles"] = 0
    metrics["branch_mispredictions"] = 0


def update_metrics(instruction, branch_taken=False, predicted_branch=None, stall=False):
    """
    Update global performance counters after each instruction.

    Args:
        instruction: instruction string executed
        branch_taken: True if BEQ resulted in a taken branch
        predicted_branch: Optional boolean prediction; if provided and differs
            from branch_taken, counts as a misprediction.
        stall: Boolean flag indicating whether a stall cycle occurred.
    """
    # increment instruction count
    metrics["total_instructions"] += 1

    # stall cycles
    if stall:
        metrics["stall_cycles"] += 1

    # branch misprediction logic
    if instruction == "BEQ" and predicted_branch is not None:
        if predicted_branch != (1 if branch_taken else 0):
            metrics["branch_mispredictions"] += 1


def compute_derived_metrics():
    """Calculate cycles, CPI, IPC, and throughput based on current counters."""
    instr = metrics["total_instructions"]
    stalls = metrics["stall_cycles"]

    # for a 5-stage pipeline: total cycles = instructions + 4 + stall cycles
    total_cycles = instr + 4 + stalls

    cpi = total_cycles / instr if instr > 0 else 0
    ipc = instr / total_cycles if total_cycles > 0 else 0
    throughput = ipc

    return {
        "total_instructions": instr,
        "total_cycles": total_cycles,
        "stall_cycles": stalls,
        "branch_mispredictions": metrics["branch_mispredictions"],
        "cpi": cpi,
        "ipc": ipc,
        "throughput": throughput
    }

# -------------------------------
# Error Diagnosis Module
# Pattern-based AI diagnosis for common RISC instruction errors

def diagnose_error(instruction, rs, rt, simulator_result, current_pc=None):
    """
    Diagnose common errors in RISC instruction execution.
    
    Detects pattern-based mistakes and identifies probable pipeline stage of error.
    
    Args:
        instruction: The RISC instruction (ADD, SUB, AND, OR, SLT, BEQ)
        rs: Source register 1 value
        rt: Source register 2 value
        simulator_result: The result computed by the simulator
        current_pc: Optional program counter value
    
    Returns:
        Dictionary with:
            - expected_result: Correct result value
            - status: "Correct" or "Incorrect"
            - diagnosis: Human-readable explanation with pipeline stage hint
    """
    
    # Step 1: Compute expected result based on instruction type
    expected_result = None
    
    if instruction == "ADD":
        expected_result = rs + rt
    elif instruction == "SUB":
        expected_result = rs - rt
    elif instruction == "AND":
        expected_result = rs & rt
    elif instruction == "OR":
        expected_result = rs | rt
    elif instruction == "SLT":
        expected_result = 1 if rs < rt else 0
    elif instruction == "BEQ":
        # For BEQ, result indicates if branch should be taken (1=taken, 0=not taken)
        expected_result = 1 if rs == rt else 0
    else:
        return {
            "expected_result": None,
            "status": "Unknown",
            "diagnosis": f"Unknown instruction: {instruction}"
        }
    
    # Step 2: Compare results
    if simulator_result == expected_result:
        return {
            "expected_result": expected_result,
            "status": "Correct",
            "diagnosis": f"✓ {instruction} executed correctly. Pipeline: IF → ID → EX ✓ → MEM → WB"
        }
    
    # Step 3: Error detected - identify pattern
    diagnosis = f"Instruction: {instruction} | Expected: {expected_result} | Got: {simulator_result}\n"
    pipeline_stage = "EX"  # Most errors occur in Execute stage
    
    # Pattern matching for common mistakes
    if instruction == "ADD":
        if simulator_result == rs - rt:
            diagnosis += "Pattern Match: SUB logic used instead of ADD (left operand - right operand detected)."
            pipeline_stage = "EX"
        elif simulator_result == rs & rt:
            diagnosis += "Pattern Match: AND logic used instead of ADD (bitwise AND detected)."
            pipeline_stage = "EX"
        elif simulator_result == rs:
            diagnosis += "Pattern Match: Result equals only rs. rt operand not factored in."
            pipeline_stage = "ID"  # Register read error
        elif simulator_result == rt:
            diagnosis += "Pattern Match: Result equals only rt. rs operand not factored in."
            pipeline_stage = "ID"  # Register read error
        elif simulator_result == 0:
            diagnosis += "Pattern Match: Result is zero. Possible register read failure or forwarding issue."
            pipeline_stage = "EX/ID"
        else:
            diagnosis += "Pattern: Unexpected ADD result value."
            pipeline_stage = "EX"
    
    elif instruction == "SUB":
        if simulator_result == rs + rt:
            diagnosis += "Pattern Match: ADD logic used instead of SUB (addition detected)."
            pipeline_stage = "EX"
        elif simulator_result == rs:
            diagnosis += "Pattern Match: Result equals only rs. rt operand not subtracted."
            pipeline_stage = "ID"  # Register read or ALU routing error
        elif simulator_result == 0:
            diagnosis += "Pattern Match: Result is zero. Possible register read failure or forwarding issue."
            pipeline_stage = "EX/ID"
        else:
            diagnosis += "Pattern: Unexpected SUB result value."
            pipeline_stage = "EX"
    
    elif instruction == "AND":
        if simulator_result == rs:
            diagnosis += "Pattern Match: Result equals only rs. rt operand not applied in AND operation."
            pipeline_stage = "ID"
        elif simulator_result == 0:
            diagnosis += "Pattern Match: Result is zero. Possible register read failure or AND gate issue."
            pipeline_stage = "EX/ID"
        else:
            diagnosis += "Pattern: Unexpected AND result value."
            pipeline_stage = "EX"
    
    elif instruction == "OR":
        if simulator_result == rs:
            diagnosis += "Pattern Match: Result equals only rs. rt operand not applied in OR operation."
            pipeline_stage = "ID"
        elif simulator_result == 0:
            diagnosis += "Pattern Match: Result is zero. Possible register read failure or OR gate issue."
            pipeline_stage = "EX/ID"
        else:
            diagnosis += "Pattern: Unexpected OR result value."
            pipeline_stage = "EX"
    
    elif instruction == "SLT":
        if simulator_result not in [0, 1]:
            diagnosis += "Pattern: SLT result must be 0 or 1 (boolean). Invalid value used."
            pipeline_stage = "EX"
        else:
            # Check for reversed condition
            if (rs < rt and simulator_result == 0) or (rs >= rt and simulator_result == 1):
                diagnosis += "Pattern Match: SLT condition appears reversed (inverted comparison logic)."
                pipeline_stage = "EX"
            else:
                diagnosis += "Pattern: Unexpected SLT comparison result."
                pipeline_stage = "EX"
    
    elif instruction == "BEQ":
        # Check for reversed branch condition
        if (rs == rt and simulator_result == 0) or (rs != rt and simulator_result == 1):
            diagnosis += "Pattern Match: BEQ condition reversed (branch taken when should not be)."
            pipeline_stage = "EX"
        else:
            diagnosis += "Pattern: Unexpected BEQ comparison result."
            pipeline_stage = "EX"
    
    diagnosis += f"\n→ Error likely in {pipeline_stage} stage"
    
    return {
        "expected_result": expected_result,
        "status": "Incorrect",
        "diagnosis": diagnosis
    }

# -------------------------------
# Machine Code Generator
def generate_machine_code(operation, rs, rt):
    rs_bin = format(rs & 0x1F, '05b')
    rt_bin = format(rt & 0x1F, '05b')
    rd_bin = "00000"  # For now, hardcode rd to 0
    shamt = "00000"
    
    opcode = "000000"  # default R-type opcode
    funct_map = {
        "ADD": "100000",
        "SUB": "100010",
        "AND": "100100",
        "OR" : "100101",
        "SLT": "101010"
    }
    
    if operation in funct_map:  # R-type
        funct = funct_map[operation]
        machine_code = opcode + rs_bin + rt_bin + rd_bin + shamt + funct
    elif operation == "BEQ":  # I-type
        opcode = "000100"
        immediate = "0000000000000000"  # placeholder
        machine_code = opcode + rs_bin + rt_bin + immediate
    else:
        machine_code = "0" * 32
    
    return machine_code

# -------------------------------
# Page Routes

@app.route('/')
def splash():
    return render_template('splash.html')

@app.route('/landing')
def landing():
    return render_template('landing.html')

@app.route('/execution')
def execution():
    return render_template('execution.html')

@app.route('/simulator')
def simulator():
    return render_template('index.html')   # Your simulator page


@app.route('/results')
def results():
    """Display results page - data passed via sessionStorage from frontend."""
    return render_template('results.html')


@app.route('/simulate', methods=['POST'])
def simulate():
    data = request.json

    # Correct key from JS
    operation = data.get('operation')
    rs = int(data.get('rs', 0))
    rt = int(data.get('rt', 0))

    result = 0
    branch_taken = False
    overflow = False

    try:
        if operation == "ADD":
            result = rs + rt
        elif operation == "SUB":
            result = rs - rt
        elif operation == "AND":
            result = rs & rt
        elif operation == "OR":
            result = rs | rt
        elif operation == "SLT":
            result = 1 if rs < rt else 0
        elif operation == "BEQ":
            branch_taken = (rs == rt)
            result = 0
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    zero_flag = (result == 0)
    machine_code = generate_machine_code(operation, rs, rt)

    # optional metrics flags from frontend
    predicted_branch = data.get('predicted_branch', None)
    stall = data.get('stall', False)

    # update global performance counters
    update_metrics(operation, branch_taken, predicted_branch, stall)
    metrics_data = compute_derived_metrics()
    
    # Integrate error diagnosis
    diagnosis_result = diagnose_error(operation, rs, rt, result)

    return jsonify({
        # Pipeline stage messages
        "IF": "Instruction Fetched",
        "ID": f"Operands: {rs}, {rt}",
        "EX": f"Executed {operation}",
        "MEM": "Memory Access",
        "WB": "Write Back",

        # ALU results
        "result_decimal": result,
        "result_binary": group_binary(to_32bit_binary(result)),
        "machine_code": machine_code,

        "rs_binary": group_binary(to_32bit_binary(rs)),
        "rt_binary": group_binary(to_32bit_binary(rt)),

        "zero_flag": zero_flag,
        "branch_taken": branch_taken,
        "overflow": overflow,

        # Error Diagnosis
        "expected_result": diagnosis_result["expected_result"],
        "diagnosis_status": diagnosis_result["status"],
        "diagnosis": diagnosis_result["diagnosis"],

        # Performance metrics
        **metrics_data
    })


# -------------------------------
# Metrics Reset Route

@app.route('/reset_metrics', methods=['POST'])
def reset_metrics_route():
    """Endpoint to reset performance counters."""
    reset_metrics()
    return jsonify(compute_derived_metrics())

# -------------------------------
# Run App

if __name__ == '__main__':
    app.run(debug=True)