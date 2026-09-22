---
layout: post
title: "Trello Cards Not Loading: How to Fix It"
date: 2026-09-22 09:00:00 +0900
tags: ["Trello", "troubleshooting", "project management", "remote work", "productivity tools"]
---

![support.atlassian.com official page screenshot](https://afroditena.github.io/mattress-checklist-android/assets/img/trello-cards-not-loading-how-to-fix-it/1.png)
*Screenshot of support.atlassian.com ([source](https://support.atlassian.com/trello/docs/troubleshooting-browser-issues-with-trello/))*

# Trello Cards Not Loading: How to Fix It

**Quick fix:** In nine out of ten cases, a board filter is hiding your cards or your browser cache is stale. Look at the top of your board for an active filter and clear it — then, if cards are still missing, hard-refresh the page and clear your browser cache for trello.com, which is Atlassian's own first-line fix for browser issues with Trello.

## Why This Happens

![support.atlassian.com official page screenshot](https://afroditena.github.io/mattress-checklist-android/assets/img/trello-cards-not-loading-how-to-fix-it/2.png)
*Screenshot of support.atlassian.com ([source](https://support.atlassian.com/trello/docs/troubleshooting-a-slow-board/))*

Trello is a single-page web app, so "cards not loading" usually isn't a data-loss problem — it's a display or delivery problem. The usual suspects:

- **An active filter or a saved view.** If you filtered by a label, member, or due date and never cleared it, the rest of the board is still there — you just can't see it.
- **Stale browser cache or blocked cookies.** Atlassian's support docs specifically call out cookies as a factor and list 
id.atlassian.com, auth.atlassian.com, and trello.com as the domains that need to be allowed in your browser's site settings
.
- **Browser extensions.** Ad blockers, privacy tools, and Trello-specific extensions can intercept requests or hide cards. Atlassian's browser troubleshooting article covers extensions as a distinct step.
- **A board that's simply too big.** 
Trello has to load open cards and attachments every time a board opens, so boards with a lot of open cards load slowly — Atlassian recommends staying under 1,000 open cards per board, and under 500 if the cards carry a lot of attachments or checklists.

- **A Trello-side incident.** Sometimes it's not you. Atlassian runs a public status page for Trello at trello.status.atlassian.com.
- **Local app data problems** on the desktop or mobile apps.

## Step-by-Step Fixes

![support.atlassian.com official page screenshot](https://afroditena.github.io/mattress-checklist-android/assets/img/trello-cards-not-loading-how-to-fix-it/3.png)
*Screenshot of support.atlassian.com ([source](https://support.atlassian.com/trello/docs/troubleshooting-for-the-desktop-app-windows-and-macos/))*

### 1. Clear any active board filter

Open the board and check the top bar. If it shows that filters are applied, open the filter menu and clear everything. This is the single most common cause of "my cards disappeared," and it takes five seconds to rule out.

While you're in there, a handy trick from Atlassian's docs: 
open the filter menu and type an asterisk (*) in the keyword field to display all cards on the board — the total count appears at the top of the results.
 If the count looks right, your cards exist and this is purely a display issue.

### 2. Hard-refresh the page

Press **Ctrl + Shift + R** (Windows) or **Cmd + Shift + R** (Mac). This forces the browser to pull fresh files instead of reusing cached ones. If lists render but cards stay blank, this fixes it surprisingly often.

### 3. Test in a private/incognito window

Open a private window and log into Trello. Incognito runs without most extensions and with a clean cache, so if your cards load there, you've confirmed the problem is local — move on to steps 4 and 5.

### 4. Clear your cache and check cookie permissions

Atlassian's browser troubleshooting guide walks through clearing your web browser's cache and allowing cookies as core steps. In Chrome, go to **Settings → Privacy and security → Delete browsing data**, and clear cached images and files. Then confirm that cookies aren't blocked for trello.com, id.atlassian.com, and auth.atlassian.com — if any of those are blocked by a strict privacy setting, Trello can fail to authenticate and render an empty board.

### 5. Disable extensions one at a time

Turn off ad blockers, VPN browser extensions, and any third-party Trello add-ons, then reload. Re-enable them one by one to find the culprit. Corporate-managed browsers sometimes install security extensions you didn't choose — worth checking if you're on a work laptop.

### 6. Check Trello's status page

Head to **trello.status.atlassian.com**. If there's an active incident, stop troubleshooting and wait it out. Nothing on your end will fix a server-side problem.

### 7. Fix the desktop app specifically

If you're on the Mac or Windows desktop app, Atlassian's guidance is to 
close the app completely, reboot your device, and reopen it — and if that doesn't work, clear the app's cache by opening the "Help" menu and using the "Reset local data" option, then fully close and relaunch the app
. 
Antivirus, firewall, VPN, and network proxy settings can also interfere.


### 8. Fix the mobile app

On Android, Atlassian's sequence is to 
close the app completely and reopen it first, then try clearing the cache, logging out and back in, or reinstalling the app
. One important caveat: 
these actions clear any offline changes you've made that haven't synced yet, so check for unsent changes before you do them.


### 9. Trim an oversized board

If a specific board is the only one that struggles, it's probably too heavy. Atlassian suggests archiving what you're not actively using: 
archiving a list stops it from loading every time you open the board, while still letting you un-archive it later and search for those cards.
 Archived cards aren't deleted — they stay searchable.

### 10. Grab the console error

If nothing works, capture the error before you contact support. Atlassian's docs list the shortcuts: 
Chrome uses Cmd+Opt+J (Mac) or Ctrl+Shift+J (Windows), Firefox uses Cmd+Opt+K or Ctrl+Shift+K, and in Safari you enable the "Develop" menu under the Advanced tab in Preferences.
 A screenshot of the console gets you a real answer much faster than "it doesn't work."

## How to Prevent It Next Time

![support.atlassian.com official page screenshot](https://afroditena.github.io/mattress-checklist-android/assets/img/trello-cards-not-loading-how-to-fix-it/4.png)
*Screenshot of support.atlassian.com ([source](https://support.atlassian.com/trello/docs/troubleshooting-for-the-android-app/))*

- **Archive aggressively.** Move completed lists to the archive monthly instead of letting a board balloon past a thousand cards.
- **Split giant boards.** One board per quarter or per project beats one mega-board that takes 20 seconds to render.
- **Keep trello.com whitelisted** in your ad blocker and cookie settings, especially if you use strict privacy extensions.
- **Bookmark the status page.** Checking trello.status.atlassian.com first saves you from reinstalling apps during an outage.
- **Stay on a supported, updated browser.** Most stubborn rendering bugs trace back to an out-of-date browser build.