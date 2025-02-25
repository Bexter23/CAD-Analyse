import json
import csv
import os
from datetime import datetime
import pdfkit
import tempfile
import logging

logger = logging.getLogger(__name__)

class ReportGenerator:
    def __init__(self, differences, file1_name, file2_name):
        self.differences = differences
        self.file1_name = os.path.basename(file1_name)
        self.file2_name = os.path.basename(file2_name)
        self.timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    def generate_text_report(self, output_path=None):
        """Generate a text-based report of the differences"""
        report = []
        
        # Add header
        report.append("=== STEP-AP242 Comparison Report ===")
        report.append(f"File 1: {self.file1_name}")
        report.append(f"File 2: {self.file2_name}")
        report.append(f"Generated: {self.timestamp}")
        report.append("\n")
        
        # Add structural differences
        report.append("--- Structural Comparison ---")
        
        # Entity differences
        entity_diffs = self.differences['structural']['entity_differences']
        report.append("\nEntity Type Differences:")
        
        if entity_diffs['only_in_file1']:
            report.append("  - Only in File 1:")
            for entity, count in entity_diffs['only_in_file1'].items():
                report.append(f"      - {entity} (Count: {count})")
        
        if entity_diffs['only_in_file2']:
            report.append("  - Only in File 2:")
            for entity, count in entity_diffs['only_in_file2'].items():
                report.append(f"      - {entity} (Count: {count})")
        
        if entity_diffs['count_differences']:
            report.append("  - Count Difference (Significant > 10% difference):")
            for entity, diff in entity_diffs['count_differences'].items():
                report.append(f"      - {entity}: File 1 (Count: {diff['file1']}), "
                             f"File 2 (Count: {diff['file2']})  ({diff['change']} in File 2)")
        
        # Relationship differences
        # ... similar implementation for relationships
        
        # PMI differences
        report.append("\n--- PMI Comparison ---")
        # ... implementation for PMI differences
        
        # Attribute differences
        report.append("\n--- Attribute Comparison ---")
        # ... implementation for attribute differences
        
        # Summary
        report.append("\n--- Summary ---")
        # ... implementation for summary
        
        # Write to file if output path is provided
        if output_path:
            with open(output_path, 'w') as f:
                f.write('\n'.join(report))
        
        return '\n'.join(report)
    
    def generate_json_report(self, output_path=None):
        """Generate a JSON report of the differences"""
        report = {
            'metadata': {
                'file1': self.file1_name,
                'file2': self.file2_name,
                'timestamp': self.timestamp
            },
            'differences': self.differences
        }
        
        # Write to file if output path is provided
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
        
        return report
    
    def _format_number(self, number, precision=2):
        """Format a number with the specified precision"""
        return f"{number:.{precision}f}"

    def generate_html_report(self, output_path=None):
        """Generate an HTML report of the differences"""
        html = []
        
        # Add HTML header
        html.append('<!DOCTYPE html>')
        html.append('<html lang="en">')
        html.append('<head>')
        html.append('    <meta charset="UTF-8">')
        html.append('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
        html.append('    <title>STEP-AP242 Comparison Report</title>')
        html.append('    <style>')
        html.append('        body { font-family: Arial, sans-serif; margin: 20px; }')
        html.append('        h1 { color: #2c3e50; }')
        html.append('        h2 { color: #3498db; margin-top: 30px; }')
        html.append('        h3 { color: #2980b9; }')
        html.append('        .metadata { background-color: #f8f9fa; padding: 10px; border-radius: 5px; }')
        html.append('        .section { margin-bottom: 30px; }')
        html.append('        table { border-collapse: collapse; width: 100%; }')
        html.append('        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }')
        html.append('        th { background-color: #f2f2f2; }')
        html.append('        tr:nth-child(even) { background-color: #f9f9f9; }')
        html.append('        .added { background-color: #d4edda; }')
        html.append('        .removed { background-color: #f8d7da; }')
        html.append('        .changed { background-color: #fff3cd; }')
        html.append('        .summary { font-weight: bold; }')
        html.append('        .metric-card { border-left: 4px solid #3498db; padding: 10px; margin-bottom: 15px; background-color: #f8f9fa; }')
        html.append('        .metric-value { font-size: 18px; font-weight: bold; color: #3498db; }')
        html.append('        .metric-label { color: #7f8c8d; font-size: 14px; }')
        html.append('        .metric-diff { font-size: 14px; color: #e74c3c; }')
        html.append('        .metric-row { display: flex; flex-wrap: wrap; gap: 20px; }')
        html.append('        .similarity-score { font-size: 24px; font-weight: bold; text-align: center; margin: 20px 0; }')
        html.append('        .similarity-high { color: #27ae60; }')
        html.append('        .similarity-medium { color: #f39c12; }')
        html.append('        .similarity-low { color: #e74c3c; }')
        html.append('    </style>')
        html.append('</head>')
        html.append('<body>')
        
        # Add report header
        html.append('    <h1>STEP-AP242 Comparison Report</h1>')
        html.append('    <div class="metadata">')
        html.append(f'        <p><strong>File 1:</strong> {self.file1_name}</p>')
        html.append(f'        <p><strong>File 2:</strong> {self.file2_name}</p>')
        html.append(f'        <p><strong>Generated:</strong> {self.timestamp}</p>')
        html.append('    </div>')
        
        # Add similarity score
        similarity_score = self.differences['summary']['similarity_score']
        similarity_class = 'similarity-high' if similarity_score >= 80 else ('similarity-medium' if similarity_score >= 50 else 'similarity-low')
        html.append(f'    <div class="similarity-score {similarity_class}">')
        html.append(f'        Similarity Score: {self._format_number(similarity_score)}%')
        html.append('    </div>')
        
        # Add geometric comparison
        html.append('    <div class="section">')
        html.append('        <h2>Geometric Comparison</h2>')
        
        # Volume comparison
        html.append('        <div class="metric-row">')
        
        # Volume
        vol_data = self.differences['geometric']['volume']
        html.append('            <div class="metric-card">')
        html.append('                <div class="metric-label">Volume</div>')
        html.append(f'                <div class="metric-value">{self._format_number(vol_data["file1"])} mm³ vs {self._format_number(vol_data["file2"])} mm³</div>')
        html.append(f'                <div class="metric-diff">Difference: {self._format_number(vol_data["difference"])} mm³ ({self._format_number(vol_data["percentage"])}%)</div>')
        html.append('            </div>')
        
        # Surface Area
        area_data = self.differences['geometric']['surface_area']
        html.append('            <div class="metric-card">')
        html.append('                <div class="metric-label">Surface Area</div>')
        html.append(f'                <div class="metric-value">{self._format_number(area_data["file1"])} mm² vs {self._format_number(area_data["file2"])} mm²</div>')
        html.append(f'                <div class="metric-diff">Difference: {self._format_number(area_data["difference"])} mm² ({self._format_number(area_data["percentage"])}%)</div>')
        html.append('            </div>')
        
        html.append('        </div>')
        
        # Center of Mass and Bounding Box
        html.append('        <div class="metric-row">')
        
        # Center of Mass
        com_data = self.differences['geometric']['center_of_mass']
        html.append('            <div class="metric-card">')
        html.append('                <div class="metric-label">Center of Mass</div>')
        html.append(f'                <div class="metric-value">File 1: [{self._format_number(com_data["file1"][0])}, {self._format_number(com_data["file1"][1])}, {self._format_number(com_data["file1"][2])}]</div>')
        html.append(f'                <div class="metric-value">File 2: [{self._format_number(com_data["file2"][0])}, {self._format_number(com_data["file2"][1])}, {self._format_number(com_data["file2"][2])}]</div>')
        html.append(f'                <div class="metric-diff">Distance: {self._format_number(com_data["distance"])} mm</div>')
        html.append('            </div>')
        
        # Bounding Box
        bbox_data = self.differences['geometric']['bounding_box']
        html.append('            <div class="metric-card">')
        html.append('                <div class="metric-label">Bounding Box</div>')
        html.append(f'                <div class="metric-value">File 1: {self._format_number(bbox_data["file1"]["dimensions"][0])} × {self._format_number(bbox_data["file1"]["dimensions"][1])} × {self._format_number(bbox_data["file1"]["dimensions"][2])} mm</div>')
        html.append(f'                <div class="metric-value">File 2: {self._format_number(bbox_data["file2"]["dimensions"][0])} × {self._format_number(bbox_data["file2"]["dimensions"][1])} × {self._format_number(bbox_data["file2"]["dimensions"][2])} mm</div>')
        html.append(f'                <div class="metric-diff">Volume Difference: {self._format_number(bbox_data["difference"])} mm³ ({self._format_number(bbox_data["percentage"])}%)</div>')
        html.append('            </div>')
        
        html.append('        </div>')
        
        html.append('    </div>')
        
        # Add structural differences
        html.append('    <div class="section">')
        html.append('        <h2>Structural Comparison</h2>')
        
        # Entity differences
        html.append('        <h3>Entity Type Differences</h3>')
        entity_diffs = self.differences['structural']['entity_differences']
        
        if entity_diffs['only_in_file1'] or entity_diffs['only_in_file2'] or entity_diffs['count_differences']:
            html.append('        <table>')
            html.append('            <tr><th>Entity Type</th><th>File 1</th><th>File 2</th><th>Status</th></tr>')
            
            # Entities only in file 1
            for entity, count in entity_diffs['only_in_file1'].items():
                html.append(f'            <tr class="removed"><td>{entity}</td><td>{count}</td><td>-</td><td>Only in File 1</td></tr>')
            
            # Entities only in file 2
            for entity, count in entity_diffs['only_in_file2'].items():
                html.append(f'            <tr class="added"><td>{entity}</td><td>-</td><td>{count}</td><td>Only in File 2</td></tr>')
            
            # Entities with count differences
            for entity, diff in entity_diffs['count_differences'].items():
                html.append(f'            <tr class="changed"><td>{entity}</td><td>{diff["file1"]}</td><td>{diff["file2"]}</td><td>{diff["change"]} in File 2</td></tr>')
            
            html.append('        </table>')
        else:
            html.append('        <p>No entity differences found.</p>')
        
        # Relationship differences
        html.append('        <h3>Relationship Differences</h3>')
        # ... similar implementation for relationships
        
        html.append('    </div>')
        
        # PMI differences
        html.append('    <div class="section">')
        html.append('        <h2>PMI Comparison</h2>')
        # ... implementation for PMI differences
        html.append('    </div>')
        
        # Attribute differences
        html.append('    <div class="section">')
        html.append('        <h2>Attribute Comparison</h2>')
        # ... implementation for attribute differences
        html.append('    </div>')
        
        # Summary
        html.append('    <div class="section">')
        html.append('        <h2>Summary</h2>')
        
        summary = self.differences['summary']
        html.append('        <div class="metric-row">')
        
        html.append('            <div class="metric-card">')
        html.append('                <div class="metric-label">Total Differences</div>')
        html.append(f'                <div class="metric-value">{summary["total_differences"]}</div>')
        html.append('            </div>')
        
        html.append('            <div class="metric-card">')
        html.append('                <div class="metric-label">Structural Differences</div>')
        html.append(f'                <div class="metric-value">{summary["structural_differences"]}</div>')
        html.append('            </div>')
        
        html.append('            <div class="metric-card">')
        html.append('                <div class="metric-label">PMI Differences</div>')
        html.append(f'                <div class="metric-value">{summary["pmi_differences"]}</div>')
        html.append('            </div>')
        
        html.append('            <div class="metric-card">')
        html.append('                <div class="metric-label">Attribute Differences</div>')
        html.append(f'                <div class="metric-value">{summary["attribute_differences"]}</div>')
        html.append('            </div>')
        
        html.append('            <div class="metric-card">')
        html.append('                <div class="metric-label">Geometric Differences</div>')
        html.append(f'                <div class="metric-value">{summary["geometric_differences"]}</div>')
        html.append('            </div>')
        
        html.append('        </div>')
        
        html.append('    </div>')
        
        # Close HTML tags
        html.append('</body>')
        html.append('</html>')
        
        # Write to file if output path is provided
        if output_path:
            with open(output_path, 'w') as f:
                f.write('\n'.join(html))
        
        # For embedding in another template, return just the content part
        content_start = html.index('    <h1>STEP-AP242 Comparison Report</h1>')
        content_end = html.index('</body>')
        return '\n'.join(html[content_start:content_end])
    
    def generate_pdf_report(self, output_path=None):
        """Generate a PDF report of the differences using reportlab"""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            
            # Create PDF document
            if not output_path:
                output_path = f"comparison_report_{self.timestamp}.pdf"
            
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []
            
            # Add title
            title_style = styles['Heading1']
            elements.append(Paragraph("STEP-AP242 Comparison Report", title_style))
            elements.append(Spacer(1, 12))
            
            # Add metadata
            elements.append(Paragraph(f"File 1: {self.file1_name}", styles['Normal']))
            elements.append(Paragraph(f"File 2: {self.file2_name}", styles['Normal']))
            elements.append(Paragraph(f"Generated: {self.timestamp}", styles['Normal']))
            elements.append(Spacer(1, 12))
            
            # Add similarity score
            similarity_score = self.differences['summary']['similarity_score']
            elements.append(Paragraph(f"Similarity Score: {self._format_number(similarity_score)}%", styles['Heading2']))
            elements.append(Spacer(1, 12))
            
            # Add geometric comparison
            elements.append(Paragraph("Geometric Comparison", styles['Heading2']))
            
            # Build the document
            doc.build(elements)
            logger.info(f"PDF report generated at {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}")
            return None
    
    def generate_csv_report(self, output_path=None):
        """Generate a CSV report of the differences"""
        try:
            # Prepare CSV data
            csv_data = []
            
            # Add metadata
            csv_data.append(['Comparison Information', '', ''])
            csv_data.append(['File 1', self.file1_name, ''])
            csv_data.append(['File 2', self.file2_name, ''])
            csv_data.append(['Comparison Date', self.timestamp, ''])
            csv_data.append(['', '', ''])
            
            # Add summary
            summary = self.differences.get('summary', {})
            csv_data.append(['Summary', '', ''])
            csv_data.append(['Similarity Score', f"{self._format_number(summary.get('similarity_score', 0))}%", ''])
            csv_data.append(['Total Differences', summary.get('total_differences', 0), ''])
            csv_data.append(['Structural Differences', summary.get('structural_differences', 0), ''])
            csv_data.append(['Geometric Differences', summary.get('geometric_differences', 0), ''])
            csv_data.append(['PMI Differences', summary.get('pmi_differences', 0), ''])
            csv_data.append(['Attribute Differences', summary.get('attribute_differences', 0), ''])
            csv_data.append(['', '', ''])
            
            # Add geometric differences
            geometric = self.differences.get('geometric', {})
            if geometric:
                csv_data.append(['Geometric Differences', '', ''])
                
                # Volume
                volume1 = geometric.get('volume', {}).get('file1', 0)
                volume2 = geometric.get('volume', {}).get('file2', 0)
                volume_diff = geometric.get('volume', {}).get('difference', 0)
                volume_percent = geometric.get('volume', {}).get('percent_difference', 0)
                
                csv_data.append(['Volume', '', ''])
                csv_data.append(['', 'File 1', 'File 2', 'Difference', 'Percent Difference'])
                csv_data.append(['', f"{self._format_number(volume1)} mm³", f"{self._format_number(volume2)} mm³", 
                                f"{self._format_number(volume_diff)} mm³", f"{self._format_number(volume_percent)}%"])
                csv_data.append(['', '', ''])
                
                # Surface Area
                area1 = geometric.get('surface_area', {}).get('file1', 0)
                area2 = geometric.get('surface_area', {}).get('file2', 0)
                area_diff = geometric.get('surface_area', {}).get('difference', 0)
                area_percent = geometric.get('surface_area', {}).get('percent_difference', 0)
                
                csv_data.append(['Surface Area', '', ''])
                csv_data.append(['', 'File 1', 'File 2', 'Difference', 'Percent Difference'])
                csv_data.append(['', f"{self._format_number(area1)} mm²", f"{self._format_number(area2)} mm²", 
                                f"{self._format_number(area_diff)} mm²", f"{self._format_number(area_percent)}%"])
                csv_data.append(['', '', ''])
                
                # Bounding Box
                bbox1 = geometric.get('bounding_box', {}).get('file1', {})
                bbox2 = geometric.get('bounding_box', {}).get('file2', {})
                
                csv_data.append(['Bounding Box', '', ''])
                csv_data.append(['', 'Dimension', 'File 1', 'File 2', 'Difference'])
                
                for dim in ['x', 'y', 'z']:
                    dim1 = bbox1.get(dim, 0)
                    dim2 = bbox2.get(dim, 0)
                    diff = abs(dim2 - dim1)
                    csv_data.append(['', dim.upper(), f"{self._format_number(dim1)} mm", f"{self._format_number(dim2)} mm", f"{self._format_number(diff)} mm"])
                
                csv_data.append(['', '', ''])
                
                # Center of Mass
                com1 = geometric.get('center_of_mass', {}).get('file1', {})
                com2 = geometric.get('center_of_mass', {}).get('file2', {})
                com_distance = geometric.get('center_of_mass', {}).get('distance', 0)
                
                csv_data.append(['Center of Mass', '', ''])
                csv_data.append(['', 'Axis', 'File 1', 'File 2', 'Difference'])
                
                for axis in ['x', 'y', 'z']:
                    pos1 = com1.get(axis, 0)
                    pos2 = com2.get(axis, 0)
                    diff = abs(pos2 - pos1)
                    csv_data.append(['', axis.upper(), f"{self._format_number(pos1)} mm", f"{self._format_number(pos2)} mm", f"{self._format_number(diff)} mm"])
                
                csv_data.append(['', 'Total Distance', '', '', f"{self._format_number(com_distance)} mm"])
                csv_data.append(['', '', ''])
            
            # Add structural differences
            structural = self.differences.get('structural', {})
            if structural:
                csv_data.append(['Structural Differences', '', ''])
                
                # Entity differences
                entity_diffs = structural.get('entity_differences', {})
                if entity_diffs:
                    # Only in file 1
                    only_in_file1 = entity_diffs.get('only_in_file1', {})
                    if only_in_file1:
                        csv_data.append(['Entities Only in File 1', '', ''])
                        csv_data.append(['', 'Entity Type', 'Count'])
                        
                        for entity_type, count in only_in_file1.items():
                            csv_data.append(['', entity_type, count])
                        
                        csv_data.append(['', '', ''])
                    
                    # Only in file 2
                    only_in_file2 = entity_diffs.get('only_in_file2', {})
                    if only_in_file2:
                        csv_data.append(['Entities Only in File 2', '', ''])
                        csv_data.append(['', 'Entity Type', 'Count'])
                        
                        for entity_type, count in only_in_file2.items():
                            csv_data.append(['', entity_type, count])
                        
                        csv_data.append(['', '', ''])
                    
                    # Count differences
                    count_diffs = entity_diffs.get('count_differences', {})
                    if count_diffs:
                        csv_data.append(['Entity Count Differences', '', ''])
                        csv_data.append(['', 'Entity Type', 'File 1', 'File 2', 'Difference'])
                        
                        for entity_type, counts in count_diffs.items():
                            count1 = counts.get('file1', 0)
                            count2 = counts.get('file2', 0)
                            diff = count2 - count1
                            csv_data.append(['', entity_type, count1, count2, f"{diff:+d}"])
                        
                        csv_data.append(['', '', ''])
            
            # Write to CSV file
            if output_path:
                with open(output_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerows(csv_data)
                logger.info(f"CSV report generated at {output_path}")
                return output_path
            
            return csv_data
            
        except Exception as e:
            logger.error(f"Error generating CSV report: {str(e)}")
            return None 