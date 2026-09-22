---
layout: post
title: "Notion Not Syncing Across Devices: How to Fix It"
date: 2026-09-22 09:00:00 +0900
tags: ["Notion", "troubleshooting", "remote work", "productivity apps", "sync issues"]
---

![notion.com official page screenshot](https://afroditena.github.io/mattress-checklist-android/assets/img/notion-not-syncing-across-devices-how-to-fix-it/1.png)
*Screenshot of notion.com ([source](https://www.notion.com/help/reset-notion))*

# Notion Not Syncing Across Devices: How to Fix It

**The quickest fix: fully quit and reopen Notion on the device showing stale content, then sign out and sign back in.** If that doesn't do it, reset the app — 
on mobile you reset Notion by deleting the app and reinstalling it, and you won't lose data because it's synced to your account
.

## Why This Happens

![notion.com official page screenshot](https://afroditena.github.io/mattress-checklist-android/assets/img/notion-not-syncing-across-devices-how-to-fix-it/2.png)
*Screenshot of notion.com ([source](https://www.notion.com/help/notion-error-messages))*

Notion is cloud-first. Every device holds a local copy of your workspace, and sync breaks when that local copy and the server stop talking. The usual culprits:

- **A stale local cache or session.** The app keeps showing the old version of a page even though the server already has the new one.
- **Edits made offline that never uploaded.** 
Changes you make offline save locally and sync automatically the next time your device connects to the internet
 — but only if the app actually gets back online and stays open long enough.
- **Network or workplace restrictions.** Corporate firewalls, secure web gateways, and VPNs can quietly block Notion's traffic. Notion's own guidance is to 
allowlist the URL *.notion.com and update allow/deny rules in network controls like firewalls or secure web gateways
.
- **An unsupported or outdated platform.** 
Notion says to make sure you're on a supported device — Chromebooks and ChromeOS devices aren't supported, and you should use a browser like Chrome, Firefox, Safari, or Edge, or an Android or iOS device
. 
iOS 15 or earlier also isn't supported; upgrade to iOS 16 or later if your device allows it
.
- **A Notion-side outage.** 
Notion recommends checking its status page and X for live updates on known issues.

- **You're in the wrong workspace or account.** Sounds silly, but if your work laptop is logged into a personal account, nothing will "sync."

## Step-by-Step Fixes

![notion.com official page screenshot](https://afroditena.github.io/mattress-checklist-android/assets/img/notion-not-syncing-across-devices-how-to-fix-it/3.png)
*Screenshot of notion.com ([source](https://www.notion.com/help/guides/working-offline-in-notion-everything-you-need-to-know))*

Work down this list. Stop as soon as the page updates.

### 1. Force-quit and reopen (30 seconds)

Not just closing the window — quit the app entirely (Cmd+Q on Mac, close it from the tray on Windows, swipe it out of recent apps on mobile), then reopen. In a browser, reload the tab. 
Notion also suggests restarting your device and trying again.


### 2. Confirm it's not Notion's fault

Open the page on a second device or in a browser. If the newest version shows up there, the problem is local to one device. If it's stale everywhere, check Notion's status page before touching anything else.

### 3. Sign out and sign back in

This rebuilds your session and forces a fresh pull from the server. 
Notion lists logging out and back into your account as a standard troubleshooting step.
 Do it on the device that's behaving badly, not all of them at once.

### 4. Test in a different browser or incognito window


Notion recommends accessing it from a different device or browser, or from an incognito tab.
 If incognito shows the current version, you've got a cache or extension problem — move to the next step.

### 5. Clear the cache properly (browser)


Notion advises clearing local storage and cache in your browser, then quitting and restarting it.
 For a deeper clean, Notion's reset guide walks through it: 
open Developer Tools (Cmd+Option+I on Mac, Ctrl+Shift+I on Windows), right-click the refresh button, and select Empty Cache and Hard Refresh
. You can also 
go to Application in Developer Tools, expand Cookies, right-click the Notion entry, and select Clear
. On Safari, 
open the Safari menu → Preferences → Privacy → Manage Website Data, find Notion, and select Remove All
.

### 6. Reset the app


Before deleting the desktop app, make sure Notion is fully quit — not running in the background or system tray, and with no Notion processes left in Task Manager — then delete it
 and reinstall from Notion's site. On phones and tablets, 
delete the app and reinstall it
. 
Notion also says to make sure you're on the latest version.


One caution: if you have edits you made offline that never uploaded, get that device online and let it sync *before* you reset or reinstall.

### 7. Check the network, then escalate

Switch off the VPN, or hop to a different Wi-Fi network or your phone's hotspot. If sync works on cellular but not on the office network, the fix belongs to IT — send them Notion's allowlist guidance. Still stuck? 
Notion can use HAR file recordings to troubleshoot your issue
, so recording one before contacting support will save a round trip.

## How to Prevent It Next Time

- **Give the app a beat before closing your laptop.** Most "lost" edits are edits that never finished uploading.
- **Mark pages as available offline on every device you use.** 
Open the page, tap the ••• menu in the top-right corner, and turn on Available offline.
 
If a parent page has many sub-pages, mark each one you need.

- **Know the database limit.** 
When you download a database, the first 50 rows download automatically — download additional rows individually if you need them offline.

- **Audit what's actually saved.** 
The Offline tab in Settings shows pages downloaded by you or by Notion, and lets you remove them.

- **Do permission changes while you're online.** 
You can't share pages or change permissions offline, so handle that before you disconnect or after you're back.

- **Keep every device on the latest app version.** Sync bugs get patched; old builds keep them.