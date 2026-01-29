import subprocess
import sys
import typer

def run_wrapper_range(filename, start_id, end_id):
    """
    Run wrapper.py for a range of scenario_ids
    
    Args:
        filename: The filename to pass to wrapper.py
        start_id: Starting scenario_id (inclusive)
        end_id: Ending scenario_id (inclusive)
    """
    # set to python venv called 'AOIgraphextractMAC' in current directory
    python_cmd = r'AOIgraphextractMAC/bin/python3'

    for scenario_id in range(start_id, end_id + 1):
        print(f"Running wrapper.py with filename='{filename}' and scenario_id={scenario_id}")
        
        try:
            result = subprocess.run(
                [python_cmd, 'wrapper.py', '--filename', filename, '--scenario-id', str(scenario_id)],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"✓ Completed scenario_id {scenario_id}")
            if result.stdout:
                print(result.stdout)
                
        except subprocess.CalledProcessError as e:
            print(f"✗ Error with scenario_id {scenario_id}")
            print(f"Error message: {e.stderr}")
            # You can choose to continue or stop on error
            # raise  # Uncomment to stop on first error

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python run_range.py <filename> <start_id> <end_id>")
        print("Example: python run_range.py data.csv 5 15")
        sys.exit(1)
    
    filename = sys.argv[1]
    start_id = int(sys.argv[2])
    end_id = int(sys.argv[3])
    
    run_wrapper_range(filename, start_id, end_id)
    print(f"\nAll done! Ran scenarios {start_id} through {end_id}")