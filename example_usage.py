"""
Example Usage Script
Shows how to use the IB-to-DSR system programmatically
"""

import os
from pathlib import Path
from src.pdf_indexer import IBIndexer
from src.mapping_parser import MappingParser
from src.content_matcher import ContentMatcher
from src.template_populator import TemplatePopulator
import json

# Configuration
BASE_DIR = Path(__file__).parent
IB_PDF = BASE_DIR / "investigative_brochure.pdf"
TEMPLATE = BASE_DIR / "Drug_Safety_Report_Template.docx"
MAPPING = BASE_DIR / "IB_to_DSR_Manual_Mapping.md"
OUTPUT = BASE_DIR / "data" / "output" / "DSR_Example.docx"
INDEX_FILE = BASE_DIR / "data" / "intermediate" / "ib_index.json"

# Get OpenAI API key from environment
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


def example_stage_1_indexing():
    """Example: Stage 1 - Index the IB PDF"""
    print("\n" + "="*60)
    print("EXAMPLE: Stage 1 - PDF Indexing")
    print("="*60)
    
    # Create indexer
    indexer = IBIndexer(str(IB_PDF))
    
    # Create index
    ib_index = indexer.create_index()
    
    # Save index
    indexer.save_index(str(INDEX_FILE))
    
    # Show some results
    print(f"\nIndex Summary:")
    print(f"  Total pages: {ib_index['total_pages']}")
    print(f"  Sections found: {len(ib_index['sections'])}")
    print(f"  Tables extracted: {len(ib_index['tables'])}")
    
    return ib_index


def example_stage_2_matching(ib_index):
    """Example: Stage 2 - Match content"""
    print("\n" + "="*60)
    print("EXAMPLE: Stage 2 - Content Matching")
    print("="*60)
    
    # Parse mapping
    parser = MappingParser(str(MAPPING))
    mapping = parser.parse_mapping_file()
    
    print(f"\nMapping Summary:")
    priorities = parser.get_all_fields_by_priority()
    print(f"  Direct extraction: {len(priorities['priority_1_direct'])}")
    print(f"  AI synthesis: {len(priorities['priority_2_synthesis'])}")
    print(f"  Unavailable: {len(priorities['priority_3_unavailable'])}")
    
    # Create matcher
    matcher = ContentMatcher(ib_index, mapping, OPENAI_API_KEY)
    
    # Match all fields
    matched_content = matcher.match_all_fields()
    
    # Save matched content
    matched_file = BASE_DIR / "data" / "intermediate" / "matched_content_example.json"
    matched_file.parent.mkdir(parents=True, exist_ok=True)
    with open(matched_file, 'w', encoding='utf-8') as f:
        json.dump(matched_content, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Matched content saved to: {matched_file}")
    
    return matched_content


def example_stage_3_populating(matched_content):
    """Example: Stage 3 - Populate template"""
    print("\n" + "="*60)
    print("EXAMPLE: Stage 3 - Template Population")
    print("="*60)
    
    # Create populator
    populator = TemplatePopulator(str(TEMPLATE))
    
    # Find placeholders
    placeholders = populator.find_all_placeholders()
    print(f"\nFound {len(placeholders)} placeholders")
    
    # Populate all fields
    populator.populate_all_fields(matched_content)
    
    # Generate report
    report = populator.generate_mapping_report(matched_content)
    populator.print_report(report)
    
    # Save document
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    populator.save_document(str(OUTPUT))
    
    print(f"\n✓ Document saved to: {OUTPUT}")


def example_direct_extraction_only():
    """Example: Extract only direct fields (no AI)"""
    print("\n" + "="*60)
    print("EXAMPLE: Direct Extraction Only (No AI)")
    print("="*60)
    
    # Load or create index
    if INDEX_FILE.exists():
        print(f"Loading existing index from {INDEX_FILE}")
        with open(INDEX_FILE, 'r') as f:
            ib_index = json.load(f)
    else:
        print("Creating new index...")
        indexer = IBIndexer(str(IB_PDF))
        ib_index = indexer.create_index()
        indexer.save_index(str(INDEX_FILE))
    
    # Parse mapping
    parser = MappingParser(str(MAPPING))
    mapping = parser.parse_mapping_file()
    
    # Filter to only direct extraction fields
    priorities = parser.get_all_fields_by_priority()
    direct_fields = priorities['priority_1_direct']
    
    direct_mapping = {k: v for k, v in mapping.items() if k in direct_fields}
    
    print(f"\nProcessing {len(direct_mapping)} direct extraction fields...")
    
    # Create matcher without API key (skips AI)
    matcher = ContentMatcher(ib_index, direct_mapping, None)
    
    # Match only direct fields
    matched_content = {}
    for field_name, mapping_info in direct_mapping.items():
        content = matcher.direct_extract(field_name, mapping_info)
        matched_content[field_name] = content
        print(f"  ✓ {field_name}: {len(content)} chars")
    
    return matched_content


def main():
    """Run example workflows"""
    
    print("\n" + "="*80)
    print("IB-TO-DSR AUTOMATION - EXAMPLE USAGE")
    print("="*80)
    print("\nThis script demonstrates different ways to use the system.")
    print("\nChoose an example to run:")
    print("1. Full pipeline (all 3 stages)")
    print("2. Stage 1 only (PDF indexing)")
    print("3. Stage 2 only (content matching) - requires existing index")
    print("4. Stage 3 only (template population) - requires matched content")
    print("5. Direct extraction only (no AI, no API key needed)")
    print()
    
    choice = input("Enter choice (1-5): ").strip()
    
    if choice == "1":
        # Full pipeline
        print("\n→ Running full pipeline...")
        ib_index = example_stage_1_indexing()
        matched_content = example_stage_2_matching(ib_index)
        example_stage_3_populating(matched_content)
        
    elif choice == "2":
        # Stage 1 only
        example_stage_1_indexing()
        
    elif choice == "3":
        # Stage 2 only
        if not INDEX_FILE.exists():
            print(f"\n✗ Error: Index file not found at {INDEX_FILE}")
            print("Run stage 1 first to create the index.")
            return
        
        with open(INDEX_FILE, 'r') as f:
            ib_index = json.load(f)
        
        example_stage_2_matching(ib_index)
        
    elif choice == "4":
        # Stage 3 only
        matched_file = BASE_DIR / "data" / "intermediate" / "matched_content.json"
        if not matched_file.exists():
            print(f"\n✗ Error: Matched content not found at {matched_file}")
            print("Run stage 2 first to create matched content.")
            return
        
        with open(matched_file, 'r') as f:
            matched_content = json.load(f)
        
        example_stage_3_populating(matched_content)
        
    elif choice == "5":
        # Direct extraction only
        matched_content = example_direct_extraction_only()
        print(f"\n✓ Extracted {len(matched_content)} direct fields")
        
    else:
        print("\n✗ Invalid choice")
        return
    
    print("\n" + "="*80)
    print("EXAMPLE COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

