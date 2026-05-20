from fastapi import APIRouter
from fastapi.responses import StreamingResponse, JSONResponse
from models.schemas import ChatRequest
from services.database import db
import os
import json
import logging
from groq import Groq, APIError

router = APIRouter()
logger = logging.getLogger(__name__)

GROQ_MODEL = "llama-3.1-8b-instant"


def get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    return Groq(api_key=api_key if api_key else "no-key"), bool(api_key)


def build_system_prompt(ctx: dict) -> str:
    cat_json = json.dumps(
        {k: f"₹{v:,.0f}" for k, v in ctx.get("category_spending", {}).items()},
        indent=2,
        ensure_ascii=False,
    )
    return f"""You are FinanceAI, an expert personal finance assistant for Indian users. \
You help users manage money, optimize spending, plan budgets, and achieve financial goals.

=== Current Month Financial Context ===
Total Income  : ₹{ctx.get('total_income', 0):,.0f}
Total Expenses: ₹{ctx.get('total_expense', 0):,.0f}
Net Savings   : ₹{ctx.get('savings', 0):,.0f}
Savings Rate  : {ctx.get('savings_rate', 0):.1f}%

Category-wise Spending:
{cat_json}
========================================

Rules:
- Give specific, actionable, personalised financial advice based on the data above.
- Always use Indian Rupees (₹).
- For investments, recommend SIP, mutual funds, PPF, NPS, ELSS, FD as relevant.
- Be encouraging but honest about overspending.
- Never output raw reasoning chains, XML tags, or internal thoughts.
- Keep responses concise and well-structured."""


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.post("/chat")
async def ai_chat(request: ChatRequest):
    client, has_key = get_groq_client()
    ctx = db.get_financial_summary()

    if not has_key:
        resp = generate_demo_response(request.message, ctx)
        # Wrap demo response as SSE stream so the frontend works uniformly
        async def demo_stream():
            for word in resp["reply"].split(" "):
                yield _sse({"delta": word + " "})
            yield _sse({"done": True})
        return StreamingResponse(demo_stream(), media_type="text/event-stream")

    messages = [{"role": "system", "content": build_system_prompt(ctx)}]
    for msg in request.conversation_history[-20:]:  # cap history to last 20 turns
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": request.message})

    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.7,
            top_p=0.95,
            max_tokens=4096,
            stream=True,
        )

        def generate():
            try:
                for chunk in completion:
                    delta = chunk.choices[0].delta
                    content = getattr(delta, "content", None)
                    if content:
                        yield _sse({"delta": content})
                yield _sse({"done": True})
            except Exception as stream_err:
                logger.error(f"Streaming error: {stream_err}")
                yield _sse({"error": "Stream interrupted", "done": True})

        return StreamingResponse(generate(), media_type="text/event-stream")

    except APIError as e:
        logger.error(f"Groq API error: {e}")
        return JSONResponse(status_code=502, content={"detail": f"Groq API error: {e.message}"})
    except Exception as e:
        logger.error(f"Unexpected error in ai_chat: {e}", exc_info=True)
        resp = generate_demo_response(request.message, ctx)
        return JSONResponse(content={"reply": resp["reply"], "role": "assistant"})


@router.post("/chat/sync")
async def ai_chat_sync(request: ChatRequest):
    """Non-streaming fallback endpoint."""
    client, has_key = get_groq_client()
    ctx = db.get_financial_summary()

    if not has_key:
        return generate_demo_response(request.message, ctx)

    messages = [{"role": "system", "content": build_system_prompt(ctx)}]
    for msg in request.conversation_history[-20:]:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": request.message})

    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.7,
            top_p=0.95,
            max_tokens=4096,
            stream=True,
        )
        full_reply = ""
        for chunk in completion:
            content = getattr(chunk.choices[0].delta, "content", None)
            if content:
                full_reply += content
        return {"reply": full_reply.strip(), "role": "assistant"}

    except APIError as e:
        logger.error(f"Groq API error (sync): {e}")
        return JSONResponse(status_code=502, content={"detail": f"Groq API error: {e.message}"})
    except Exception as e:
        logger.error(f"Unexpected error in ai_chat_sync: {e}", exc_info=True)
        return generate_demo_response(request.message, ctx)


def generate_demo_response(message: str, ctx: dict) -> dict:
    msg = message.lower()
    income = ctx.get("total_income", 0)
    expense = ctx.get("total_expense", 0)
    savings = ctx.get("savings", 0)
    rate = ctx.get("savings_rate", 0)

    if any(w in msg for w in ["save", "saving", "savings"]):
        reply = f"""Great question about savings! 💰

Based on your current data:
- Monthly Income: ₹{income:,.0f}
- Monthly Expenses: ₹{expense:,.0f}
- Current Savings: ₹{savings:,.0f} ({rate:.1f}% savings rate)

My Recommendations:
1. Target 20-30% savings rate — You're at {rate:.1f}%. {'Great work!' if rate >= 20 else 'There is room to improve.'}
2. Automate savings — Set up an auto-transfer on salary day
3. SIP Investment — Consider ₹{income * 0.1:,.0f}/month in index funds
4. Emergency Fund — Maintain 6 months expenses (₹{expense * 6:,.0f}) in liquid funds

Would you like advice on any of these strategies?"""

    elif any(w in msg for w in ["invest", "investment", "mutual fund", "stock", "sip"]):
        reply = f"""Smart thinking about investments! 📈

Given your savings of ₹{savings:,.0f}/month, here's a recommended split:

1. Index Funds SIP — ₹{savings * 0.4:,.0f}/month → Nifty 50 (8-12% returns)
2. PPF — ₹{min(savings * 0.2, 12500):,.0f}/month → Tax-free, 7.1% guaranteed
3. Liquid Fund — ₹{savings * 0.2:,.0f}/month → Emergency reserve
4. ELSS — ₹{savings * 0.2:,.0f}/month → Tax saving under 80C

Rule of thumb: 60% equity, 40% debt at your stage.
Platforms: Zerodha, Groww, or Paytm Money."""

    elif any(w in msg for w in ["budget", "spend", "spending", "expense"]):
        cat = ctx.get("category_spending", {})
        top = max(cat, key=cat.get) if cat else "Shopping"
        reply = f"""Let's review your spending! 📊

This Month:
- Total Expenses: ₹{expense:,.0f}
- Highest: {top} (₹{cat.get(top, 0):,.0f})

50/30/20 Rule for you:
- 50% Needs: ₹{income * 0.5:,.0f}
- 30% Wants: ₹{income * 0.3:,.0f}
- 20% Savings: ₹{income * 0.2:,.0f}

Quick wins:
1. Cancel unused subscriptions
2. Cook at home 4 days/week
3. Use public transport
4. Buy groceries in bulk"""

    else:
        reply = f"""Hello! I'm FinanceAI — your personal finance advisor. 🏦

Your snapshot this month:
- 💵 Income: ₹{income:,.0f}
- 💸 Expenses: ₹{expense:,.0f}
- 💰 Savings: ₹{savings:,.0f} ({rate:.1f}%)

I can help with:
- 📊 Spending analysis
- 💡 Budget planning
- 📈 Investment advice (SIP, PPF, ELSS)
- 🎯 Goal planning
- 🔔 Saving tips

What would you like to explore?"""

    return {"reply": reply, "role": "assistant"}


@router.get("/insights")
def get_ai_insights():
    ctx = db.get_financial_summary()
    insights = []

    rate = ctx.get("savings_rate", 0)
    income = ctx.get("total_income", 0)
    cat = ctx.get("category_spending", {})

    if rate < 10:
        insights.append({"type": "warning", "icon": "⚠️", "title": "Low Savings Rate",
                         "message": f"Your savings rate is {rate:.1f}%. Aim for at least 20%."})
    elif rate >= 30:
        insights.append({"type": "success", "icon": "🎉", "title": "Excellent Savings!",
                         "message": f"You're saving {rate:.1f}% — consider investing the surplus in mutual funds."})
    else:
        insights.append({"type": "info", "icon": "💡", "title": "Savings on Track",
                         "message": f"Saving {rate:.1f}% this month. Push towards 30% for faster wealth growth."})

    food = cat.get("Food & Dining", 0)
    if income > 0 and food / income > 0.15:
        insights.append({"type": "info", "icon": "🍽️", "title": "Food Budget Check",
                         "message": f"Food spending ₹{food:,.0f} is {food/income*100:.1f}% of income. Meal prepping can help."})

    entertainment = cat.get("Entertainment", 0)
    if entertainment > 3000:
        insights.append({"type": "info", "icon": "🎭", "title": "Entertainment Costs",
                         "message": f"₹{entertainment:,.0f} on entertainment. Review unused subscriptions."})

    if cat.get("Investment", 0) == 0:
        insights.append({"type": "warning", "icon": "📈", "title": "No Investments This Month",
                         "message": "Start a SIP with even ₹500/month — compounding makes a big difference over time."})

    bills = cat.get("Bills & Utilities", 0)
    if income > 0 and bills / income > 0.20:
        insights.append({"type": "info", "icon": "⚡", "title": "High Utility Bills",
                         "message": f"Bills & Utilities are ₹{bills:,.0f} ({bills/income*100:.1f}% of income). Check for better plans."})

    if not insights:
        insights.append({"type": "success", "icon": "✅", "title": "Finances Look Healthy!",
                         "message": "Your spending patterns look great. Keep up the discipline!"})

    return {"insights": insights}
