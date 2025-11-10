"""
Quick system test to verify all modules can be imported
"""

import sys
from pathlib import Path

def test_imports():
    """Test that all modules can be imported"""
    print("Testing module imports...")
    
    try:
        from src.pdf_indexer import IBIndexer
        print("✓ pdf_indexer imported successfully")
    except Exception as e:
        print(f"✗ pdf_indexer import failed: {e}")
        return False
    
    try:
        from src.mapping_parser import MappingParser
        print("✓ mapping_parser imported successfully")
    except Exception as e:
        print(f"✗ mapping_parser import failed: {e}")
        return False
    
    try:
        from src.content_matcher import ContentMatcher
        print("✓ content_matcher imported successfully")
    except Exception as e:
        print(f"✗ content_matcher import failed: {e}")
        return False
    
    try:
        from src.template_populator import TemplatePopulator
        print("✓ template_populator imported successfully")
    except Exception as e:
        print(f"✗ template_populator import failed: {e}")
        return False
    
    return True

def test_files_exist():
    """Test that required files exist"""
    print("\nChecking required files...")
    
    files = {
        'IB PDF': 'investigative_brochure.pdf',
        'DSR Template': 'Drug_Safety_Report_Template.docx',
        'Mapping File': 'IB_to_DSR_Manual_Mapping.md'
    }
    
    all_exist = True
    for name, filepath in files.items():
        path = Path(filepath)
        if path.exists():
            print(f"✓ {name} found: {filepath}")
        else:
            print(f"✗ {name} NOT found: {filepath}")
            all_exist = False
    
    return all_exist

def test_dependencies():
    """Test that required packages are installed"""
    print("\nChecking Python dependencies...")
    
    packages = [
        'PyPDF2',
        'pdfplumber',
        'fitz',  # pymupdf
        'docx',  # python-docx
        'openai',
        'pandas',
        'numpy',
        'yaml',
        'dotenv',
        'tqdm'
    ]
    
    missing = []
    for package in packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - NOT INSTALLED")
            missing.append(package)
    
    if missing:
        print(f"\n⚠ Missing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    return True

def main():
    """Run all tests"""
    print("="*60)
    print("IB-to-DSR System Test")
    print("="*60)
    print()
    
    # Test imports
    imports_ok = test_imports()
    
    # Test files
    files_ok = test_files_exist()
    
    # Test dependencies
    deps_ok = test_dependencies()
    
    print("\n" + "="*60)
    if imports_ok and files_ok and deps_ok:
        print("✓ ALL TESTS PASSED")
        print("System is ready to run!")
        print("\nRun the pipeline with:")
        print("python main.py --ib-pdf investigative_brochure.pdf \\")
        print("  --template Drug_Safety_Report_Template.docx \\")
        print("  --mapping IB_to_DSR_Manual_Mapping.md \\")
        print("  --output data/output/DSR_Populated.docx")
    else:
        print("✗ SOME TESTS FAILED")
        print("Please fix the issues above before running the pipeline.")
        sys.exit(1)
    print("="*60)

if __name__ == '__main__':
    main()

