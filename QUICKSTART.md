# Quick Start Guide

## Installation (5 minutes)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

Or use the setup script:

```bash
chmod +x setup.sh
./setup.sh
```

### Step 2: Set Up OpenAI API Key

Create a `.env` file:

```bash
echo "OPENAI_API_KEY=sk-your-actual-api-key-here" > .env
```

Get your API key from: https://platform.openai.com/api-keys

### Step 3: Verify Installation

```bash
python test_system.py
```

## Running the Pipeline (2-5 minutes)

### Basic Usage

```bash
python main.py \
  --ib-pdf investigative_brochure.pdf \
  --template Drug_Safety_Report_Template.docx \
  --mapping IB_to_DSR_Manual_Mapping.md \
  --output data/output/DSR_Populated.docx
```

The system will:
1. ✓ Index the IB PDF (~30 seconds)
2. ✓ Match content to DSR fields (~2-3 minutes with AI)
3. ✓ Populate the Word template (~10 seconds)

### Output Files

After completion, check:

- **Populated DSR**: `data/output/DSR_Populated.docx`
- **Population Report**: `data/output/population_report_*.json`
- **Matched Content** (for review): `data/intermediate/matched_content.json`

## What to Expect

### ✅ Success Indicators

- 70%+ of fields populated automatically
- Direct extraction fields (drug name, etc.) 100% accurate
- AI-synthesized content coherent and relevant
- Clear report showing what was/wasn't populated

### ⚠️ Fields Requiring Manual Review

Some fields will be marked as unavailable:
- Individual case narratives (need safety database)
- External literature data
- Real-time safety information

These will show: `[DATA NOT AVAILABLE IN IB - REQUIRES: ...]`

## Troubleshooting

### "No OpenAI API key provided"
→ Set `OPENAI_API_KEY` in `.env` or pass `--openai-key` argument

### "PDF file not found"
→ Verify file path is correct relative to current directory

### "Rate limit exceeded"
→ Wait a few minutes, or switch to slower/cheaper model (edit `src/content_matcher.py` line 138 to use `gpt-3.5-turbo`)

### "Template not populating correctly"
→ Check `data/intermediate/matched_content.json` to verify content was extracted

## Cost Estimate

Typical run with GPT-4 Turbo:
- **~$2-5 USD** per complete DSR
- ~20-30 AI synthesis operations
- ~15,000-45,000 tokens total

To reduce costs:
- Use `gpt-3.5-turbo` (10x cheaper)
- Reuse cached IB index (don't use `--force-reindex`)

## Next Steps

1. Review the populated DSR document
2. Check the population report to see what fields need manual attention
3. Edit `data/intermediate/matched_content.json` if you want to refine specific fields
4. Re-run stage 3 only to apply manual edits:

```bash
python -m src.template_populator \
  --template Drug_Safety_Report_Template.docx \
  --content data/intermediate/matched_content.json \
  --output data/output/DSR_Populated_v2.docx
```

## Full Documentation

See `README_AUTOMATION.md` for:
- Detailed architecture explanation
- Advanced configuration options
- API customization
- Performance tuning
- Complete troubleshooting guide

## Support Workflow

If something goes wrong:

1. Run system test: `python test_system.py`
2. Check intermediate files: `ls -la data/intermediate/`
3. Review error messages in console output
4. Check OpenAI API status: https://status.openai.com/
5. Verify API key has credits: https://platform.openai.com/account/usage

