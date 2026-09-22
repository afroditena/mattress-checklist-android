---
layout: post
title: "Loom Recording Not Uploading: How to Fix It"
date: 2026-09-22 09:00:00 +0900
tags: ["Loom", "troubleshooting", "remote work", "screen recording", "video tools"]
---

![support.atlassian.com official page screenshot](https://afroditena.github.io/mattress-checklist-android/assets/img/loom-recording-not-uploading-how-to-fix-it/1.png)
*Screenshot of support.atlassian.com ([source](https://support.atlassian.com/loom/kb/troubleshoot-a-video-stuck-in-processing/))*

**Quick fix:** Restart the Loom desktop app (or toggle the Chrome extension off and back on), wait a few minutes, and refresh the video link. 
Loom's own guidance is to reboot the app to recover your video, give it a few minutes to process, and refresh the video link.
 If that doesn't do it and you recorded with the desktop app, run the recording through Loom's recovery page at loom.com/recover-videos.

Before you panic: a video that's still spinning isn't necessarily lost. 
Loom only recommends troubleshooting once a video hasn't processed after 30 minutes.
 
Long recordings on a slow connection legitimately take longer, because Loom is still finishing the upload while it says "processing."


## Why This Happens

![support.atlassian.com official page screenshot](https://afroditena.github.io/mattress-checklist-android/assets/img/loom-recording-not-uploading-how-to-fix-it/2.png)
*Screenshot of support.atlassian.com ([source](https://support.atlassian.com/loom/kb/troubleshoot-and-fix-loom-video-upload-failures/))*

A Loom video isn't saved until it's been shipped to Loom's servers and transcoded. Anything that breaks that handoff leaves you staring at a stuck upload. The usual suspects:

- **A network hiccup mid-recording or mid-upload.** 
An interruption while recording or processing — a Wi-Fi drop, a dead internet connection — can stop your video from uploading successfully.

- **Slow upload speed.** 
Loom recommends at least 5 Mbps upload.
 Home connections are often asymmetrical, so your fast download speed tells you nothing.
- **The app crashed.** 
A crash can leave files that never upload.

- **Length and quality.** 
Longer videos take longer, and higher recording resolutions take longer still.
 
Multiple videos processing at once also slows things down.

- **File limits, if you're uploading an existing video rather than recording one.** 
A "Failed to process" message most often means the file is over 4 GB, over 60 fps, or above 4096 x 2160 resolution.

- **Corporate VPNs, proxies, and security software** that inspect or throttle large outbound uploads.

## Step-by-Step Fixes

![support.atlassian.com official page screenshot](https://afroditena.github.io/mattress-checklist-android/assets/img/loom-recording-not-uploading-how-to-fix-it/3.png)
*Screenshot of support.atlassian.com ([source](https://support.atlassian.com/loom/kb/fix-loom-videos-that-wont-play-or-load-desktop-app-only/))*

### 1. Wait out the 30-minute window

Boring, but it saves a lot of unnecessary work. 
Loom's support docs set the troubleshooting threshold at 30 minutes without processing.
 Keep the app or tab open while you wait — closing it mid-upload is how a recoverable video becomes an unrecoverable one.

### 2. Restart the recorder you used

**Desktop app:** quit Loom completely (don't just close the window — use the menu bar or system tray icon), reopen it, and let it resume. 
Loom's official fix for desktop videos that won't upload is the Recovery Page plus restarting the desktop app.


**Chrome extension:** 
Turn the Loom extension off and back on, then wait a few minutes and refresh the link.


### 3. Check your actual upload speed

Run a speed test and look at the *upload* number, not download. 
Loom recommends at least 5 Mbps upload for good results.
 If you're on hotel Wi-Fi, a crowded coffee shop, or a VPN, that's very likely your problem. Switch to a wired connection or turn off the VPN and let the upload retry.

### 4. Use Loom's recovery page

If the video is still stuck or missing from your library, go to **loom.com/recover-videos**. One important caveat: 
the recovery page only works for videos you own that were recorded with the Loom desktop app (screen only or screen + cam)
. 
Loom does not currently offer a recovery method for Chrome extension or mobile recordings
 — 
extension recordings aren't stored on your local machine, so missing parts can't be recovered.


### 5. Hunt for local video parts (desktop app only)


If the video still fails after restarting the app, check your local storage for unsaved video parts — Loom has separate instructions for the Mac and Windows apps — and if you find parts, send them to Support, who can sometimes manually repair the recording.
 Do this sooner rather than later: 
Loom notes that a video not processed successfully after 24 hours gets filtered out of your dashboard view.


### 6. Reset the extension or update your software


Loom's own checklist for common recording errors: restart Chrome and your device, reset the extension by right-clicking its icon and choosing Remove from Chrome, restart Chrome, then reinstall it — and make sure Chrome itself is up to date.
 
Clearing your Chrome cache via chrome://history/ → Clear Browsing Data is on the same list.
 On the desktop app, check for an app update too.

### 7. Re-encode the file (uploads, not recordings)

If you're uploading an existing MP4 and hitting "Failed to process," check it against Loom's limits first. 
Loom suggests running unsupported files through HandBrake — sometimes an underlying property, like too many audio channels, is the real blocker and re-encoding is the only fix.


### 8. Contact support

If local parts exist and nothing else worked, open a ticket and attach them. That's the path Loom itself points to for manual repair.

## How to Prevent It Next Time

![support.atlassian.com official page screenshot](https://afroditena.github.io/mattress-checklist-android/assets/img/loom-recording-not-uploading-how-to-fix-it/4.png)
*Screenshot of support.atlassian.com ([source](https://support.atlassian.com/loom/kb/quickly-fix-common-recording-errors/))*

- **Don't close the app or tab until the upload bar finishes.** This is the single biggest cause of unrecoverable Looms.
- **Use the desktop app for anything important.** It's the only recorder with an official recovery path.
- **Record at a lower resolution** for long videos. 
Higher recording quality means longer processing.

- **Break long recordings into chunks.** A 5-minute clip that uploads beats a 45-minute one that stalls — and people watch short Looms anyway.
- **Upload one at a time.** 
Multiple videos processing simultaneously is a documented cause of delays.

- **Get on a stable connection before you hit record,** and drop the VPN if your company allows it. 
Closing unnecessary tabs and background apps to free up resources is also on Loom's prevention list.