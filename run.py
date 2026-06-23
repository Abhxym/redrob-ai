"""
CLI Interface for RedRob AI Recruiter
Usage: python run.py <jd_file.txt>
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from demo import RedRobRecruiter


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: python run.py <jd_file.txt>")
        print("\nExample:")
        print("  python run.py sample_jd.txt")
        sys.exit(1)
    
    jd_file = sys.argv[1]
    
    # Check file exists
    if not os.path.exists(jd_file):
        print(f"Error: File not found: {jd_file}")
        sys.exit(1)
    
    # Read JD
    with open(jd_file, 'r', encoding='utf-8') as f:
        jd_text = f.read()
    
    if not jd_text.strip():
        print(f"Error: JD file is empty: {jd_file}")
        sys.exit(1)
    
    # Extract JD ID from filename
    jd_id = os.path.splitext(os.path.basename(jd_file))[0]
    
    print(f"Processing JD: {jd_id}")
    print(f"File: {jd_file}\n")
    
    # Initialize and run
    recruiter = RedRobRecruiter()
    results = recruiter.run(jd_text, jd_id=jd_id, top_k=100, verbose=True)
    
    # Display top 10
    recruiter.print_top_candidates(results, top_n=10)
    
    print("\n✓ Pipeline complete!")
    print(f"Submission CSV: {results['submission_path']}")


if __name__ == "__main__":
    main()
