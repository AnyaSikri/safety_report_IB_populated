# IB-to-DSR Automation System

Automated Drug Safety Report (DSR) population from Investigator Brochure (IB) PDF using OpenAI.

## Overview

This system automates the population of a Drug Safety Report Word template using content extracted from an Investigator Brochure PDF. It uses a three-stage pipeline:

1. **PDF Indexer** - Extracts and indexes all content from the IB PDF
2. **Content Matcher** - Matches IB sections to DSR fields using AI (OpenAI GPT-4)
3. **Template Populator** - Populates the Word template with extracted content

## Features

- ✅ Automatic PDF text and table extraction
- ✅ Intelligent section identification and indexing
- ✅ AI-powered content synthesis using OpenAI
- ✅ Direct extraction for simple fields
- ✅ Word document template population with formatting preservation
- ✅ Comprehensive reporting of populated vs. unavailable fields
- ✅ Resume capability (cached index for faster reruns)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Setup Steps

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

2. **Set up OpenAI API key:**

Create a `.env` file in the project root:

```bash
echo "OPENAI_API_KEY=sk-your-api-key-here" > .env
```

Or export as environment variable:

```bash
export OPENAI_API_KEY=sk-your-api-key-here
```

## Usage

### Quick Start

Run the full pipeline with the provided files:

```bash
python main.py \
  --ib-pdf investigative_brochure.pdf \
  --template Drug_Safety_Report_Template.docx \
  --mapping IB_to_DSR_Manual_Mapping.md \
  --output data/output/DSR_Populated.docx \
  --openai-key sk-your-key
```

Or if you've set the environment variable:

```bash
python main.py \
  --ib-pdf investigative_brochure.pdf \
  --template Drug_Safety_Report_Template.docx \
  --mapping IB_to_DSR_Manual_Mapping.md \
  --output data/output/DSR_Populated.docx
```

### Command Line Options

```
Required Arguments:
  --ib-pdf PATH        Path to Investigator Brochure PDF
  --template PATH      Path to DSR Word template (.docx)
  --mapping PATH       Path to manual mapping markdown file
  --output PATH        Path for output populated DSR document

Optional Arguments:
  --openai-key KEY     OpenAI API key (or set OPENAI_API_KEY env var)
  --force-reindex      Force re-indexing of IB PDF (ignore cached index)
  --index-path PATH    Custom path for IB index file
  --intermediate-dir   Directory for intermediate files
```

### Stage-by-Stage Execution

You can also run individual stages:

#### Stage 1: Index IB PDF Only

```bash
python -m src.pdf_indexer \
  --input investigative_brochure.pdf \
  --output data/intermediate/ib_index.json
```

#### Stage 2: Parse Mapping Only

```bash
python -m src.mapping_parser \
  --input IB_to_DSR_Manual_Mapping.md \
  --output data/intermediate/mapping.json
```

#### Stage 3: Populate Template Only

```bash
python -m src.template_populator \
  --template Drug_Safety_Report_Template.docx \
  --content data/intermediate/matched_content.json \
  --output data/output/DSR_Populated.docx
```

## Project Structure

```
ib_template_matcher/
├── main.py                          # Main orchestration script
├── config.py                        # Configuration settings
├── requirements.txt                 # Python dependencies
├── .env                            # Environment variables (create this)
├── README_AUTOMATION.md            # This file
│
├── src/
│   ├── __init__.py
│   ├── pdf_indexer.py              # Stage 1: PDF extraction
│   ├── mapping_parser.py           # Mapping file parser
│   ├── content_matcher.py          # Stage 2: Content matching
│   └── template_populator.py       # Stage 3: Document population
│
├── data/
│   ├── intermediate/               # Cached index and matched content
│   └── output/                     # Generated DSR documents
│
├── investigative_brochure.pdf
├── Drug_Safety_Report_Template.docx
└── IB_to_DSR_Manual_Mapping.md
```

## How It Works

### Stage 1: PDF Indexing

The system extracts all text and tables from the IB PDF and creates a structured index:

- Identifies section headers (e.g., "1.1 Scientific Rationale", "5.5.1.2.4 Deaths")
- Tracks page ranges for each section
- Extracts metadata (drug name, RO number, etc.)
- Saves index as JSON for fast reuse

### Stage 2: Content Matching

Using the manual mapping file, the system matches IB content to DSR fields:

**Direct Extraction** - Simple fields copied verbatim:
- Drug name, RO number
- Approved indications
- Simple text fields

**AI Synthesis** - Complex fields requiring rewriting:
- Background sections
- Safety summaries
- Combined multi-section content
- Uses OpenAI GPT-4 for intelligent synthesis

**Unavailable** - Fields requiring external data:
- Individual case narratives
- Safety database queries
- Marked with placeholder messages

### Stage 3: Template Population

Replaces placeholders in the Word template:

- Finds all `[INSERT_*]` placeholders
- Replaces with matched content
- Attempts to preserve formatting
- Generates detailed population report

## Output Files

After running the pipeline, you'll find:

1. **Populated DSR Document**: `data/output/DSR_Populated.docx`
2. **IB Index**: `data/intermediate/ib_index.json` (cached for reuse)
3. **Matched Content**: `data/intermediate/matched_content.json` (for review)
4. **Population Report**: `data/output/population_report_YYYYMMDD_HHMMSS.json`

## Expected Results

### Success Metrics

✅ **70%+ of DSR fields populated automatically**
✅ **Direct extraction fields 100% accurate**
✅ **AI-synthesized content requires only minor edits**
✅ **Processing time under 5 minutes**
✅ **Clear reporting on unpopulated fields**

### Field Categories

**✓ Should Populate Perfectly:**
- Drug name, RO number, trade name
- Approved indications (verbatim from IB)
- Mechanism of action
- Basic pharmacology

**⚠ May Need Review:**
- AI-synthesized narratives
- Combined background sections
- Discussion sections

**⊘ Cannot Populate from IB:**
- Individual case narratives (need safety database)
- Epidemiological data (need literature)
- Real-time safety data

## Cost Estimates

### OpenAI API Usage

- **Model**: GPT-4 Turbo Preview recommended for quality
- **Estimated cost per run**: $2-5 USD
  - ~20-30 AI synthesis fields
  - ~500-1500 tokens per field
  - Total: ~15,000-45,000 tokens

**Cost Saving Options:**
1. Use GPT-3.5-turbo instead (10x cheaper, slightly lower quality)
2. Run only direct extraction first, review, then run AI synthesis
3. Cache results and only rerun changed sections

## Troubleshooting

### Common Issues

**1. OpenAI API Error: Rate Limit**
- Solution: Add delays between calls (see `config.py`)
- Or: Use slower model (GPT-3.5-turbo)

**2. PDF Extraction Issues**
- Problem: Text appears garbled
- Solution: Try different PDF library settings
- Workaround: Convert PDF to searchable format first

**3. Placeholder Not Replaced**
- Problem: Word document formatting splits placeholder
- Solution: Manually fix placeholder to be continuous text
- Check: Ensure placeholder matches exactly (case-sensitive)

**4. Missing Content**
- Problem: IB section not found in index
- Solution: Check section numbers in mapping file
- Workaround: Add section manually to index JSON

### Debug Mode

To debug issues, examine intermediate files:

```bash
# Check IB index structure
cat data/intermediate/ib_index.json | jq '.sections | keys'

# Check matched content
cat data/intermediate/matched_content.json | jq 'keys'

# Check specific field
cat data/intermediate/matched_content.json | jq '."[INSERT_DRUG_NAME]"'
```

## Advanced Usage

### Using GPT-3.5-turbo (Cheaper/Faster)

Edit `src/content_matcher.py` line 138:

```python
model="gpt-3.5-turbo",  # Instead of gpt-4-turbo-preview
```

### Customizing AI Prompts

Edit the `_create_extraction_prompt()` method in `src/content_matcher.py` to adjust how content is synthesized.

### Adding New Field Mappings

1. Edit `IB_to_DSR_Manual_Mapping.md`
2. Add new row to mapping table
3. Rerun pipeline (no code changes needed)

### Processing Different Documents

```bash
python main.py \
  --ib-pdf other_ib.pdf \
  --template other_template.docx \
  --mapping other_mapping.md \
  --output other_output.docx \
  --force-reindex
```

## API Key Security

⚠️ **Important**: Never commit your `.env` file or expose your API key!

**Best Practices:**
- Add `.env` to `.gitignore`
- Use environment variables in production
- Rotate keys regularly
- Monitor usage on OpenAI dashboard

## Performance Tips

1. **Cache the IB Index**: First run takes longer (PDF parsing), subsequent runs are fast
2. **Skip AI if not needed**: Comment out AI synthesis fields in mapping
3. **Batch process**: If doing multiple DSRs from same IB, reuse the index
4. **Parallel processing**: Modify code to process multiple fields concurrently

## Limitations

1. **PDF Quality**: Requires searchable text (not scanned images)
2. **Section Numbering**: Relies on consistent section number format
3. **Formatting**: May lose some Word document formatting
4. **AI Accuracy**: AI synthesis should be reviewed by human expert
5. **External Data**: Cannot populate fields requiring non-IB sources

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review intermediate JSON files for data issues
3. Check OpenAI API status and quotas
4. Examine error messages in console output

## License

This automation system is provided as-is for internal use.

## Version History

- **v1.0** - Initial release with OpenAI integration
  - Three-stage pipeline
  - GPT-4 Turbo support
  - Comprehensive reporting

