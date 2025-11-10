"""
Mapping Parser Module
Parses the IB_to_DSR_Manual_Mapping.md file to extract mapping information
"""

import re
from typing import Dict, List, Tuple
from pathlib import Path


class MappingParser:
    """Parses the manual mapping markdown file"""
    
    def __init__(self, mapping_file_path: str):
        """
        Initialize with path to mapping markdown file
        
        Args:
            mapping_file_path: Path to IB_to_DSR_Manual_Mapping.md
        """
        self.mapping_file_path = Path(mapping_file_path)
        if not self.mapping_file_path.exists():
            raise FileNotFoundError(f"Mapping file not found: {mapping_file_path}")
        
        self.mapping_dict = {}
        
    def parse_mapping_file(self) -> Dict[str, Dict]:
        """
        Parse the markdown mapping file
        
        Returns:
            Dict mapping DSR field placeholders to IB section info
        """
        print(f"Parsing mapping file: {self.mapping_file_path}")
        
        with open(self.mapping_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract mapping tables from markdown
        # Look for table rows with format: | DSR Field | IB Section | Pages | Notes |
        mappings = {}
        
        # Find all table rows (lines starting with |)
        table_row_pattern = re.compile(r'\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]*)\|')
        
        for line in content.split('\n'):
            match = table_row_pattern.match(line)
            if match:
                field = match.group(1).strip()
                ib_section = match.group(2).strip()
                pages = match.group(3).strip()
                notes = match.group(4).strip()
                
                # Skip header rows and separator rows
                if field in ['DSR Template Field', 'DSR Field', '---', '']:
                    continue
                if '---' in field or '===' in field:
                    continue
                
                # Look for placeholder pattern [INSERT_*]
                placeholder_match = re.search(r'\[INSERT_[A-Z0-9_]+\]', field)
                if placeholder_match:
                    placeholder = placeholder_match.group(0)
                    
                    # Parse page numbers
                    page_list = self._parse_pages(pages)
                    
                    # Determine mapping type
                    mapping_type = self._determine_mapping_type(ib_section, notes)
                    
                    mappings[placeholder] = {
                        'field_description': field.replace(placeholder, '').strip(' -:'),
                        'ib_section': ib_section,
                        'ib_pages': page_list,
                        'mapping_type': mapping_type,
                        'notes': notes
                    }
        
        self.mapping_dict = mappings
        print(f"✓ Parsed {len(mappings)} field mappings")
        return mappings
    
    def _parse_pages(self, pages_str: str) -> List[int]:
        """
        Parse page numbers from string format
        Handles: "89", "34-45", "15, 22, 34", etc.
        
        Args:
            pages_str: String containing page numbers
            
        Returns:
            List of page numbers
        """
        if not pages_str or pages_str == 'N/A' or pages_str == '-':
            return []
        
        page_list = []
        
        # Split by comma first
        parts = pages_str.split(',')
        
        for part in parts:
            part = part.strip()
            
            # Check for range (e.g., "34-45")
            if '-' in part:
                range_match = re.match(r'(\d+)\s*-\s*(\d+)', part)
                if range_match:
                    start = int(range_match.group(1))
                    end = int(range_match.group(2))
                    page_list.extend(range(start, end + 1))
            else:
                # Single page number
                page_match = re.search(r'\d+', part)
                if page_match:
                    page_list.append(int(page_match.group(0)))
        
        return sorted(list(set(page_list)))  # Remove duplicates and sort
    
    def _determine_mapping_type(self, ib_section: str, notes: str) -> str:
        """
        Determine the type of mapping needed
        
        Args:
            ib_section: IB section description
            notes: Notes about the mapping
            
        Returns:
            Mapping type: 'direct_extract', 'synthesis_required', or 'unavailable'
        """
        # Convert to lowercase for checking
        section_lower = ib_section.lower()
        notes_lower = notes.lower()
        
        # Check for unavailable/external data needed
        unavailable_keywords = [
            'not in ib',
            'external source',
            'safety database',
            'case report',
            'requires query',
            'not available',
            'n/a'
        ]
        
        for keyword in unavailable_keywords:
            if keyword in section_lower or keyword in notes_lower:
                return 'unavailable'
        
        # Check for synthesis needed
        synthesis_keywords = [
            'synthesis',
            'combine',
            'summarize',
            'multiple sections',
            'rewrite',
            'adapt'
        ]
        
        for keyword in synthesis_keywords:
            if keyword in notes_lower:
                return 'synthesis_required'
        
        # Check if multiple sections mentioned
        if '+' in ib_section or ',' in ib_section or 'and' in section_lower:
            return 'synthesis_required'
        
        # Default to direct extraction
        return 'direct_extract'
    
    def get_mapping_for_field(self, field_name: str) -> Dict:
        """
        Get mapping details for a specific DSR field
        
        Args:
            field_name: DSR placeholder field name
            
        Returns:
            Mapping details dict
        """
        if not self.mapping_dict:
            self.parse_mapping_file()
        
        return self.mapping_dict.get(field_name, {})
    
    def get_all_fields_by_priority(self) -> Dict[str, List[str]]:
        """
        Return fields grouped by extraction priority
        
        Returns:
            Dict with priority levels as keys and field lists as values
        """
        if not self.mapping_dict:
            self.parse_mapping_file()
        
        priorities = {
            'priority_1_direct': [],
            'priority_2_synthesis': [],
            'priority_3_unavailable': []
        }
        
        for field, mapping in self.mapping_dict.items():
            mapping_type = mapping['mapping_type']
            
            if mapping_type == 'direct_extract':
                priorities['priority_1_direct'].append(field)
            elif mapping_type == 'synthesis_required':
                priorities['priority_2_synthesis'].append(field)
            else:
                priorities['priority_3_unavailable'].append(field)
        
        return priorities
    
    def get_fields_requiring_ai(self) -> List[str]:
        """
        Return list of fields that need AI-powered extraction
        
        Returns:
            List of field names requiring AI synthesis
        """
        if not self.mapping_dict:
            self.parse_mapping_file()
        
        ai_fields = []
        
        for field, mapping in self.mapping_dict.items():
            if mapping['mapping_type'] == 'synthesis_required':
                ai_fields.append(field)
        
        return ai_fields
    
    def get_all_field_names(self) -> List[str]:
        """
        Get list of all DSR field placeholders
        
        Returns:
            List of field placeholder names
        """
        if not self.mapping_dict:
            self.parse_mapping_file()
        
        return list(self.mapping_dict.keys())


def main():
    """Standalone execution for testing"""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='Parse IB to DSR mapping file')
    parser.add_argument('--input', required=True, help='Path to mapping markdown file')
    parser.add_argument('--output', help='Optional: Path for output JSON')
    
    args = parser.parse_args()
    
    parser = MappingParser(args.input)
    mapping = parser.parse_mapping_file()
    
    print(f"\nTotal fields: {len(mapping)}")
    
    priorities = parser.get_all_fields_by_priority()
    print(f"Direct extraction: {len(priorities['priority_1_direct'])}")
    print(f"Synthesis required: {len(priorities['priority_2_synthesis'])}")
    print(f"Unavailable: {len(priorities['priority_3_unavailable'])}")
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Mapping saved to: {args.output}")


if __name__ == '__main__':
    main()

