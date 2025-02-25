import argparse
import os
import sys
from step_parser import StepParser
from comparison_engine import ComparisonEngine
from report_generator import ReportGenerator

def main():
    parser = argparse.ArgumentParser(description='Compare two STEP-AP242 files')
    parser.add_argument('file1', help='Path to the first STEP file')
    parser.add_argument('file2', help='Path to the second STEP file')
    parser.add_argument('--output', '-o', help='Output directory for reports')
    parser.add_argument('--format', '-f', choices=['text', 'json', 'html', 'csv', 'all'],
                        default='text', help='Output format (default: text)')
    
    args = parser.parse_args()
    
    # Validate input files
    if not os.path.exists(args.file1):
        print(f"Error: File not found: {args.file1}")
        return 1
    
    if not os.path.exists(args.file2):
        print(f"Error: File not found: {args.file2}")
        return 1
    
    # Create output directory if it doesn't exist
    if args.output and not os.path.exists(args.output):
        os.makedirs(args.output)
    
    try:
        # Parse STEP files
        print(f"Parsing file 1: {args.file1}")
        parser = StepParser()
        data1 = parser.parse(args.file1)
        
        print(f"Parsing file 2: {args.file2}")
        parser = StepParser()
        data2 = parser.parse(args.file2)
        
        # Compare the files
        print("Comparing files...")
        engine = ComparisonEngine()
        differences = engine.compare(data1, data2)
        
        # Generate reports
        print("Generating reports...")
        generator = ReportGenerator(differences, args.file1, args.file2)
        
        if args.format in ['text', 'all']:
            output_path = None
            if args.output:
                output_path = os.path.join(args.output, 'comparison_report.txt')
            report = generator.generate_text_report(output_path)
            if not args.output:
                print("\n" + report)
        
        if args.format in ['json', 'all']:
            if args.output:
                output_path = os.path.join(args.output, 'comparison_report.json')
                generator.generate_json_report(output_path)
        
        if args.format in ['html', 'all']:
            if args.output:
                output_path = os.path.join(args.output, 'comparison_report.html')
                generator.generate_html_report(output_path)
        
        if args.format in ['csv', 'all']:
            if args.output:
                output_path = os.path.join(args.output, 'comparison_report.csv')
                generator.generate_csv_report(output_path)
        
        print("Comparison completed successfully.")
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 