---
layout: post
title: "AI Coding Assistants in 2026: Who Should Pay"
date: 2026-10-01 09:00:00 +0900
tags: ["AI coding assistants", "GitHub Copilot", "Cursor", "Claude Code", "AI tool verdicts"]
---

![github.com official page screenshot](https://afroditena.github.io/mattress-checklist-android/assets/img/ai-coding-assistants-in-2026-who-should-pay/1.png)
*Screenshot of github.com ([source](https://github.com/features/copilot/plans))*

**My verdict:** If you write code most workdays, exactly one of these is worth paying for — and for most people it's the $10 or $20 entry tier, not the $100–$200 one. GitHub Copilot Pro is the right default if you live in VS Code and want predictable billing. Cursor Pro is worth it if you actually want the editor to make multi-file changes for you. Claude Code is worth it if your work happens in a terminal. They are *not* worth paying for if you code occasionally, if you're still learning fundamentals, or if you expect a flat fee — because in 2026 almost none of these are flat fees anymore. I'm leading with that because the hard part this year isn't picking a tool, it's not getting surprised by the bill.

## What's Actually Going On

![docs.github.com official page screenshot](https://afroditena.github.io/mattress-checklist-android/assets/img/ai-coding-assistants-in-2026-who-should-pay/2.png)
*Screenshot of docs.github.com ([source](https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing))*

The three mainstream options have converged on the same shape: a cheap seat, plus metered AI usage on top.

**GitHub Copilot.** 
Copilot is free for individuals with limits, $10/month for Pro, $39 for Pro+, $100 for Max, $19 per seat for Business and $39 per seat for Enterprise.
 
The free tier is capped at roughly 2,000 completions and 50 chat requests a month.
 The important change this year is billing: 
since June 1, 2026, all plans bill premium AI usage through GitHub AI Credits, where one credit equals $0.01, metered by tokens at each model's published rate, with each paid plan bundling a monthly allowance roughly equal to its price.
 
The $100 Max tier is explicitly aimed at sustained agent workflows and includes $100/month in credits.


**Cursor.** A separate editor rather than a plugin. 
Plans are Hobby (free), Pro ($20/mo), Pro+ ($60/mo), Ultra ($200/mo), Teams ($40/user/mo), and Enterprise (custom).
 
A June 2026 update added a $120/month Premium team seat with five times the included usage of a Standard seat, with annual prices lower.
 
Since August 24, 2026, Cursor retired its old flat Auto rate and bills usage at the list price of whichever model it routes your request to.


**Claude Code.** Anthropic's terminal agent, sold as part of a Claude subscription rather than on its own. 
It costs $20/month on Claude Pro (or $17/month if you pay $200 up front for the year), $100 on Max 5x and $200 on Max 20x; the free plan doesn't include it.
 
Claude Code is included in Pro, Max, Team and Enterprise, or you can run it on pay-as-you-go API billing instead.


A sourcing note, since this is a pricing post: the Copilot figures above trace to GitHub's own plans and billing docs. The Cursor and Claude numbers I pulled from pricing trackers that cite the vendor pages, not from the vendor pages directly, and credit-based plans move fast. Check the live page before you enter a card.

## Where It Breaks

- **"Unlimited" means completions, not agents.** Autocomplete is effectively unlimited on paid tiers. The expensive part — a model reading your repo and editing ten files — is metered.
- **Overage is the real price.** On Cursor, 
each paid plan includes a monthly usage pool drawn down at the underlying model's list price, with pay-as-you-go overages once it's exhausted.
 Set a spending cap on day one.
- **Team plans add a tax you won't see in the headline number.** 
Teams and Enterprise plans pay an extra $0.25 per million tokens on third-party models.

- **Automation gets billed separately from your chats.** On Claude, 
usage through the Agent SDK, headless CI pipelines, or third-party agents authenticating via your subscription draws from a separate monthly credit — $20 on Pro, $100 on Max 5x, $200 on Max 20x — rather than your interactive plan limits.

- **A stray environment variable can move your spending.** 
If `ANTHROPIC_API_KEY` is set, Claude Code uses that key instead of your subscription even while you're logged in, and the work bills per token to the API account that owns the key.

- **CI costs sneak in.** 
From June 1, 2026, Copilot code review workflows also consume GitHub Actions minutes.

- **Availability isn't guaranteed at the top end.** Copilot's $100 Max tier has had 
sign-ups paused
, so don't build a plan around it without checking.

## So Which One

| You are | Pay for | Why |
|---|---|---|
| In VS Code daily, want a boring bill | Copilot Pro, $10 | Cheapest serious seat; credits bundled roughly to plan price |
| Want the editor to do multi-file work | Cursor Pro, $20 | Agent-first editor, $20 pool included |
| Working in the terminal / on servers | Claude Pro, $20 | Claude Code included at the lowest paid tier |
| Running agents all day, every day | Max/Ultra tiers | Only tier where $100–$200 beats overage |
| Coding a few hours a week | Nothing | Copilot Free's 2,000 completions will cover you |

My take: the $200 tiers are rational only if you've already blown through a $20 pool two months running. Buying them pre-emptively is paying for a habit you don't have yet.

## What I Learned While Writing This (and What I Think)

Three things genuinely moved me off my prior.

First, the flat-fee era is over and nobody announced it loudly. GitHub kept its headline prices the same — 
Pro stayed $10, Pro+ $39, Business $19, Enterprise $39 when usage billing arrived
 — which reads like stability but isn't. Your bill now depends on how you work, not which plan you clicked.

Second, Cursor's August repricing to per-model list prices is a bigger deal than the plan table suggests, because it means your cost changes when the vendor changes routing. I think that's fair but uncomfortable, and I'd rather pay Copilot's slightly worse agent $10 for a predictable number than optimize a model-routing bill every month. Some teams will disagree, and they're right to if their agents genuinely save hours a week.

Third — and I want to flag this one carefully — secondary sources I came across report that Cursor's parent company was acquired in 2026. I could not confirm that on a vendor page, so treat it as unverified here. I'd still weigh ownership stability before standardizing a 50-person team on any one editor.

The honest limits of this piece: I read pricing and billing documentation, I did not run all three tools side by side for a month, and I have no benchmark of my own on code quality. If someone tells you one of these writes measurably better code than the others, ask what they measured. On cost, though, the pattern is clear enough — and I think the single most valuable thing you can do after subscribing is find the spending cap and turn it on before you forget.