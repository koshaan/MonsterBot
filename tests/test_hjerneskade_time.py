import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import requests
import poll_bot


class ScheduleCommandTests(unittest.IsolatedAsyncioTestCase):
    def interaction(self, administrator=True, guild_id=123):
        return SimpleNamespace(
            guild_id=guild_id,
            guild=SimpleNamespace(owner_id=1),
            user=SimpleNamespace(id=2),
            permissions=SimpleNamespace(administrator=administrator),
            response=SimpleNamespace(send_message=AsyncMock(), defer=AsyncMock()),
            followup=SimpleNamespace(send=AsyncMock()),
        )

    async def test_rejects_non_admin_and_dm_without_api_call(self):
        for admin, guild in [(False, 123), (True, None)]:
            with self.subTest(admin=admin, guild=guild):
                interaction = self.interaction(admin, guild)
                with patch.object(requests, "put") as put:
                    await poll_bot.hjerneskade_time.callback(interaction, "13:00")
                put.assert_not_called()
                interaction.response.send_message.assert_awaited_once()
                self.assertTrue(interaction.response.send_message.call_args.kwargs["ephemeral"])

    async def test_rejects_invalid_times_and_reversed_interval(self):
        for start, end in [("24:00", None), ("1pm", None), ("13:00", ""), ("13:00", "12:00")]:
            with self.subTest(start=start, end=end):
                with patch.object(requests, "put") as put:
                    await poll_bot.hjerneskade_time.callback(self.interaction(), start, end)
                put.assert_not_called()

    async def test_admin_can_set_fixed_time_or_interval(self):
        for end, guild in [(None, 123), ("15:00", 456)]:
            interaction = self.interaction(guild_id=guild)
            with patch.object(poll_bot, "API_HOST", "https://api.example/"), \
                 patch.object(poll_bot, "BOT_SECRET", "test-secret"), \
                 patch.object(requests, "put", return_value=Mock(status_code=200, json=Mock(return_value={"timeZone": "America/New_York"}))) as put:
                await poll_bot.hjerneskade_time.callback(interaction, "13:00", end)
            put.assert_called_once_with(
                "https://api.example/memeoftheday/schedule",
                headers={"Bot_Secret": "test-secret"},
                json={"start": "13:00", "end": end, "timeZone": None}, timeout=15,
            )
            interaction.followup.send.assert_awaited_once()
            self.assertTrue(interaction.followup.send.call_args.kwargs["ephemeral"])
            self.assertIn("America/New_York", interaction.followup.send.call_args.args[0])

    async def test_admin_who_is_not_owner_cannot_set_timezone(self):
        interaction = self.interaction()
        with patch.object(requests, "put") as put:
            await poll_bot.hjerneskade_time.callback(interaction, "13:00", timezone="UTC")
        put.assert_not_called()
        self.assertIn("Only the server owner", interaction.response.send_message.call_args.args[0])

    async def test_owner_can_set_timezone(self):
        interaction = self.interaction()
        interaction.user.id = interaction.guild.owner_id
        with patch.object(poll_bot, "API_HOST", "https://api.example/"), \
             patch.object(requests, "put", return_value=Mock(status_code=200, json=Mock(return_value={"timeZone": "UTC"}))) as put:
            await poll_bot.hjerneskade_time.callback(interaction, "13:00", "15:00", timezone="UTC")
        self.assertEqual({"start": "13:00", "end": "15:00", "timeZone": "UTC"}, put.call_args.kwargs["json"])
        self.assertIn("UTC", interaction.followup.send.call_args.args[0])

    async def test_invalid_timezone_reports_validation_error(self):
        interaction = self.interaction()
        interaction.user.id = interaction.guild.owner_id
        with patch.object(poll_bot, "API_HOST", "https://api.example/"), \
             patch.object(requests, "put", return_value=Mock(status_code=400)):
            await poll_bot.hjerneskade_time.callback(interaction, "13:00", timezone="MadeUp/TimeZone")
        self.assertIn("Invalid schedule or timezone", interaction.followup.send.call_args.args[0])

    async def test_api_failure_does_not_report_success(self):
        interaction = self.interaction()
        with patch.object(poll_bot, "API_HOST", "https://api.example/"), \
             patch.object(requests, "put", side_effect=requests.Timeout):
            await poll_bot.hjerneskade_time.callback(interaction, "13:00")
        self.assertIn("Could not confirm", interaction.followup.send.call_args.args[0])

    def test_command_is_administrator_only_and_guild_only_by_default(self):
        self.assertTrue(poll_bot.hjerneskade_time.guild_only)
        self.assertTrue(poll_bot.hjerneskade_time.default_permissions.administrator)
