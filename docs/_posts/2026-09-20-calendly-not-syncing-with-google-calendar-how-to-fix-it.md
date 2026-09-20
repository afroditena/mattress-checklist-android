---
layout: post
title: "Calendly Not Syncing with Google Calendar: How to Fix It"
date: 2026-09-20 09:00:00 +0900
tags: ["Calendly", "Google Calendar", "remote work tools", "troubleshooting", "scheduling"]
---

![calendly.com official page screenshot](https://afroditena.github.io/mattress-checklist-android/assets/img/calendly-not-syncing-with-google-calendar-how-to-fix-it/1.png)
*Screenshot of calendly.com ([source](https://calendly.com/help/how-to-connect-your-google-calendar))*

## The Quick Fix

![calendly.com official page screenshot](https://afroditena.github.io/mattress-checklist-android/assets/img/calendly-not-syncing-with-google-calendar-how-to-fix-it/2.png)
*Screenshot of calendly.com ([source](https://calendly.com/help/connect-your-calendar-to-calendly))*

Go to **Settings → Scheduling → Calendars** in Calendly and check that the right calendars are selected under **Calendars to check for conflicts** — and that you've picked a destination under **Calendar to add events to**. 
Calendly's own help docs point to this screen: go to Settings → Scheduling → Calendars, then select which calendars to check under Calendars to check for conflicts and choose a calendar under Calendar to add events to.
 Nine times out of ten, a sub-calendar simply isn't checked off, or the event in Google is marked **Free** instead of **Busy**, which Calendly ignores.

## Why This Happens

![calendly.com official page screenshot](https://afroditena.github.io/mattress-checklist-android/assets/img/calendly-not-syncing-with-google-calendar-how-to-fix-it/3.png)
*Screenshot of calendly.com ([source](https://calendly.com/help/calendar-connections))*

A "sync failure" between Calendly and Google Calendar is almost never an outage. It's usually one of these:

- **The wrong sub-calendars are selected.** Calendly only blocks time from the calendars you explicitly check. Your "Personal" or "Family" calendar sitting under the same Google account won't count unless you select it.
- **Events are marked Free, not Busy.** 
Calendly removes times when events are set to Busy — including all-day or multi-day events — so an event marked Free won't block anything.

- **Sharing permissions are too limited.** For a calendar owned by someone else (a shared team calendar, a partner's calendar), 
you need to add the connected Google account under "Share with specific people" with permission set to "Make changes and manage sharing" so Calendly can see it as a sub-calendar to check for conflicts.

- **You changed sharing settings after connecting.** 
If sharing or calendar selections were updated after the initial connection, reconnecting the calendar often clears the glitch.

- **No destination calendar is set**, so booked meetings never write back to Google. 
Once connected properly, Calendly checks your calendar for busy times and adds new meetings to it — and if you've connected more than one calendar, you choose one as the main calendar for bookings.

- **Plan limits.** The number of calendars you can check for conflicts depends on your Calendly plan, so a second or third account may not be connectable on a free plan.

## Step-by-Step Fixes

![support.google.com official page screenshot](https://afroditena.github.io/mattress-checklist-android/assets/img/calendly-not-syncing-with-google-calendar-how-to-fix-it/4.png)
*Screenshot of support.google.com ([source](https://support.google.com/calendar))*

### 1. Verify your conflict-checking calendars (2 minutes)

Head to **Settings → Scheduling → Calendars**. 
If you signed up with a Google email address, your calendar may already be connected — if it's listed there, you're set on that front.
 Now look at the calendar list under the connected account and tick every sub-calendar that holds real commitments: Work, Personal, side-project, whatever. Unchecked calendars are invisible to Calendly.

Then confirm the **Calendar to add events to** field is pointing at the calendar you actually live in. If bookings are "disappearing," they're often landing on a secondary calendar you never look at.

### 2. Check the Free/Busy status of the events that got double-booked

Open one of the Google Calendar events that Calendly ignored, click into the event details, and look at the availability setting. Set it to **Busy** and save. Then refresh your Calendly booking page and confirm the slot is gone. Recurring events keep their original setting, so if a weekly block was created as Free, every instance is invisible to Calendly.

### 3. Fix sharing permissions on borrowed calendars

If the problem calendar belongs to another account, open Google Calendar on a desktop, hover the calendar in the sidebar, and open **Settings and sharing**. Under **Share with specific people**, add the Google address you connected to Calendly and set the permission level to **Make changes and manage sharing**. Read-only access isn't enough for Calendly to treat it as a conflict source. Then go back to Calendly's Calendars page and check the box for the newly shared calendar.

### 4. Disconnect and reconnect the calendar

This is the reset button, and it fixes stale OAuth tokens and permission changes that never propagated. 
Disconnect Google Calendar in Calendly, clear your browser cache and cookies, restart the browser, then reconnect Google Calendar.
 
Use Connect next to Google Calendar for your first calendar, or + Connect calendar account then Google Calendar to add another, and sign in when prompted.


Important: reconnecting resets your selections. Re-check your sub-calendars and your destination calendar afterward, then book a test meeting with yourself to confirm the event lands in Google.

### 5. Confirm you haven't hit your plan's calendar limit

If a second Google account won't connect at all — or connects but never appears in the conflict list — you may be at your plan's cap. 
Feature access can vary based on your plan, when your account was created, and any add-ons.
 Check your current plan before assuming it's a bug.

### 6. Rule out event-type-level settings

Sometimes the calendar sync is fine and the event type is the culprit. Open the event type and review its availability rules. 
Go to your Scheduling page, select the event type, choose More options, and open the section you want to edit — including limits and buffers, free/busy rules, and booking page options — then save and check your booking page.
 Buffers and daily meeting limits can make availability look broken when sync is actually working.

### 7. Contact support with specifics

If everything is connected and correct but events still aren't writing to Google, it's a backend issue. Reach out through in-app chat or Calendly support with the date, time, and invitee for a specific failed booking — vague reports get slow answers.

## How to Prevent It Next Time

- **Default new Google events to Busy.** Check your Google Calendar settings so newly created events aren't defaulting to Free.
- **Re-audit your calendar list after any change** — a new work account, a new sub-calendar, a password reset, or a reconnect. Selections don't carry over automatically.
- **Run a monthly test booking.** Book yourself through your own public link and confirm the event appears in Google within a minute. It takes 30 seconds and catches silent failures before a client does.
- **Keep the destination calendar the same as a conflict-checked calendar.** That way every Calendly booking immediately blocks future availability instead of leaving a gap.
- **Don't stack too many calendar accounts.** Every extra connection is another place for permissions to break. Consolidate with sub-calendars under one Google account where you can.