"""
Main Orchestration Script
IB to DSR Automation Pipeline
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

from src.pdf_indexer import IBIndexer
from src.mapping_parser import MappingParser
from src.content_matcher import ContentMatcher
from src.template_populator import TemplatePopulator


class IBtoDSRPipeline:
    """Main pipeline orchestrating all stages"""
    
    def __init__(self, config: dict):
        """
        Initialize pipeline with configuration
        
        Args:
            config: Configuration dictionary with paths and settings
        """
        self.config = config
        self.ib_index = None
        self.mapping = None
        self.matched_content = None
    
    def run_full_pipeline(self):
        """Run the complete three-stage pipeline"""
        print("\n" + "="*80)
        print("IB-TO-DSR AUTOMATION PIPELINE")
        print("="*80)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        try:
            # Stage 1: Index IB PDF
            print("\n[STAGE 1] Indexing Investigator Brochure PDF...")
            print("-" * 80)
            self.index_ib()
            
            # Stage 2: Parse mapping and match content
            print("\n[STAGE 2] Matching IB Content to DSR Fields...")
            print("-" * 80)
            self.match_content()
            
            # Stage 3: Populate template
            print("\n[STAGE 3] Populating DSR Template...")
            print("-" * 80)
            self.populate_template()
            
            print("\n" + "="*80)
            print("✓ PIPELINE COMPLETED SUCCESSFULLY!")
            print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*80 + "\n")
            
            return True
            
        except Exception as e:
            print("\n" + "="*80)
            print("✗ PIPELINE FAILED")
            print(f"Error: {str(e)}")
            print("="*80 + "\n")
            import traceback
            traceback.print_exc()
            return False
    
    def index_ib(self):
        """Stage 1: Index the IB PDF"""
        ib_pdf_path = Path(self.config['ib_pdf_path'])
        index_path = Path(self.config['index_output_path'])
        
        if not ib_pdf_path.exists():
            raise FileNotFoundError(f"IB PDF not found: {ib_pdf_path}")
        
        # Check if index already exists
        if index_path.exists() and not self.config.get('force_reindex', False):
            print(f"Loading existing IB index from: {index_path}")
            with open(index_path, 'r', encoding='utf-8') as f:
                self.ib_index = json.load(f)
            print(f"✓ IB index loaded: {len(self.ib_index.get('sections', {}))} sections found")
        else:
            print(f"Creating new IB index from: {ib_pdf_path}")
            indexer = IBIndexer(str(ib_pdf_path))
            self.ib_index = indexer.create_index()
            
            # Save index
            index_path.parent.mkdir(parents=True, exist_ok=True)
            indexer.save_index(str(index_path))
            print(f"✓ IB indexed: {len(self.ib_index.get('sections', {}))} sections found")
    
    def match_content(self):
        """Stage 2: Parse mapping and match content from IB to DSR fields"""
        mapping_path = Path(self.config['mapping_file_path'])
        
        if not mapping_path.exists():
            raise FileNotFoundError(f"Mapping file not found: {mapping_path}")
        
        # Parse mapping file
        print(f"Parsing mapping file: {mapping_path}")
        parser = MappingParser(str(mapping_path))
        self.mapping = parser.parse_mapping_file()
        
        print(f"✓ Mapping parsed: {len(self.mapping)} fields identified")
        
        # Show priority breakdown
        priorities = parser.get_all_fields_by_priority()
        print(f"  - Direct extraction: {len(priorities['priority_1_direct'])} fields")
        print(f"  - AI synthesis: {len(priorities['priority_2_synthesis'])} fields")
        print(f"  - Unavailable: {len(priorities['priority_3_unavailable'])} fields")
        
        # Match content
        print("\nMatching content from IB to DSR fields...")
        matcher = ContentMatcher(
            self.ib_index,
            self.mapping,
            openai_api_key=self.config.get('openai_api_key')
        )
        
        self.matched_content = matcher.match_all_fields()
        
        # Save matched content for review
        intermediate_path = Path(self.config['intermediate_output_path'])
        intermediate_path.mkdir(parents=True, exist_ok=True)
        
        matched_content_file = intermediate_path / "matched_content.json"
        with open(matched_content_file, 'w', encoding='utf-8') as f:
            json.dump(self.matched_content, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Content matched and saved to: {matched_content_file}")
    
    def populate_template(self):
        """Stage 3: Populate the DSR template"""
        template_path = Path(self.config['template_path'])
        output_path = Path(self.config['output_path'])
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        # Create populator
        print(f"Loading template: {template_path}")
        populator = TemplatePopulator(str(template_path))
        
        # Find placeholders
        placeholders = populator.find_all_placeholders()
        print(f"Found {len(placeholders)} placeholders in template")
        
        # Populate all fields
        populator.populate_all_fields(self.matched_content)
        
        # Generate report
        report = populator.generate_mapping_report(self.matched_content)
        populator.print_report(report)
        
        # Save populated document
        output_path.parent.mkdir(parents=True, exist_ok=True)
        populator.save_document(str(output_path))
        
        # Save report
        report_path = output_path.parent / f"population_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Report saved to: {report_path}")


def main():
    """Main entry point with CLI interface"""
    parser = argparse.ArgumentParser(
        description='Automate DSR population from Investigator Brochure',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full pipeline with all files specified
  python main.py \\
    --ib-pdf investigative_brochure.pdf \\
    --template Drug_Safety_Report_Template.docx \\
    --mapping IB_to_DSR_Manual_Mapping.md \\
    --output data/output/DSR_Populated.docx \\
    --openai-key sk-...
  
  # Using environment variable for API key
  export OPENAI_API_KEY=sk-...
  python main.py --ib-pdf ib.pdf --template template.docx --mapping mapping.md --output output.docx
        """
    )
    
    parser.add_argument(
        '--ib-pdf',
        required=True,
        help='Path to Investigator Brochure PDF'
    )
    parser.add_argument(
        '--template',
        required=True,
        help='Path to DSR Word template (.docx)'
    )
    parser.add_argument(
        '--mapping',
        required=True,
        help='Path to manual mapping markdown file'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Path for output populated DSR document'
    )
    parser.add_argument(
        '--openai-key',
        help='OpenAI API key (or set OPENAI_API_KEY environment variable)'
    )
    parser.add_argument(
        '--force-reindex',
        action='store_true',
        help='Force re-indexing of IB PDF even if index exists'
    )
    parser.add_argument(
        '--index-path',
        default='data/intermediate/ib_index.json',
        help='Path for IB index file (default: data/intermediate/ib_index.json)'
    )
    parser.add_argument(
        '--intermediate-dir',
        default='data/intermediate',
        help='Directory for intermediate files (default: data/intermediate)'
    )
    
    args = parser.parse_args()
    
    # Get OpenAI API key from args or environment
    import os
    openai_key = args.openai_key or os.getenv('OPENAI_API_KEY')
    
    if not openai_key:
        print("\n⚠ WARNING: No OpenAI API key provided!")
        print("AI-powered synthesis will be skipped.")
        print("Provide key via --openai-key or set OPENAI_API_KEY environment variable.\n")
    
    # Build configuration
    config = {
        'ib_pdf_path': args.ib_pdf,
        'template_path': args.template,
        'mapping_file_path': args.mapping,
        'output_path': args.output,
        'openai_api_key': openai_key,
        'force_reindex': args.force_reindex,
        'index_output_path': args.index_path,
        'intermediate_output_path': args.intermediate_dir
    }
    
    # Validate input files exist
    for key in ['ib_pdf_path', 'template_path', 'mapping_file_path']:
        path = Path(config[key])
        if not path.exists():
            print(f"✗ Error: {key} not found: {path}")
            sys.exit(1)
    
    # Run pipeline
    pipeline = IBtoDSRPipeline(config)
    success = pipeline.run_full_pipeline()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

