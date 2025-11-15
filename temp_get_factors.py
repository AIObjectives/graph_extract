from pathlib import Path
import sys
import json
import src.utils as utils

# Establishing paths
scenarios_output_path = Path().resolve() / "scenarios"
print(scenarios_output_path)

for file in scenarios_output_path.iterdir():
    pass

