# Web Crawler + Gemini OCR Skill

> **Claude Code Skill** for web page crawling + image OCR
> **Created**: 2025-10-29
> **Inspired by**: Noah Brier's Claudesidian

## Quick Start

This skill **automatically activates** when you mention:
- "Analyze this URL: https://example.com"
- "Crawl this website"
- "Competitor site analysis"
- "Extract webpage with images"

## What It Does

1. **Firecrawl**: Extracts clean text (removes ads/clutter)
2. **Gemini OCR**: Analyzes images up to 20MB (bypasses Claude's 5MB limit)
3. **Complete Markdown**: Saves text + image analysis in one file

## Setup Complete ✅

- [x] SKILL.md created at `~/.claude/skills/web-crawler-ocr/SKILL.md`
- [x] API keys configured in `.env`
- [x] Python dependencies installed
- [x] Scripts ready at `~/.claude/skills/web-crawler-ocr/scripts/`

## Test It Now

Try these commands in Claude Code:

```
Analyze this URL: https://example.com
```

```
Crawl competitor cafe website: https://competitor-cafe.com
```

```
Extract content from this HFK page: https://hfk.me/team
```

## How It Works

**Model-Invoked Execution:**
1. You provide a URL
2. Claude detects the trigger keywords
3. Skill automatically executes web-crawler.py
4. Results saved to appropriate PKM location
5. Claude analyzes and summarizes

## PKM Integration

Results automatically saved to:
- **Competitor analysis**: `~/pkm/03-resources/competitor-analysis/`
- **Education reference**: `~/pkm/10-projects/12-education/{project}/`
- **General research**: `~/pkm/03-resources/web-research/`

## API Keys Configuration

Create `.env` file in `~/.claude/skills/web-crawler-ocr/scripts/`:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
```

**Note**: `.env` file is gitignored for security.

## Limitations

- **Gemini Free Tier**: 15 requests/minute
- **Firecrawl Free Tier**: 500 credits
- **Image Limit**: Max 10 images per page
- **File Size**: 20MB per image max

## Troubleshooting

### Check if skill is loaded
```bash
ls -la ~/.claude/skills/web-crawler-ocr/
```

### Verify API keys
```bash
cat ~/.claude/skills/web-crawler-ocr/scripts/.env
```

### Test script manually
```bash
cd ~/.claude/skills/web-crawler-ocr/scripts
source venv/bin/activate
python3 web-crawler.py "https://example.com" /tmp/test-output.md
```

## Version

- **v1.1.0** (2025-11-10): Restructured to follow official skills guidelines
  - Moved scripts into skill folder
  - Added requirements.txt and .gitignore
  - Removed exposed API keys from documentation
- **v1.0.0** (2025-10-29): Initial release

## Related Files

- **Skill Definition**: `~/.claude/skills/web-crawler-ocr/SKILL.md`
- **Scripts**: `~/.claude/skills/web-crawler-ocr/scripts/`
- **Config**: `~/.claude/skills/web-crawler-ocr/scripts/.env` (gitignored)
