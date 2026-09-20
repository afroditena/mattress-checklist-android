---
layout: post
title: "Slack Notifications Not Working: How to Fix It"
date: 2026-09-20 09:00:00 +0900
tags: ["Slack", "troubleshooting", "remote work", "notifications", "team chat"]
---

![slack.com official page screenshot](https://afroditena.github.io/mattress-checklist-android/assets/img/slack-notifications-not-working-how-to-fix-it/1.png)
*Screenshot of slack.com ([source](https://slack.com/help/articles/360001559367-Troubleshoot-Slack-notifications))*

**The fastest fix:** check whether Do Not Disturb (the bell icon next to your profile picture) is on, and confirm your notification delivery is actually enabled in Slack's own preferences. On desktop, 
click your profile picture in the sidebar, select Preferences, then click Notifications, and under "How to notify you," make sure the box for Desktop notifications or Mobile notifications is checked
. That one toggle accounts for a huge share of "Slack went silent" complaints.

If that's already set correctly, work down the list below.

## Why This Happens

![slack.com official page screenshot](https://afroditena.github.io/mattress-checklist-android/assets/img/slack-notifications-not-working-how-to-fix-it/2.png)
*Screenshot of slack.com ([source](https://slack.com/help/articles/201355156-Configure-your-Slack-notifications))*

Slack notifications pass through several independent gates, and any one of them can quietly block an alert:

- **Do Not Disturb or a notification schedule** you set weeks ago and forgot about.
- **Workspace-level preferences** set to "Direct messages, mentions & keywords" (or nothing at all) instead of all messages.
- **Channel-level overrides.** 
You can set notification preferences for specific channels and DMs with three or more people, choose to be notified about all new posts or just mentions, and mute a conversation to turn off notifications entirely.
 A muted channel ignores your global settings.
- **Your operating system.** macOS Focus modes and Windows Focus/Do Not Disturb can suppress Slack even when Slack itself is configured perfectly.
- **Mobile timing settings.** Slack deliberately waits before pinging your phone so you don't get double-notified at your desk.
- **Battery savers and "optimization" apps.** Slack notes that 
power saving mode or performance optimization apps may prevent notifications, so try deactivating them or adding Slack to the allowlist.

- **A stale local cache or an out-of-date app.**

One more thing worth knowing if you use Slack in a browser: 
you'll only get notifications for workspaces you have open in your browser.


## Step-by-Step Fixes

![slack.com official page screenshot](https://afroditena.github.io/mattress-checklist-android/assets/img/slack-notifications-not-working-how-to-fix-it/3.png)
*Screenshot of slack.com ([source](https://slack.com/help/articles/360056534254-Manage-notifications-for-specific-channels-and-direct-messages))*

### 1. Turn off Do Not Disturb

Click the bell icon beside your profile picture in the top bar. If DND is active, resume notifications. While you're there, check whether you have a recurring notification schedule that's running longer than you intended.

### 2. Check your global notification preferences

Profile picture → **Preferences** → **Notifications**. Set "Notify me about" to whichever level you actually want. If you only want pings for @-mentions, that's fine — just know that's why quiet channels stay quiet.

Also check **Sound & appearance** in the same panel. 
Below Sound & appearance, you can check or uncheck "Show a badge on Slack's icon to indicate new activity."
 If badges aren't appearing, that's the setting.

### 3. Check the specific channel or DM

If only *one* conversation is silent, it's a channel-level override, not a global problem. 
Open the channel or group DM, click the Notifications icon at the top of the conversation and select All new posts or Just mentions.
 On mobile: 
tap the conversation name, tap Settings & Details, tap Notifications, and choose your preference.


### 4. Check your OS notification settings

- **macOS:** System Settings → Notifications → Slack. Allow Notifications on, alert style set to Banners or Alerts. Then check Control Center for an active Focus mode — Focus has its own allowed-apps list.
- **Windows:** Settings → System → Notifications. Confirm Slack is toggled on, then check that Focus assist / Do Not Disturb isn't running on a schedule.
- **iPhone:** Settings → Notifications → Slack.
- **Android:** Settings → Apps → Slack → Notifications.

### 5. Fix delayed mobile notifications

If pings arrive but arrive late, that's usually by design. 
Tap your profile picture at the top of the screen, tap Notifications, tap Notify Me on Mobile, then choose "As soon as I'm inactive."


### 6. Run Slack's built-in diagnostic (mobile)

Slack ships a real test tool, and it's underused. 
Restarting your phone or tablet sometimes fixes notification issues; if it doesn't, you can run a diagnostic test from the app, and depending on the results there may be additional steps to try.
 Find it at profile picture → **Notifications** → **Troubleshoot Notifications**. 
If the first four parts of the test pass but no test notification arrives, try uninstalling and reinstalling the Slack app, then re-run the test — and if that doesn't help, restart your device again.


### 7. Clear stuck badges

Different problem, different fix: if you see unread badges for messages you've already read, or Threads won't unbold, 
something may be out of sync — open the affected workspace in the desktop app or browser and press Shift + Esc
 to mark everything read.

### 8. Escalate to Slack

If nothing lands, send the diagnostic results in. 
Tap your profile picture → Notifications → Troubleshoot Notifications → Send a report
, and 
include a brief summary of the issue plus your workspace URL and email address.


## How to Prevent It Next Time

- **Audit DND monthly.** Notification schedules are the single most common self-inflicted cause.
- **Use mute deliberately.** Mute high-volume channels instead of dialing down your global settings — that way your important channels keep working.
- **Add Slack to your Focus mode allowlist** on macOS and iOS rather than relying on the general notification toggle.
- **Keep the app updated** and skip aggressive battery-saver apps on your work phone.
- **Set one device as your source of truth.** Settings don't sync across devices, so configure your phone and desktop separately and on purpose.