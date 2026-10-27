"""Build a narrated slideshow demo video (offline): PIL slides + espeak-ng voice + ffmpeg.

Usage: python3 scripts/make_demo_video.py  -> data/demo/chargeback_counsel_demo.mp4
Requires ffmpeg and espeak-ng on PATH. Slide text comes from the real showcase outputs.
"""
import pathlib, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "demo"
W, H = 1280, 720
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def section(md: str, title: str) -> list[str]:
    m = re.search(rf"## {re.escape(title)}\n(.*?)(?=\n## |\Z)", md, re.S)
    return [l for l in (m.group(1).strip().splitlines() if m else [])]


def table(lines, cols):
    rows = [[c.strip() for c in l.strip("|").split("|")] for l in lines if l.startswith("|") and "---" not in l]
    return ["  ".join(r[i][:22].ljust(w) for i, w in cols) for r in rows]


def slide(path, title, body, mono=True):
    img = Image.new("RGB", (W, H), (14, 20, 34))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 8], fill=(98, 66, 255))
    d.text((48, 36), title, font=ImageFont.truetype(SANS, 40), fill=(255, 255, 255))
    f = ImageFont.truetype(MONO if mono else SANS, 18 if mono else 28)
    y = 120
    for line in body:
        d.text((48, y), line, font=f, fill=(255, 120, 120) if "urgent" in line else (210, 220, 235))
        y += 26 if mono else 44
    d.text((48, H - 40), "Chargeback Counsel  |  Airwallex hackathon demo  |  synthetic data", font=ImageFont.truetype(MONO, 16), fill=(120, 130, 150))
    img.save(path)


def main():
    subprocess.run(["bash", "scripts/showcase.sh"], cwd=ROOT, check=True, capture_output=True, env={"TODAY": "2026-11-08", "PATH": "/usr/bin:/bin:/usr/local/bin"})
    md = (ROOT / "data" / "brief_late.md").read_text()
    OUT.mkdir(parents=True, exist_ok=True)
    triage = table(section(md, "Triage queue"), [(0, 8), (1, 22), (2, 11), (4, 6), (5, 7), (6, 7)])
    dl = table(section(md, "Evidence deadlines"), [(0, 8), (1, 10), (2, 8), (3, 11)])
    rec = table(section(md, "Expected recovery by currency"), [(0, 8), (1, 9), (3, 10), (5, 22)])
    gaps = table(section(md, "Evidence that would most help"), [(0, 8), (2, 8), (3, 22), (4, 6), (5, 22)])
    draft = [l for l in section(md, "Draft rebuttals (top by due date)")[:7] if l.strip()]
    slides = [
        ("Chargeback Counsel", ["An AI dispute agent for Airwallex merchants.", "It triages chargebacks, watches evidence deadlines,", "and drafts rebuttals. A human approves every submission."], False,
         "Chargeback Counsel is an A I dispute agent for Airwallex merchants. It triages chargebacks, watches evidence deadlines, and drafts rebuttals, and a human approves every submission."),
        ("The problem", ["Small merchants lose disputes they could win.", "Evidence deadlines slip and rebuttals are slow.", "Every lost dispute costs the amount plus a fee."], False,
         "Small merchants lose disputes they could win. Evidence deadlines slip, rebuttals are slow, and every lost dispute costs the amount plus a fee."),
        ("Triage: contest or accept", triage, True,
         "Signed dispute webhooks feed a triage queue. Each dispute gets a win probability from reason code playbooks and an expected value, so the agent recommends contesting five and accepting five."),
        ("Deadlines first", dl, True,
         "The brief leads with evidence deadlines, because a missed deadline is an automatic loss. Here one fraud dispute is urgent, with two days left."),
        ("Evidence gaps", gaps, True,
         "For each dispute the agent names the single piece of missing evidence that would raise the win chance most, and flags when it would flip an accept into a contest."),
        ("Draft rebuttal (approval gated)", draft, True,
         "Rebuttals are drafted per reason code, and every draft stays in draft status until the merchant approves it. Nothing is submitted automatically."),
        ("Expected recovery by currency", rec + ["", "34 tests pass. Next: live Airwallex sandbox client."], True,
         "Finally, the brief shows expected net recovery per currency across U S D, G B P, A U D and S G D. Thirty four tests pass, and the next step is the live Airwallex sandbox client."),
    ]
    parts = []
    for i, (t, body, mono, say) in enumerate(slides):
        png, wav, mp4 = OUT / f"s{i}.png", OUT / f"s{i}.wav", OUT / f"s{i}.mp4"
        slide(png, t, body, mono)
        subprocess.run(["espeak-ng", "-v", "en-us", "-s", "155", "-w", str(wav), say], check=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(png), "-i", str(wav), "-af", "apad=pad_dur=0.8",
                        "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p", "-r", "24", "-c:a", "aac", "-shortest", str(mp4)], check=True)
        parts.append(mp4)
    lst = OUT / "parts.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in parts))
    final = OUT / "chargeback_counsel_demo.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(final)], check=True)
    for p in list(OUT.glob("s*.wav")) + parts + [lst]:
        p.unlink()
    print(f"wrote {final.relative_to(ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
