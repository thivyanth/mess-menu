import os
import requests
from datetime import datetime, date
from zoneinfo import ZoneInfo
from simplenote import Simplenote

API = "https://gymkhana.iitb.ac.in/instiapp/api/mess"
HOSTEL_NAME = os.getenv("HOSTEL_NAME", "Hostel 18")
NOTE_TITLE = os.getenv("NOTE_TITLE", "Hostel 18 Mess")
NOTE_TAG = os.getenv("NOTE_TAG", "mess-h18")
TZ = ZoneInfo("Asia/Kolkata")


def clean(s: str) -> str:
	return " ".join((s or "").split())


def fetch_today(hostel: str = "Hostel 18"):
	data = requests.get(API, timeout=15).json()
	H = next(
		x
		for x in data
		if x.get("name") == hostel or x.get("short_name") == hostel.split()[-1]
	)
	# Python weekday: Monday=1..Sunday=7
	day = date.fromtimestamp(datetime.now(TZ).timestamp()).isoweekday()
	today = next(m for m in H["mess"] if m["day"] == day)
	return H["name"], day, today


def slot_now() -> str:
	"""Return current meal slot in IST with 15-minute grace after each slot.

	Windows (IST):
	- breakfast: 07:30–09:45 (grace until 10:00)
	- lunch:     12:00–14:15 (grace until 14:30)
	- snacks:    16:30–18:15 (grace until 18:30)
	- dinner:    19:30–21:45 (grace until 22:00)

	Between 22:00 and 07:30, we show breakfast.
	"""
	now = datetime.now(TZ)
	m = now.hour * 60 + now.minute

	bf_start, bf_grace_end = 7 * 60 + 30, 10 * 60
	l_start, l_grace_end = 12 * 60, 14 * 60 + 30
	sn_start, sn_grace_end = 16 * 60 + 30, 18 * 60 + 30
	d_start, d_grace_end = 19 * 60 + 30, 22 * 60

	if m < bf_grace_end:
		return "breakfast"
	if m < l_grace_end:
		return "lunch"
	if m < sn_grace_end:
		return "snacks"
	if m < d_grace_end:
		return "dinner"
	return "breakfast"


def build_text(hostel_name: str, day: int, today: dict) -> str:
	now_slot = slot_now()
	lines = [
		f"# {NOTE_TITLE}",
		f"**{hostel_name} — Day {day}**",
		"",
		f"## Now ({now_slot.upper()})",
		"",
		f"{clean(today.get(now_slot, ''))}",
		"",
		"## Today",
		f"- Lunch:  {clean(today.get('lunch', ''))}",
		f"- Snacks: {clean(today.get('snacks', ''))}",
		f"- Dinner: {clean(today.get('dinner', ''))}",
	]
	return "\n".join(lines)


def upsert(sn: Simplenote, body: str) -> None:
	notes, _ = sn.get_note_list(tags=[NOTE_TAG])
	if notes:
		key = notes[0]["key"]
		note, _ = sn.get_note(key)
		note["content"] = body
		note["tags"] = list(set(note.get("tags", []) + [NOTE_TAG]))
		note["systemTags"] = list(set(note.get("systemTags", []) + ["markdown"]))
		sn.update_note(note)
	else:
		sn.add_note({
			"content": body,
			"tags": [NOTE_TAG],
			"systemTags": ["markdown"],
		})


def main() -> None:
	sn = Simplenote(os.environ["SIMPLENOTE_EMAIL"], os.environ["SIMPLENOTE_PASSWORD"])
	hostel_name, day, today = fetch_today(HOSTEL_NAME)
	body = build_text(hostel_name, day, today)
	upsert(sn, body)


if __name__ == "__main__":
	main()


