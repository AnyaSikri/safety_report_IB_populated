"""
Content Matcher Module - Stage 2
Matches DSR template fields to IB content using the mapping
Uses OpenAI for AI-powered extraction and synthesis
"""

import json
import time
from typing import Dict, List, Any, Optional
from openai import OpenAI


class ContentMatcher:
    """Matches DSR fields to IB content with AI-powered extraction"""
    
    def __init__(self, ib_index: Dict, mapping_dict: Dict, openai_api_key: Optional[str] = None):
        """
        Initialize with IB index and mapping
        
        Args:
            ib_index: The indexed IB structure from IBIndexer
            mapping_dict: The mapping from MappingParser
            openai_api_key: OpenAI API key for AI-powered extraction
        """
        self.ib_index = ib_index
        self.mapping_dict = mapping_dict
        self.openai_api_key = openai_api_key
        
        if openai_api_key:
            self.client = OpenAI(api_key=openai_api_key)
        else:
            self.client = None
            print("⚠ Warning: No OpenAI API key provided. AI extraction will be skipped.")
    
    def match_all_fields(self) -> Dict[str, str]:
        """
        Match all DSR fields to IB content
        
        Returns:
            Dict of {field_name: extracted_content}
        """
        print("\n" + "="*60)
        print("Matching DSR Fields to IB Content")
        print("="*60)
        
        matched_content = {}
        
        # Count by type
        direct_count = 0
        ai_count = 0
        unavailable_count = 0
        
        total = len(self.mapping_dict)
        current = 0
        
        for field_name, mapping_info in self.mapping_dict.items():
            current += 1
            print(f"\n[{current}/{total}] Processing: {field_name}")
            
            mapping_type = mapping_info['mapping_type']
            
            try:
                if mapping_type == 'direct_extract':
                    content = self.direct_extract(field_name, mapping_info)
                    direct_count += 1
                elif mapping_type == 'synthesis_required':
                    content = self.ai_extract(field_name, mapping_info)
                    ai_count += 1
                else:  # unavailable
                    content = self.handle_unavailable_field(field_name, mapping_info)
                    unavailable_count += 1
                
                matched_content[field_name] = content
                print(f"  ✓ {mapping_type}: {len(content) if content else 0} chars extracted")
                
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
                matched_content[field_name] = f"[ERROR EXTRACTING CONTENT: {str(e)}]"
        
        print("\n" + "="*60)
        print("Matching Complete")
        print(f"  Direct extraction: {direct_count}")
        print(f"  AI synthesis: {ai_count}")
        print(f"  Unavailable: {unavailable_count}")
        print("="*60 + "\n")
        
        return matched_content
    
    def direct_extract(self, field_name: str, mapping_info: Dict) -> str:
        """
        Extract content directly from IB for fields with direct mapping
        
        Args:
            field_name: DSR field placeholder name
            mapping_info: Mapping information dict
            
        Returns:
            Extracted content string
        """
        ib_section = mapping_info['ib_section']
        pages = mapping_info['ib_pages']
        
        # Try to extract from specific sections
        content_parts = []
        
        # Extract section numbers from ib_section string
        section_numbers = self._extract_section_numbers(ib_section)
        
        if section_numbers:
            for section_num in section_numbers:
                section_content = self._get_section_content(section_num)
                if section_content:
                    content_parts.append(section_content)
        
        # If no section content found, try to get content from specific pages
        if not content_parts and pages:
            content_parts = self._get_content_from_pages(pages)
        
        # Combine and clean content
        if content_parts:
            combined = "\n\n".join(content_parts)
            return self._clean_text(combined)
        
        return "[Content not found in IB]"
    
    def ai_extract(self, field_name: str, mapping_info: Dict) -> str:
        """
        Use AI to extract and synthesize content
        
        Args:
            field_name: DSR field placeholder name
            mapping_info: Mapping information dict
            
        Returns:
            AI-synthesized content string
        """
        if not self.client:
            return "[AI extraction skipped - no API key provided]"
        
        # First, get the raw content from IB
        ib_section = mapping_info['ib_section']
        pages = mapping_info['ib_pages']
        notes = mapping_info.get('notes', '')
        field_description = mapping_info.get('field_description', '')
        
        # Extract relevant IB sections
        source_content = []
        section_numbers = self._extract_section_numbers(ib_section)
        
        for section_num in section_numbers:
            section_content = self._get_section_content(section_num)
            if section_content:
                source_content.append(f"### Section {section_num}\n{section_content}")
        
        # If no section content, get from pages
        if not source_content and pages:
            page_content = self._get_content_from_pages(pages)
            source_content = page_content
        
        if not source_content:
            return "[No source content found in IB for AI extraction]"
        
        # Combine source content
        combined_source = "\n\n".join(source_content)
        
        # Limit content length to avoid token limits (keep first 10000 chars)
        if len(combined_source) > 10000:
            combined_source = combined_source[:10000] + "\n\n[Content truncated...]"
        
        # Create extraction prompt
        prompt = self._create_extraction_prompt(
            field_name, 
            field_description,
            combined_source, 
            notes
        )
        
        # Call OpenAI API
        try:
            print(f"  → Calling OpenAI API for synthesis...")
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a medical writer preparing a Drug Safety Report (DSR) for pralsetinib (GAVRETO, RO7499790). Extract and synthesize content accurately from the provided Investigator Brochure sections."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            extracted_content = response.choices[0].message.content.strip()
            
            # Add small delay to avoid rate limits
            time.sleep(0.5)
            
            return extracted_content
            
        except Exception as e:
            print(f"  ✗ OpenAI API error: {str(e)}")
            return f"[AI extraction failed: {str(e)}]\n\nRaw content:\n{combined_source[:500]}..."
    
    def _create_extraction_prompt(self, field_name: str, field_description: str, 
                                   ib_content: str, context: str) -> str:
        """
        Create a prompt for AI extraction
        
        Args:
            field_name: DSR field placeholder
            field_description: Description of what the field should contain
            ib_content: Source content from IB
            context: Additional context/notes
            
        Returns:
            Formatted prompt string
        """
        return f"""You are preparing a Drug Safety Report (DSR) for pralsetinib (GAVRETO, RO7499790).

Your task: Extract and synthesize content for the DSR field: {field_name}
Field purpose: {field_description}

Additional context: {context}

Source content from Investigator Brochure:
{ib_content}

Instructions:
1. Extract relevant information from the IB sections above
2. Synthesize into cohesive, well-written content appropriate for a DSR
3. Use formal medical/scientific writing style
4. Be concise but comprehensive
5. Do not include reference citations (we'll add those separately)
6. Do not use placeholder text or phrases like "based on the IB"
7. If the IB content is insufficient, note what specific information is missing
8. Present the information in a clear, professional manner suitable for regulatory submission

Output the extracted/synthesized content only, with no preamble or explanation."""
    
    def _extract_section_numbers(self, ib_section: str) -> List[str]:
        """
        Extract section numbers from IB section description
        
        Args:
            ib_section: Section description string
            
        Returns:
            List of section numbers
        """
        section_numbers = []
        
        # Look for patterns like "Section 1.1", "1.2", "5.5.1", etc.
        pattern = r'\b(\d+(?:\.\d+)*)\b'
        matches = re.findall(pattern, ib_section)
        
        section_numbers.extend(matches)
        
        return section_numbers
    
    def _get_section_content(self, section_number: str) -> str:
        """
        Get content for a specific section from IB index
        
        Args:
            section_number: Section number (e.g., "1.1", "5.5")
            
        Returns:
            Section content string
        """
        sections = self.ib_index.get('sections', {})
        
        # Try to find the section
        # First check top-level sections
        for top_section, top_data in sections.items():
            if top_section == section_number:
                # Get content from pages
                pages = top_data.get('pages', [])
                title = top_data.get('title', '')
                content = self._get_content_from_pages(pages)
                if content:
                    return f"{title}\n\n" + "\n\n".join(content)
            
            # Check subsections
            subsections = top_data.get('subsections', {})
            if section_number in subsections:
                pages = subsections[section_number].get('pages', [])
                title = subsections[section_number].get('title', '')
                content = self._get_content_from_pages(pages)
                if content:
                    return f"{title}\n\n" + "\n\n".join(content)
        
        return ""
    
    def _get_content_from_pages(self, page_numbers: List[int]) -> List[str]:
        """
        Get text content from specific page numbers
        
        Args:
            page_numbers: List of page numbers
            
        Returns:
            List of page content strings
        """
        # Note: In the real implementation, we'd need to store page text in the index
        # For now, return a placeholder
        return [f"[Content from page {p}]" for p in page_numbers[:3]]  # Limit to first 3 pages
    
    def handle_unavailable_field(self, field_name: str, mapping_info: Dict) -> str:
        """
        For fields that cannot be populated from IB
        
        Args:
            field_name: DSR field placeholder name
            mapping_info: Mapping information dict
            
        Returns:
            Placeholder message string
        """
        notes = mapping_info.get('notes', 'External data source required')
        ib_section = mapping_info.get('ib_section', 'N/A')
        
        return f"[DATA NOT AVAILABLE IN IB - REQUIRES: {notes}]"
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers and headers if present
        text = re.sub(r'Page \d+ of \d+', '', text)
        
        # Trim
        text = text.strip()
        
        return text
    
    def validate_extraction(self, field_name: str, extracted_content: str) -> Dict[str, Any]:
        """
        Basic validation of extracted content
        
        Args:
            field_name: DSR field name
            extracted_content: Extracted content string
            
        Returns:
            Validation result dict
        """
        validation = {
            'field': field_name,
            'is_valid': True,
            'warnings': []
        }
        
        # Check if empty
        if not extracted_content or len(extracted_content.strip()) == 0:
            validation['is_valid'] = False
            validation['warnings'].append("Content is empty")
        
        # Check for error messages
        if '[ERROR' in extracted_content or '[DATA NOT AVAILABLE' in extracted_content:
            validation['warnings'].append("Contains error or unavailable message")
        
        # Check for unreasonable length
        if len(extracted_content) > 20000:
            validation['warnings'].append(f"Content very long ({len(extracted_content)} chars)")
        
        if len(extracted_content) < 10 and '[' not in extracted_content:
            validation['warnings'].append("Content very short")
        
        return validation


# Import re at module level (was missing)
import re


def main():
    """Standalone execution for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Match IB content to DSR fields')
    parser.add_argument('--index', required=True, help='Path to IB index JSON')
    parser.add_argument('--mapping', required=True, help='Path to mapping JSON')
    parser.add_argument('--output', required=True, help='Path for output JSON')
    parser.add_argument('--openai-key', help='OpenAI API key')
    
    args = parser.parse_args()
    
    # Load index
    with open(args.index, 'r', encoding='utf-8') as f:
        ib_index = json.load(f)
    
    # Load mapping
    with open(args.mapping, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    
    # Match content
    matcher = ContentMatcher(ib_index, mapping, args.openai_key)
    matched_content = matcher.match_all_fields()
    
    # Save results
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(matched_content, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Matched content saved to: {args.output}")


if __name__ == '__main__':
    main()

