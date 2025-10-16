
import os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(__file__))
def run(p): print(">>", p); r = subprocess.run([sys.executable, p], cwd=ROOT); r.check_returncode()
def main():
    run("src/fetch_fed_events.py")
    run("src/fetch_market_free.py")
    run("src/analysis.py")
    run("src/plots.py")
    print("finished, check outputs folder")
if __name__ == "__main__":
    main()
