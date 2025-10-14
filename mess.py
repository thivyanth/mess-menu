import os
import re
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


# Monday=1 .. Sunday=7
WEEKDAYS = [
	"Monday",
	"Tuesday",
	"Wednesday",
	"Thursday",
	"Friday",
	"Saturday",
	"Sunday",
]


def weekday_name(day: int) -> str:
	return WEEKDAYS[(day - 1) % 7]


def fetch_today(hostel: str = "Hostel 18"):
	data = requests.get(API, timeout=15).json()
	H = next(
		x
		for x in data
		if x.get("name") == hostel or x.get("short_name") == hostel.split()[-1]
	)
	# Python weekday: Monday=1..Sunday=7
	now = datetime.now(TZ)
	day = now.isoweekday()
	# After dinner grace end (22:00), treat "now" as next day's breakfast
	m = now.hour * 60 + now.minute
	if m >= 22 * 60:
		day = day % 7 + 1
	week = sorted(H["mess"], key=lambda x: x["day"])
	today = next(m for m in week if m["day"] == day)
	return H["name"], day, today, week


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


def next_slot_and_day(current_day: int) -> tuple[str, int]:
	"""Return the next distinct meal slot (not equal to NOW) and its day."""
	cur = slot_now()
	if cur == "breakfast":
		return "lunch", current_day
	if cur == "lunch":
		return "snacks", current_day
	if cur == "snacks":
		return "dinner", current_day
	# cur == "dinner"
	return "breakfast", (current_day % 7) + 1


def build_text(hostel_name: str, day: int, today: dict, week: list[dict]) -> str:
	now_slot = slot_now()
	updated_ts = datetime.now(TZ).strftime("%H:%M")

	def split_items(raw: str) -> list[str]:
		if not raw:
			return []
		text = raw.replace("\r", "\n").replace("\u00a0", " ")
		text = text.replace("\t", " ")
		text = text.replace("\ufeff", "")
		text = text.replace("\u2013", "-")
		text = text.replace('"', '')
		lines = []
		for line in text.split("\n"):
			line = line.strip()
			if not line:
				continue
			# Further split CSV-like lines, but keep slashes as-is
			parts = [p.strip() for p in re.split(r",+", line) if p.strip()]
			lines.extend(parts)
		cleaned = [clean(x) for x in lines if x]
		# De-duplicate while preserving order
		seen = set()
		result: list[str] = []
		for it in cleaned:
			if it not in seen:
				seen.add(it)
				result.append(it)
		return result

	def section(label: str, raw: str) -> list[str]:
		items = split_items(raw)
		if not items:
			return [f"{label}: -"]
		joined = "; ".join(items)
		return [f"{label}: {joined}"]

	lines = [
		f"{NOTE_TITLE}",
		f"{hostel_name} — Day {day} ({weekday_name(day)}) 🕒 {updated_ts} IST",
		"----------------------------------------",
	]
	lines += section(f"NOW ({now_slot.upper()})", today.get(now_slot, ""))
	lines += ["", *section("Lunch", today.get("lunch", ""))]
	lines += ["", *section("Snacks", today.get("snacks", ""))]
	lines += ["", *section("Dinner", today.get("dinner", ""))]

	# Append subsequent week's menu (next 6 days)
	lines += ["", "----------------------------------------", "Upcoming week:"]
	for offset in range(1, 7):
		dnum = ((day - 1 + offset) % 7) + 1
		dmenu = next(m for m in week if m["day"] == dnum)
		lines += ["", f"Day {dnum} ({weekday_name(dnum)})"]
		lines += section("Breakfast", dmenu.get("breakfast", ""))
		lines += ["", *section("Lunch", dmenu.get("lunch", ""))]
		lines += ["", *section("Snacks", dmenu.get("snacks", ""))]
		lines += ["", *section("Dinner", dmenu.get("dinner", ""))]

	return "\n".join(lines)


def upsert(sn: Simplenote, body: str) -> None:
	notes, _ = sn.get_note_list(tags=[NOTE_TAG])
	if notes:
		key = notes[0]["key"]
		note, _ = sn.get_note(key)
		note["content"] = body
		note["tags"] = list(set(note.get("tags", []) + [NOTE_TAG]))
		sn.update_note(note)
	else:
		sn.add_note({
			"content": body,
			"tags": [NOTE_TAG],
		})


def main() -> None:
	sn = Simplenote(os.environ["SIMPLENOTE_EMAIL"], os.environ["SIMPLENOTE_PASSWORD"])
	hostel_name, day, today, week = fetch_today(HOSTEL_NAME)
	body = build_text(hostel_name, day, today, week)
	upsert(sn, body)


if __name__ == "__main__":
	main()


