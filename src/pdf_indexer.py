"""
PDF Indexer Module - Stage 1
Extracts and indexes all content from the Investigator Brochure PDF
"""

import re
import json
from typing import Dict, List, Tuple, Any
import PyPDF2
import pdfplumber
from pathlib import Path


class IBIndexer:
    """Extracts and indexes content from Investigator Brochure PDF"""
    
    def __init__(self, pdf_path: str):
        """
        Initialize with path to IB PDF
        
        Args:
            pdf_path: Path to the Investigator Brochure PDF file
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        self.extracted_text = []
        self.sections = {}
        self.tables = []
        
    def extract_all_text(self) -> List[Tuple[int, str]]:
        """
        Extract text from all pages with page numbers
        
        Returns:
            List of (page_num, text) tuples
        """
        print(f"Extracting text from {self.pdf_path}...")
        extracted = []
        
        with open(self.pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            
            for page_num in range(total_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                extracted.append((page_num + 1, text))  # 1-indexed page numbers
        
        self.extracted_text = extracted
        print(f"✓ Extracted text from {total_pages} pages")
        return extracted
    
    def identify_sections(self, extracted_text: List[Tuple[int, str]] = None) -> Dict:
        """
        Parse extracted text to identify section headers
        Matches patterns like:
        - "1. SUMMARY"
        - "1.1 Scientific Rationale"
        - "5.5.1.2.4 Deaths"
        
        Args:
            extracted_text: Optional list of (page_num, text) tuples
            
        Returns:
            Dict mapping section numbers to titles and page ranges
        """
        if extracted_text is None:
            extracted_text = self.extracted_text
        
        if not extracted_text:
            self.extract_all_text()
            extracted_text = self.extracted_text
        
        print("Identifying section headers...")
        sections = {}
        
        # Regex pattern for section numbers (e.g., "1.", "1.1", "5.5.1.2.4")
        section_pattern = re.compile(r'^(\d+(?:\.\d+)*\.?)\s+([A-Z][A-Z\s,\-\(\)]+)', re.MULTILINE)
        
        for page_num, text in extracted_text:
            matches = section_pattern.finditer(text)
            
            for match in matches:
                section_num = match.group(1).rstrip('.')
                section_title = match.group(2).strip()
                
                # Skip very short titles (likely false positives)
                if len(section_title) < 3:
                    continue
                
                # Store section info
                if section_num not in sections:
                    sections[section_num] = {
                        'title': section_title,
                        'pages': [page_num],
                        'content': []
                    }
                else:
                    # Add page if not already present
                    if page_num not in sections[section_num]['pages']:
                        sections[section_num]['pages'].append(page_num)
        
        self.sections = sections
        print(f"✓ Identified {len(sections)} section headers")
        return sections
    
    def extract_section_content(self, section_number: str) -> str:
        """
        Extract all content for a specific section
        
        Args:
            section_number: Section number (e.g., "1.1", "5.5.1")
            
        Returns:
            String of section content
        """
        if not self.sections:
            self.identify_sections()
        
        if section_number not in self.sections:
            return ""
        
        section_info = self.sections[section_number]
        pages = section_info['pages']
        
        content_parts = []
        for page_num in pages:
            # Find the text for this page
            for p_num, text in self.extracted_text:
                if p_num == page_num:
                    content_parts.append(text)
                    break
        
        return "\n".join(content_parts)
    
    def extract_tables(self) -> List[Dict]:
        """
        Extract tables from PDF using pdfplumber
        
        Returns:
            List of tables with page numbers
        """
        print("Extracting tables from PDF...")
        tables = []
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                page_tables = page.extract_tables()
                
                for table_idx, table in enumerate(page_tables):
                    if table:  # Only add non-empty tables
                        tables.append({
                            'page': page_num,
                            'table_index': table_idx,
                            'content': table
                        })
        
        self.tables = tables
        print(f"✓ Extracted {len(tables)} tables")
        return tables
    
    def _extract_metadata(self) -> Dict[str, str]:
        """
        Extract metadata from the PDF (drug name, RO number, etc.)
        
        Returns:
            Dict with metadata fields
        """
        metadata = {
            'drug_name': '',
            'trade_name': '',
            'ro_number': '',
            'version': '',
            'date': ''
        }
        
        # Look in first few pages for metadata
        for page_num, text in self.extracted_text[:5]:
            # Look for RO number
            ro_match = re.search(r'RO\d+', text)
            if ro_match and not metadata['ro_number']:
                metadata['ro_number'] = ro_match.group(0)
            
            # Look for drug names
            if 'pralsetinib' in text.lower() and not metadata['drug_name']:
                metadata['drug_name'] = 'Pralsetinib'
            
            if 'GAVRETO' in text and not metadata['trade_name']:
                metadata['trade_name'] = 'GAVRETO'
        
        return metadata
    
    def create_index(self) -> Dict[str, Any]:
        """
        Create comprehensive index of IB structure
        
        Returns:
            Complete index structure with metadata, sections, and tables
        """
        print("\n" + "="*60)
        print("Creating IB Index")
        print("="*60)
        
        # Extract text if not already done
        if not self.extracted_text:
            self.extract_all_text()
        
        # Identify sections
        if not self.sections:
            self.identify_sections()
        
        # Extract tables
        if not self.tables:
            self.extract_tables()
        
        # Extract metadata
        metadata = self._extract_metadata()
        
        # Build hierarchical section structure
        hierarchical_sections = self._build_hierarchical_sections()
        
        index = {
            'metadata': metadata,
            'sections': hierarchical_sections,
            'tables': self.tables,
            'total_pages': len(self.extracted_text)
        }
        
        print("\n✓ Index created successfully")
        print(f"  - Metadata: {len([v for v in metadata.values() if v])} fields populated")
        print(f"  - Sections: {len(self.sections)} total")
        print(f"  - Tables: {len(self.tables)} extracted")
        print("="*60 + "\n")
        
        return index
    
    def _build_hierarchical_sections(self) -> Dict:
        """
        Build hierarchical section structure from flat section list
        
        Returns:
            Nested dict structure of sections
        """
        hierarchical = {}
        
        for section_num, section_data in sorted(self.sections.items(), key=lambda x: self._section_sort_key(x[0])):
            parts = section_num.split('.')
            
            # For top-level sections (e.g., "1", "2")
            if len(parts) == 1:
                hierarchical[section_num] = {
                    'title': section_data['title'],
                    'pages': section_data['pages'],
                    'subsections': {}
                }
            else:
                # For subsections, nest them appropriately
                parent = parts[0]
                if parent in hierarchical:
                    hierarchical[parent]['subsections'][section_num] = {
                        'title': section_data['title'],
                        'pages': section_data['pages']
                    }
        
        return hierarchical
    
    def _section_sort_key(self, section_num: str) -> Tuple:
        """
        Create a sort key for section numbers
        
        Args:
            section_num: Section number string (e.g., "1.2.3")
            
        Returns:
            Tuple of integers for sorting
        """
        return tuple(int(x) for x in section_num.split('.'))
    
    def save_index(self, output_path: str):
        """
        Save index to JSON file
        
        Args:
            output_path: Path where to save the JSON index
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create index if not already done
        if not self.sections:
            index = self.create_index()
        else:
            index = {
                'metadata': self._extract_metadata(),
                'sections': self._build_hierarchical_sections(),
                'tables': self.tables,
                'total_pages': len(self.extracted_text)
            }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Index saved to: {output_path}")


def main():
    """Standalone execution for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Index an Investigator Brochure PDF')
    parser.add_argument('--input', required=True, help='Path to IB PDF file')
    parser.add_argument('--output', required=True, help='Path for output JSON index')
    
    args = parser.parse_args()
    
    indexer = IBIndexer(args.input)
    index = indexer.create_index()
    indexer.save_index(args.output)


if __name__ == '__main__':
    main()

