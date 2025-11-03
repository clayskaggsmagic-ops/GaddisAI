# GaddisAI Cost Guide

## TL;DR

**Default cost: ~$0.08-$0.10 per deliberation** using gpt-4o-mini

**100 deliberations = ~$10**

---

## Cost Breakdown (per deliberation)

### With gpt-4o-mini (default, recommended)
- **Without memory**: $0.08
- **With memory**: $0.10

### With gpt-4-turbo (higher quality)
- **Without memory**: $0.20
- **With memory**: $0.25

### With gpt-4 (highest quality, most expensive)
- **Without memory**: $0.48
- **With memory**: $0.52

---

## What Uses Tokens?

**Per Deliberation:**
1. **SecDef recommendation**: ~2,500 input + 500 output tokens
2. **SecState recommendation**: ~2,500 input + 500 output tokens
3. **VP recommendation**: ~2,500 input + 500 output tokens
4. **President decision**: ~4,000 input + 800 output tokens

**Total per run**: ~11,600 input + 2,300 output tokens

**With memory enabled**: +100-200 tokens for memory retrieval (minimal cost)

---

## Cost Control Features

### 1. Automatic Cost Estimation
Before each run, you'll see:
```
💰 Cost Estimate: $0.085 per deliberation (3 advisors, gpt-4o-mini, with memory)
```

### 2. Per-Deliberation Cost Display
After each deliberation:
```
💰 This deliberation: $0.0842 (13,921 tokens)
```

### 3. Session Summary
When you exit:
```
============================================================
API USAGE SUMMARY
============================================================
Model: gpt-4o-mini
Input tokens: 69,600
Output tokens: 13,800
Total tokens: 83,400
Estimated cost: $0.8388
============================================================
```

---

## How to Control Costs

### Use gpt-4o-mini (default)
```bash
python src/main.py  # Uses gpt-4o-mini by default
```

### Run without memory (saves ~$0.02/run)
```bash
python src/main.py --no-memory
```

### Use gpt-4-turbo for better quality
```bash
python src/main.py --model gpt-4-turbo
```

### Set OpenAI spending limits
Go to https://platform.openai.com/account/limits and set:
- Monthly spending limit: $20 (or your preferred cap)
- Email alerts at: $10, $15

---

## Pricing Details (OpenAI, as of 2024)

### gpt-4o-mini
- Input: $0.150 per 1M tokens
- Output: $0.600 per 1M tokens
- **Best for**: Testing, development, most use cases

### gpt-4-turbo
- Input: $10.00 per 1M tokens
- Output: $30.00 per 1M tokens
- **Best for**: Production deliberations where quality matters

### gpt-4
- Input: $30.00 per 1M tokens
- Output: $60.00 per 1M tokens
- **Best for**: Maximum quality (rarely needed)

---

## Usage Projections

### Testing Phase (gpt-4o-mini, no memory)
- **10 test runs**: $0.80
- **50 test runs**: $4.00
- **100 test runs**: $8.00

### Production Phase (gpt-4o-mini, with memory)
- **10 deliberations**: $1.00
- **50 deliberations**: $5.00
- **100 deliberations**: $10.00
- **500 deliberations**: $50.00

### Production Phase (gpt-4-turbo, with memory)
- **10 deliberations**: $2.50
- **50 deliberations**: $12.50
- **100 deliberations**: $25.00

---

## Cost Optimization Tips

### 1. Start with gpt-4o-mini
Test output quality first. It's excellent for structured tasks like this.

### 2. Disable memory during testing
```bash
python src/main.py --no-memory --query "test question"
```

### 3. Batch similar questions
Run multiple related questions in one session to reuse context.

### 4. Turn off expensive features
In `config/memory.yaml`:
```yaml
importance:
  use_llm: false  # Already set to false by default

reflection:
  enabled: false  # Saves ~$0.008 per 10 deliberations
```

### 5. Monitor usage
System automatically tracks and displays costs. Watch for unexpected spikes.

---

## Real Cost Examples

### Example 1: Quick Test
```bash
python src/main.py --no-memory --query "Should we deploy to South China Sea?"
```
**Cost**: $0.07-$0.08

### Example 2: Session with 5 Queries
```bash
python src/main.py
# Ask 5 questions interactively
```
**Cost**: $0.40-$0.50 (with memory)

### Example 3: High-Quality Production Run
```bash
python src/main.py --model gpt-4-turbo --query "Iran nuclear response options?"
```
**Cost**: $0.20-$0.25

---

## Safety Nets

### 1. OpenAI Dashboard Limits
**Required**: Set spending limits in your OpenAI account before running.

### 2. Built-in Tracking
System shows costs after every run - you'll never be surprised.

### 3. Default to Cheapest Model
gpt-4o-mini is the default. You have to explicitly opt into expensive models.

### 4. No Hidden Costs
- Embedding calls are negligible ($0.00002 per 1K tokens)
- Memory storage is free (local ChromaDB)
- No ongoing subscription costs

---

## Questions?

**Q: How much for 1000 deliberations?**
A: ~$100 with gpt-4o-mini, ~$250 with gpt-4-turbo

**Q: Can I use a free tier?**
A: Yes, OpenAI gives $5-$18 in free credits initially. That's 50-200 free deliberations.

**Q: What if I run out of credits?**
A: System will fail gracefully with an API error. Set up billing or add more credits.

**Q: Can I reduce quality to save costs?**
A: gpt-4o-mini is already 90% cheaper than gpt-4 with minimal quality loss.

**Q: Will memory make it much more expensive?**
A: No - only adds ~$0.02 per deliberation (20% increase). Worth it for continuity.

---

## Recommendation

**For most users:**
1. Use default settings (gpt-4o-mini with memory)
2. Set $20 monthly limit in OpenAI dashboard
3. Run 10-20 test deliberations (~$2)
4. If quality is good, continue with same settings
5. Only upgrade to gpt-4-turbo if you need better quality

**Cost per 100 deliberations: ~$10** (very affordable)
