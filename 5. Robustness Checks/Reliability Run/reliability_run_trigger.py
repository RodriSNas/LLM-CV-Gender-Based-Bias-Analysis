import subprocess
import time

for run_id in range(1, 6):
    print(f"Running reliability run {run_id}")
    subprocess.run(["python", "scoring_pipeline_reliability_run.py", "--run_id", str(run_id)])

    if run_id < 5:  # no need to wait after the last run
        print("Waiting 60 seconds before next run...")
        time.sleep(20)
