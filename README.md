# MonsterBot

## Dagens hjerneskade schedule

Administrators in any server where the bot is installed can change the shared
schedule. Posts continue to use MemeApi's existing webhook; no additional
configuration is needed. The command rejects direct messages and checks the
caller's Administrator permission even if Discord command permissions are overridden.

- `/hjerneskade_time start:14:30` posts at a fixed daily time.
- `/hjerneskade_time start:13:00 end:15:00` chooses a random minute each day.
- `/hjerneskade_time start:13:00 end:15:00 timezone:America/New_York` also sets
  the timezone. Only the Discord server owner can supply `timezone`.

Times use the saved timezone, defaulting to `Europe/Copenhagen`, including daylight
saving. Omitting `timezone` preserves the current setting. This remains one shared
schedule for the existing webhook, including when changed from another server.
Intervals must end on the same day. Settings and the daily random choice are stored by MemeApi.
Deploy MemeApi's schedule endpoint and timezone migration before this bot change,
then restart the bot to sync the command.

Run tests with `python -m unittest discover -s tests`.
