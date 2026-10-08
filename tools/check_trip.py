#!/usr/bin/env python3
"""
Trip fact checker — run before every commit that touches travel/china-2026/.

    python3 tools/check_trip.py

Every confirmed fact (times, booking references, decisions) is written ONCE,
below. The script checks every trip file against it and fails loudly on
anything stale or contradictory. When a fact changes, change it here FIRST,
then run the script — it will list every line that still has the old value.
"""
import re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
TRIP = ROOT / "travel" / "china-2026"
FILES = sorted(TRIP.glob("*.md"))
FAMILY = ROOT / "family" / "where-alexandra-is.md"   # shared with family — no private info

# Never on the family page: (regex, why)
PRIVATE = [
    (r"PIN|\b\d{4}\.\d{3}\.\d{3}\b|\b5515\d+|BLR\d+|XF7\w+|EASDQZ|ECFV7Q|MESQ54|e-ticket|[Ss]eat \d|12956761|99987084", "Booking refs, PINs and seats stay private"),
    (r"₪|\$\d|£|THB|HKD|CNY|¥|[Pp]aid|[Cc]ost", "Money stays private"),
    (r"(?i)48 hours|no word", "No 48-hour rule on the family page"),
    (r"(?i)passport|alipay|monzo|card|ssri|medication|pill|azithro|imodium|kalbeten|vaccin|packing|outfit|bra\b|knickers", "Personal details stay private"),
]

# ---------------------------------------------------------------------------
# 1. Values that must never appear anywhere: old, cancelled or wrong.
#    (regex, why it is wrong)
# ---------------------------------------------------------------------------
FORBIDDEN = [
    (r"\bLY83\b",                    "Outbound changed to LY85, Sun 11 Oct 00:05"),
    (r"Wed 14 Oct.{0,20}Ben Gurion|Ben Gurion.{0,20}14 Oct|22:15", "At Ben Gurion Sat 10 Oct by 21:05, not 14 Oct"),
    (r"07:45",                       "Canalis shuttle is 07:00 — there is no 07:45"),
    (r"LockCha",                     "LockCha was cancelled"),
    (r"King Studio",                 "Sindhorn room was upgraded"),
    (r"pay at property",             "Sindhorn is charged automatically on 2 Oct"),
    (r"₪\s?2,020|₪\s?2,771|₪\s?4,326", "Sindhorn is THB 30,498.42, charged 2 Oct"),
    (r"(?i)optional:?\*?\*? \*?\*?REstore", "REstore is a must on Monday"),
    (r"\bBaidu\b",                   "Using Apple Maps, not Baidu"),
    (r"Japan",                       "Trip is China & Bangkok — check any 'Japan' is a brand, then allowlist"),
    (r"Quarry Bay",                  "Going to Harbour Plaza by Uber, not MTR"),
    (r"\bTala\b",                    "Tala flares were cut"),
    (r"Uniqlo long black",           "Uniqlo long black trousers were cut"),
    (r"\b[Nn]avy\b",                 "Navy top was swapped for the Asics"),
    (r"[Cc]omfy bra",                "Wired comfy bra was cut — 4 bras"),
    (r"[Ss]unscreen lotion|roll-on sunscreen", "Sunscreen stick only — lotion and roll-on cut"),
    (r"2-in-1",                      "Buying shampoo + conditioner in HK"),
    (r"500[–-]750",                  "CNY plan is 1,200–1,500"),
    (r"\$500",                       "Not carrying a USD fund"),
    (r"15,000[–-]20,000|10,000 THB|~10,000", "Bangkok withdrawal is ~8,000 THB"),
    (r"09:30[–-]13:00",              "Chatuchak is 11:00–14:00"),
    (r"Stradivarius",                "Stradivarius bra tops not bringing"),
    (r"[Cc]rocs",                    "Flip-flops, not Crocs — Crocs too bulky"),
    (r"KOKONI|Vaso",                 "Removed/unverified venue"),
    (r"❓",                          "Unconfirmed marker left in — resolve it"),
    (r"Israeli (for|passport —) ?(Hong Kong|HK|Thailand)|Israeli or UK", "UK passport for HK and Thailand; Israeli only at Ben Gurion"),
    (r"[Pp]ending pharmacist|Still to confirm with the pharmacist", "Pharmacist questions dropped by Alexandra"),
    (r"(?i)(azithromycin|kalbeten)\W{0,6}🛒|🛒\W{0,6}(azithromycin|kalbeten)", "Azithromycin and Kalbeten are collected"),
    (r"(Canalis|6637\.638\.401).*prepaid", "Canalis is NOT prepaid — pay at check-in"),
    (r"(Sindhorn|6761\.193\.363).*(charged automatically|THB 30,498\.42, charged)", "Sindhorn is paid"),
    (r"(?i)black short-sleeve|plain black\*\*|black one needs", "Plain short-sleeve is now grey, not black"),
    (r"\bFloat\*\* \(black|Float\)|Dylan green, Float", "Float bra replaced by a regular bra"),
    (r"(?i)\bmodal\b", "Amazon modal top was cut"),
    (r"(?i)hand warmers?",           "Hand warmers not bringing"),
    (r"(?i)antihistamine|cable organiser", "Not bringing: antihistamine, cable organiser"),
    (r"Sheung Wan.{0,5}3 stops|Island Line to Sheung Wan · 3", "Admiralty → Sheung Wan is 2 stops"),
    (r"Elements.*1 stop", "Elements is not 1 MTR stop from TST"),
    (r"twin-sharing for 15", "Twin-share all 16 tour nights"),
    (r"Khaki ² over", "Wed 28 is the Shein striped shirt — khaki would be a 4th wear"),
    (r"Eden",                        "The striped shirt is Shein, not Eden"),
    (r"Decathlon, Israel", "Warm hat and gloves bought in Hong Kong, not Israel"),
    (r"(?i)backup: Xi'an", "Hat and gloves: Hong Kong only — no shopping time in China"),
    (r"(?i)uniqlo.{0,10}TST|warm hat 🛒|gloves 🛒", "Hat and gloves already bought in Israel"),
    (r"(?i)hotel.{0,5}(—|\()?\s*to book|details to follow", "Bangkok hotel 11–15 Oct is booked: Pullman G"),
    (r"Tue 14 Oct",                  "14 Oct 2026 is a Wednesday"),
    (r"(?i)union mall.{0,20}one stop", "Union Mall is two MRT stops from Kamphaeng Phet"),
    (r"One walk north",              "Sarnies is a backtrack south"),
    (r"~?10:45.*(Beijing|PEK|DiDi)|(Beijing|PEK|DiDi).*10:45", "Leave Beijing hotel at 10:30"),
]
# 'Japan' is legitimate in these phrases only
ALLOW = [r"Japanese"]

# ---------------------------------------------------------------------------
# 2. Line rules: any line matching TRIGGER that contains a clock time must
#    contain REQUIRED. (trigger, required, why)
# ---------------------------------------------------------------------------
TIME = re.compile(r"\b\d{1,2}:\d{2}\b")
LINE_RULES = [
    (r"CA959",                       r"13:45|18:05", "CA959 departs PEK 13:45, lands 18:05"),
    (r"CA959.*14:00|14:00.*CA959",   r"$^",     "CA959 no longer departs 14:00 — it is 13:45"),
    (r"\bLY85\b",                    r"00:05|15:45|21:05", "LY85 departs 00:05 Sun 11 Oct, lands 15:45"),
    (r"\bLY84\b",                    r"16:30|22:55", "LY84 departs 16:30, lands 22:55"),
    (r"TG628",                       r"10:30|14:20", "TG628 departs 10:30, lands 14:20"),
    (r"[Hh]ot stone|Let's Relax",    r"16:30",  "Hot stone massage is 16:30"),
    (r"Tai Pan",                     r"17:00",  "Tai Pan massage is 17:00"),
    (r"Nu Nail",                     r"12:00",  "Manicure is 12:00"),
    (r"Big Bus",                     r"19:00",  "Big Bus is 19:00"),
    (r"Tsz Shan|[Mm]onastery",       r"10:30|09:30|17:00|75", "Monastery booked 10:30"),
    (r"Tai Po Market",               r"09:15|11:45|12:15|13:00|\b~?1[0-9]:", "Leave for the monastery 09:15 to make 10:30"),
    (r"(?<![Ss]econd )[Ww]elcome meeting", r"18:00", "First welcome meeting Mon 19 Oct 18:00"),
    (r"[Ss]econd welcome meeting",   r"16:00",  "Shanghai welcome meeting Wed 28 Oct 16:00"),
    (r"[Ss]huttle.*(Canalis|airport)|Canalis.*[Ss]huttle", r"07:00|05:00", "Canalis shuttle 07:00"),
]

# Any mention of the customs mini-program must say NOT to use it
SAFETY_RULES = [
    (r"mini-?program|海关旅客指尖服务", r"[Nn]ever|NOT|not|❌|🚨",
     "DANGER: the Alipay mini-program got the account restricted — must say never use it"),
    (r"customs declaration", r"chinaport|website|Medication|declaration on|customs declaration ·|QR",
     "Customs declaration must point to customsapp.chinaport.gov.cn"),
]

# ---------------------------------------------------------------------------
# 3. Reference numbers: if a value of this shape appears, it must be one of
#    these exact values.
# ---------------------------------------------------------------------------
REFS = [
    (r"\b\d{4}\.\d{3}\.\d{3}\b",  {"6637.638.401", "6761.193.363"},  "Booking.com refs: Canalis 6637.638.401, Sindhorn 6761.193.363"),
    (r"PIN\s*(\d{4})",            {"4470", "6989"},                  "PINs: Canalis 4470, Sindhorn 6989"),
    (r"#(\d{7})",                 {"6886724"},                       "Intrepid booking #6886724"),
    (r"\+86 1720\d+",             {"+86 17200311621"},               "Intrepid emergency +86 17200311621"),
    (r"BLR\d+",                   {"BLR2611050011"},                 "Massage booking BLR2611050011"),
    (r"XF7\w+",                   {"XF7MVK0Z"},                      "Big Bus ref XF7MVK0Z"),
    (r"\b9998\d+|\b99987\d+",     {"99987084"},                      "Airalo order 99987084"),
    (r"\b5515\d+",                {"5515516445"},                    "Luxe Manor 5515516445"),
]

# ---------------------------------------------------------------------------
# 4. Facts that must be stated somewhere (file, regex, what)
# ---------------------------------------------------------------------------
MUST_EXIST = [
    ("full-trip-plan.md",    r"CA959.*13:45",              "CA959 13:45 in the flight table"),
    ("full-trip-plan.md",    r"6886724",                   "Intrepid booking number"),
    ("full-trip-plan.md",    r"17200311621",               "Intrepid emergency number"),
    ("full-trip-plan.md",    r"Pullman.*11–15 Oct",        "Pullman Bangkok Hotel G, 11–15 Oct"),
    ("full-trip-plan.md",    r"21:05",                     "At Ben Gurion by 21:05 on Sat 10 Oct"),
    ("full-trip-plan.md",    r"LY85.*00:05",               "LY85 00:05 in the flight table"),
    ("bangkok-itinerary.md", r"07:00",                     "Canalis 07:00 shuttle"),
    ("bangkok-itinerary.md", r"12:15",                     "Leave Sindhorn 12:15 on 8 Nov"),
    ("bangkok-itinerary.md", r"BLR2611050011",             "Massage booking ref"),
    ("hong-kong-itinerary.md", r"XF7MVK0Z",                "Big Bus ref"),
    ("packing-list.md",      r"chinaport",                 "Customs declaration website"),
    ("packing-list.md",      r"[Kk]nickers ×20",           "20 knickers"),
    ("packing-list.md",      r"Bras ×4",                   "4 bras"),
    ("packing-list.md",      r"Shein.*striped",            "Shein brown & white striped shirt is packed for China"),
    ("full-trip-plan.md",    r"Israeli.*Ben Gurion|Ben Gurion.*Israeli", "Israeli passport at Ben Gurion"),
    ("bangkok-itinerary.md", r"UK passport",               "UK passport at both Thai entries"),
]


DAYS = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
MONTHS = {"Oct": 10, "Nov": 11}
WEEKDAY_DATE = re.compile(r"\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*\.?,? (\d{1,2})(?:st|nd|rd|th)? (Oct|Nov)")


def check_weekdays(name, n, line, problems):
    import datetime
    for m in WEEKDAY_DATE.finditer(line):
        d = datetime.date(2026, MONTHS[m.group(3)], int(m.group(2)))
        if DAYS[d.weekday()] != m.group(1):
            problems.append((f"{name}:{n}", f"{m.group(2)} {m.group(3)} 2026 is a {DAYS[d.weekday()]}, not {m.group(1)}", line))


def main():
    problems = []
    texts = {f.name: f.read_text(encoding="utf-8") for f in FILES}
    if FAMILY.exists():
        texts["family/" + FAMILY.name] = FAMILY.read_text(encoding="utf-8")
        for n, line in enumerate(texts["family/" + FAMILY.name].splitlines(), 1):
            for rx, why in PRIVATE:
                if re.search(rx, line):
                    problems.append((f"family/{FAMILY.name}:{n}", "PRIVATE: " + why, line))
    else:
        problems.append(("family/", "MISSING: family page", ""))
    for name, text in texts.items():
        for n, line in enumerate(text.splitlines(), 1):
            where = f"{name}:{n}"
            check_weekdays(name, n, line, problems)
            clean = line
            for a in ALLOW:
                clean = re.sub(a, "", clean)
            for rx, why in FORBIDDEN:
                if re.search(rx, clean):
                    problems.append((where, why, line))
            if TIME.search(line):
                for trig, req, why in LINE_RULES:
                    if re.search(trig, line) and not re.search(req, line):
                        problems.append((where, why, line))
            for trig, req, why in SAFETY_RULES:
                if re.search(trig, line) and not re.search(req, line):
                    problems.append((where, why, line))
            for rx, allowed, why in REFS:
                for m in re.finditer(rx, line):
                    val = m.group(1) if m.groups() else m.group(0)
                    if val not in allowed:
                        problems.append((where, why + f" — found {val}", line))
    for fname, rx, what in MUST_EXIST:
        if not re.search(rx, texts.get(fname, "")):
            problems.append((fname, f"MISSING: {what}", ""))

    # The site must list every trip file, and the offline cache must match
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    sw = (ROOT / "sw.js").read_text(encoding="utf-8")
    for f in FILES:
        if f"'{f.name}'" not in index:
            problems.append(("index.html", f"{f.name} has no tab", ""))
        if f"travel/china-2026/{f.name}" not in sw:
            problems.append(("sw.js", f"{f.name} not cached for offline", ""))

    if problems:
        print(f"✗ {len(problems)} problem(s):\n")
        for where, why, line in problems:
            print(f"  {where}\n    {why}\n    > {line.strip()[:140]}\n")
        sys.exit(1)
    print(f"✓ All {len(FILES)} trip files consistent with the confirmed facts.")


if __name__ == "__main__":
    main()
