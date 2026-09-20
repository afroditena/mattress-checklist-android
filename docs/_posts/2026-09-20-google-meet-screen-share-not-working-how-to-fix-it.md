---
layout: post
title: "Google Meet Screen Share Not Working: How to Fix It"
date: 2026-09-20 09:00:00 +0900
tags: ["Google Meet", "screen sharing", "remote work", "troubleshooting", "video conferencing"]
---

![support.google.com official page screenshot](https://afroditena.github.io/mattress-checklist-android/assets/img/google-meet-screen-share-not-working-how-to-fix-it/1.png)
*Screenshot of support.google.com ([source](https://support.google.com/meet/answer/9308856))*

If you're on a Mac, the fix is almost always a system permission: go to **System Settings → Privacy & Security → Screen & System Audio Recording**, turn on the toggle for your browser (Chrome, Edge, Firefox) or the Meet app, then **quit and reopen it** and rejoin the call. On Windows, the usual culprit is the host or your Workspace admin — 
sharing your screen may be disabled for you due to admin settings (if you're part of a Workspace organization) or meeting host controls
.

## Why This Happens

![support.google.com official page screenshot](https://afroditena.github.io/mattress-checklist-android/assets/img/google-meet-screen-share-not-working-how-to-fix-it/2.png)
*Screenshot of support.google.com ([source](https://support.google.com/meet/answer/10619995))*

Screen sharing breaks in Meet for a handful of predictable reasons:

- **Missing OS-level screen recording permission.** macOS blocks apps from capturing your display until you explicitly allow it, and the permission only takes effect after the browser restarts.
- **Permissions that "look" enabled but aren't.** After a macOS or Chrome update, an already-on toggle can silently stop working and needs to be removed and re-added.
- **The host turned sharing off.** 
Meeting hosts can stop participants from sharing their screen.
 When that happens, the Present option simply isn't available to you.
- **Wrong entry point.** 
If you click Present in the green room before joining a meeting, you join in Companion mode — and your mic and speaker are unavailable in that mode.

- **No audio in the share.** This isn't broken sharing, it's the wrong share type. 
To share audio from your presentation, you have to present a tab and toggle on "Also share tab audio."

- **Browser or extension conflicts.** Old browser builds, aggressive privacy extensions, or Meet-specific extensions can block the capture prompt.

## Step-by-Step Fixes

![support.google.com official page screenshot](https://afroditena.github.io/mattress-checklist-android/assets/img/google-meet-screen-share-not-working-how-to-fix-it/3.png)
*Screenshot of support.google.com ([source](https://support.google.com/a/users/answer/11989526))*

### 1. Grant (or reset) screen recording permission on macOS

Google's own guidance for permission prompts: 
when you start a presentation or recording in a meeting, click Allow in the dialog — and if you missed that dialog, you'll need to update your system settings
.

1. Open **System Settings → Privacy & Security → Screen & System Audio Recording** (older macOS: System Preferences → Security & Privacy → Privacy → Screen Recording).
2. Toggle on your browser or the Google Meet app. If it's not listed, use the **+** button to add it.
3. Authenticate with your password or Touch ID if prompted.
4. Choose **Quit & Reopen** when macOS asks. The permission won't apply until the browser fully restarts.
5. Rejoin the meeting and try **Present now** again.

**If the toggle was already on and sharing still fails:** select the browser, hit the **–** button to remove it, then add it back and restart. macOS updates can leave this permission in a stale state.

### 2. Check host controls

If the Present button is missing or grayed out for you but works for others, the host has locked sharing. A host or co-host can fix it in seconds: 
join the meeting, click **Host controls** at the bottom right, and in the side panel toggle **Share their screen** on
. On mobile, 
tap the screen, tap **Host controls**, and turn **Share their screen** on or off at the bottom
.

If you're not the host, message them in chat — you can't override this yourself.

### 3. Make sure you actually joined the meeting

Don't click Present from the pre-join screen unless you mean to. 
Clicking Present in the green room puts you in Companion mode, where your mic and speaker are turned off.
 Join the meeting normally first, then share.

### 4. Use the right share type


At the bottom, click **Present now**, then pick **Your entire screen**, **A window**, or **Chrome Tab**.
 A few gotchas:

- **Video or audio playback?** Share a **tab**, not the whole screen, and turn on **Also share tab audio**.
- **Multiple monitors?** "Your entire screen" asks you to pick *one* display. Pick the one your content is actually on.
- **Someone else presenting?** 
Choose **Present instead** — starting your presentation pauses theirs.


### 5. Swap or reset the browser

Meet's deepest integration is with Chrome — 
presenting directly to Meet from Google Docs, Sheets, or Slides requires a computer and Chrome
. Try, in order:

1. Fully quit and reopen the browser (not just close the tab).
2. Update to the latest version.
3. Disable extensions — ad blockers, privacy tools, and Meet add-ons are common offenders. 
Some Chrome extensions for Meet can interfere with expected functionality.

4. Test in an incognito/private window with extensions off.
5. Try a different profile or a different browser to isolate the problem.

### 6. Rule out the network and the stop button

If you're clearly presenting on your end but attendees see a frozen or black screen, it's usually bandwidth. Turn off your camera, close bandwidth-heavy apps, switch from Wi-Fi to Ethernet if you can, or stop and restart the share. To stop cleanly, 
click **Stop Presenting** in the Meet window, or click **You are presenting → Stop presenting** at the bottom right
.

### 7. Ask your admin

If nothing works and you're on a work or school account, sharing may be disabled at the organization level. 
Admin settings can disable screen sharing for you.
 Your IT admin can confirm and change it.

## How to Prevent It Next Time

- **Grant the macOS permission before you need it.** Set it once in Privacy & Security and you'll never hit the mid-meeting scramble again.
- **Re-check permissions after big OS updates.** These toggles can reset or go stale.
- **Do a 30-second dry run** before any important demo — join a solo meeting from your own link and test Present now.
- **Keep a clean browser profile for meetings** with extensions kept to a minimum.
- **If you host recurring calls,** check your host controls once and confirm **Share their screen** is on. 
In recurring meetings or meetings that use the same code, presentation settings are saved for the next scheduled meeting.