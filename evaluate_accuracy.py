import json
import time
from app.llm import interpret_operator_notes

def main():
    with open('test_data/bup_official_dataset', 'r') as f:
        data = json.load(f)

    cases = data.get('cases', [])
    total_cases = len(cases)
    correct_cases = 0

    print(f"Starting evaluation of {total_cases} cases...")
    
    for i, case in enumerate(cases):
        print(f"\n--- Case {i+1}/{total_cases}: {case['id']} ---")
        operator_notes = case['input']['operator_notes']
        expected = case['expected_output']['directive_interpretation']
        
        print("Notes:", operator_notes)
        
        try:
            # Call the LLM
            start = time.time()
            llm_result = interpret_operator_notes(operator_notes)
            elapsed = time.time() - start
            
            # Convert to dict for easier comparison
            actual = [intp.model_dump() for intp in llm_result.interpretations]
            
            # Check accuracy
            # We will compare directive_type, applies, and structured_adjustment
            case_passed = True
            for exp, act in zip(expected, actual):
                if exp['directive_type'] != act['directive_type']:
                    print(f"  [FAIL] Directive type mismatch: Expected {exp['directive_type']}, got {act['directive_type']}")
                    case_passed = False
                if exp['applies'] != act['applies']:
                    print(f"  [FAIL] 'applies' mismatch: Expected {exp['applies']}, got {act['applies']}")
                    case_passed = False
                
                exp_adj = exp.get('structured_adjustment')
                
                # Build act_adj from the flattened fields in LLMNoteInterpretation
                act_adj = None
                dtype = act['directive_type']
                if dtype == 'solar_reduction':
                    act_adj = {'hours': act.get('hours'), 'factor': act.get('factor')}
                elif dtype == 'minimum_battery_reserve':
                    act_adj = {'hours': act.get('hours'), 'minimum_energy_kwh': act.get('minimum_energy_kwh')}
                elif dtype in ['no_charge_window', 'no_discharge_window']:
                    act_adj = {'hours': act.get('hours')}
                elif dtype == 'max_grid_window':
                    act_adj = {'hours': act.get('hours'), 'max_grid_kwh': act.get('max_grid_kwh')}
                
                if exp_adj != act_adj:
                    print(f"  [FAIL] structured_adjustment mismatch:\n    Expected: {exp_adj}\n    Got: {act_adj}")
                    case_passed = False
            
            if case_passed:
                print(f"  [PASS] {case['id']} correct (took {elapsed:.1f}s)")
                correct_cases += 1
            
        except Exception as e:
            print(f"  [ERROR] LLM call failed for {case['id']}: {e}")
        
        if i < total_cases - 1:
            print("  Sleeping 1s...")
            time.sleep(1)

    print("\n==================================================")
    print(f"EVALUATION COMPLETE: {correct_cases}/{total_cases} correct ({(correct_cases/total_cases)*100:.1f}%)")
    print("==================================================")

if __name__ == '__main__':
    main()
