# JanSamadhan - Design Notes (overrides screenshots where they conflict)

## Design tokens
- Maroon #7A0F2E | Saffron #F28C28 | Cream #FFF6EE
- Status colours: Submitted=maroon, Assigned=blue, In Progress=amber, Resolved=green, Critical=red
- Font: Noto Sans + Noto Sans Devanagari / Oriya / Bengali / Tamil / Telugu
- Cards: rounded-2xl, soft shadow. Pills: rounded-full. Reuse everywhere.

## LOGIN PAGE
1. Language chips are real i18n: selecting one switches the ENTIRE page + persists it.
   Use native letters: Hindi अ, Odia ଅ, Bengali অ, Marathi म, Tamil அ, Telugu అ.
   Verify the glyphs render correctly (Odia chip and Tamil name looked garbled in the image).
2. Citizen tab -> show only: +91 mobile field, Send OTP, then a 6-box OTP screen
   (resend timer, change number). Mock OTP = 123456.
3. Admin tab -> show only: Employee ID/Email + Password + Login + Forgot Password.
   Never show both forms at once (the screenshot does).
4. Continue as Guest -> role "guest": can chat and track, history not saved.
5. A+ / A / A- must resize the root font size, with an active state.
   The sun icon toggles high contrast. Helpline number is a tel: link.
6. Mobile validation: 10 digits, starts with 6-9, error + valid states.

## DASHBOARD
1. Stats strip shows the LOGGED-IN user's own numbers (seed: Total 3, Open 1,
   Resolved 2, Avg resolution 6 days). Platform-wide numbers go to the Impact page only.
2. The language switcher in the top bar must translate every label (this is the
   multilingual proof point). Persist the choice and sync it with the login choice.
3. Remove "By continuing you agree to Terms & Privacy" from the footer.
   Use instead: "Powered by AI, reviewed by officers. Helpline 1800-123-4567".
4. Floating button opens the chat widget (chat-bubble icon + small mic badge).
   Add bottom padding to the page so the tooltip never covers cards.
5. Dates must come from StatusHistory, not hardcoded:
   Submitted 28 Oct, Assigned 29 Oct, In Progress 30 Oct.
   My Updates feed uses the same timestamps.
6. Sidebar: Dashboard, AI Assistant, My Complaints, File via Form, Notifications(badge),
   Profile, Logout. Re-add "My Complaints" (the View All link goes there).
7. Show 3 complaint rows, e.g. GRV-1042 In Progress, GRV-0987 Resolved,
   GRV-0951 Resolved. Each row: department / category / urgency / language chips,
   and an SLA countdown ("2 days left") next to the expected date.
8. "System maintenance" announcement must use a future date (e.g. 10 Nov 2026).
   Split "My Updates" (user data) from "Announcements" (platform news).
9. Notification badge count (sidebar + bell) comes from one shared state.
10. All cards/buttons need hover and keyboard focus rings.
11. Reuse the robot icon from "File via Assistant" as the chat avatar.

## Behaviour that must work (not visible in screenshots)
- Roles: citizen / admin / guest with JWT; route guards.
- Status pill colours are identical in dashboard, tracking page and admin view.
- Mobile: sidebar becomes a bottom nav bar; login and dashboard stack vertically.

## Screens still to design (build from spec, no image yet)
Chat screen, Complaint detail/tracking, Notifications, Profile, Register,
Admin dashboard (KPIs + charts), Admin complaint table + detail, Hotspot map.

