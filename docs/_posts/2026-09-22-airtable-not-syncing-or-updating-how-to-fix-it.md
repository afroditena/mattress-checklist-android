---
layout: post
title: "Airtable Not Syncing or Updating: How to Fix It"
date: 2026-09-22 09:00:00 +0900
tags: ["Airtable", "troubleshooting", "synced tables", "remote work tools", "no-code"]
---

![support.airtable.com official page screenshot](https://afroditena.github.io/mattress-checklist-android/assets/img/airtable-not-syncing-or-updating-how-to-fix-it/1.png)
*Screenshot of support.airtable.com ([source](https://support.airtable.com/docs/troubleshooting-syncs-in-airtable))*

If you see a warning icon (⚠️) on your synced table, the fix is almost always re-authentication: grab a fresh syncable view share link from the source, then in the destination base click the dropdown next to the synced table's name, choose **Update sync configuration**, and paste the new link. 
Airtable says this is the most common error message users see in synced tables — the error icon means the sync likely needs to be re-authenticated, which requires a new syncable view share link entered through Update sync configuration.


If there's no error icon and the table just looks stale, keep reading — that's a different problem with a different fix.

## Why This Happens

![support.airtable.com official page screenshot](https://afroditena.github.io/mattress-checklist-android/assets/img/airtable-not-syncing-or-updating-how-to-fix-it/2.png)
*Screenshot of support.airtable.com ([source](https://support.airtable.com/articles/2849803278-getting-started-with-airtable-sync))*

Airtable sync is a one-directional (or two-way, if configured) pull from a source view into a destination table. It breaks in a handful of predictable ways:

- **The share link changed at the source.** 
If the view share link is removed or regenerated at the source, the sync pauses until it's re-authenticated, and you'll see an error icon along with the time the table last synced.
 One person "cleaning up" share links can break every downstream table.
- **Nobody's been in the destination base.** 
Automatic syncs can stop running on a destination base that hasn't had recent activity — which looks exactly like a table that "hasn't updated in a while" even though the source is perfectly fine.

- **The source itself changed.** 
The share link may have been regenerated or its settings modified, and for sync integrations the source dataset may have been deleted or changed, or the connected account may no longer be valid.

- **Permission restrictions on the link.** 
Airtable respects password and email domain restrictions — if a view share link is restricted to a domain, you need an account on that domain to sync the view.

- **The sync is just slow or timed out.** 
Large source views can occasionally time out on the first attempt.

- **The base is overloaded.** 
If external integrations hit a base with requests around the clock, the request queue can get overloaded, making tables slow to load or even crash for human users.


## Step-by-Step Fixes

![support.airtable.com official page screenshot](https://afroditena.github.io/mattress-checklist-android/assets/img/airtable-not-syncing-or-updating-how-to-fix-it/3.png)
*Screenshot of support.airtable.com ([source](https://support.airtable.com/docs/third-party-integrations-common-troubleshooting))*

### 1. Check for the error icon first

Open the destination base and look at the synced table's name. 
A visible error icon ⚠️ on the synced table is how you identify a broken sync
, and it usually shows the time the table last synced successfully. That timestamp tells you whether this started an hour ago or three weeks ago.

No icon? Skip to step 4.

### 2. Re-authenticate with a fresh share link

At the source base, open the view being synced, create/copy a syncable view share link, then in the destination base: **table name dropdown → Update sync configuration → paste the new link**. 
Heads up: regenerating a share link affects every synced table that depends on that source
, so warn teammates before you do it in a shared workspace.

### 3. If the source is an external app, reconnect the account

For tables synced from Google Calendar, Jira, Salesforce, and similar integrations, the token is usually the culprit. 
Airtable suggests reconnecting the external account, and notes that some users have better luck removing the external account entirely and re-adding it as a new connection.
 
Those two steps — reconnect, then re-add as new — are Airtable's general starting point for third-party integration errors, followed by rebuilding the component from scratch.


### 4. Trigger a manual sync and wait a few minutes

If the table is simply stale, open the destination base and interact with it, then run a manual sync from the synced table's menu. This handles the inactivity pause described above. 
Airtable also recommends waiting a few minutes and retrying, since large source views can time out on the first attempt.


### 5. Test whether it's one view or the whole sync


Try syncing a different view from the same source base to see whether the error is specific to one view.
 If a second view syncs fine, the problem is in the original view's configuration, filters, or field set — not your account or the base.

### 6. Rebuild the sync

When configuration is suspect, start over. 
Airtable's own advice for syncs and automations is to try rebuilding that component from scratch, which can resolve a lot of configuration issues even though it's extra work.


### 7. Clear cache, then check base performance


Clearing your browser's cache and cookies is a standard part of Airtable troubleshooting.
 If the whole base feels sluggish, trim the load: 
formula fields — especially time-based ones using NOW() — can be taxing on large bases, so remove unnecessary formulas and use TODAY() instead of NOW() to reduce request load.
 
Also remove unneeded lookups, rollups, and formulas that reference linked records.


### 8. Contact support with specifics


If the error persists across views and users, contact Airtable Support with the source base, table, and view names.
 
Include a screen recording hosted online (Loom, Zight, etc.) rather than an MP4 attachment or a Google Drive upload, which often blocks their team from viewing it.
 
Also tell them roughly how many rows the source has, whether the sync worked before, and when it last synced correctly.


## How to Prevent It Next Time

![support.airtable.com official page screenshot](https://afroditena.github.io/mattress-checklist-android/assets/img/airtable-not-syncing-or-updating-how-to-fix-it/4.png)
*Screenshot of support.airtable.com ([source](https://support.airtable.com/articles/2512153420-troubleshooting-airtable-base-performance))*

- **Don't regenerate source share links casually.** Treat them as production infrastructure and document which destinations depend on each one.
- **Keep an eye on quiet destination bases.** If a base only gets opened once a month, expect its automatic sync to go dormant and plan on a manual refresh or an automation that touches it.
- **Simplify your sync topology.** 
For complex setups, Airtable recommends syncing data into a secondary base that acts purely as a sync source for downstream bases, so the original base only syncs to one destination.

- **Keep source views lean.** Fewer fields and filtered record sets sync faster and time out less.
- **Check status before you debug.** Airtable publishes a public status page; glance at it before tearing apart a working setup.