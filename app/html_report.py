from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
import webbrowser

from app.stats import StatsSnapshot, TIME_RANGE_LABELS
from app.utils import sanitize_filename


class HTMLReportBuilder:
    """Generate and open a local HTML stats report."""

    def __init__(self, exports_dir: Path) -> None:
        self.exports_dir = exports_dir

    def build_and_open(self, snapshot: StatsSnapshot, report_name: str = "spotify_stats") -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.exports_dir / f"{sanitize_filename(report_name)}_{timestamp}.html"
        path.write_text(self.render(snapshot), encoding="utf-8")
        webbrowser.open(path.resolve().as_uri())
        return path

    def render(self, snapshot: StatsSnapshot) -> str:
        profile = snapshot.profile
        avatar = profile.get("avatar_url") or "https://images.unsplash.com/photo-1511379938547-c1f69419868d?auto=format&fit=crop&w=900&q=80"
        profile_url = profile.get("profile_url") or "#"
        top_track = self._pick_primary_item(snapshot.top_tracks)
        top_artist = self._pick_primary_item(snapshot.top_artists)
        warnings_html = self._render_warning_block(snapshot.warnings)
        categories = self._build_categories(snapshot)
        benefits = self._build_benefits(snapshot)
        stories = self._build_story_cards(snapshot)

        profile_cta = (
            f"<a class='button button-primary' href='{escape(profile_url)}' target='_blank' rel='noreferrer'>Abrir perfil</a>"
            if profile.get("profile_url")
            else "<a class='button button-primary' href='#featured'>Explorar informe</a>"
        )

        return f"""<!doctype html>
<html lang='es'>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>Spotify Portrait - {escape(profile['display_name'])}</title>
  <style>
    :root {{
      --bg: #121714;
      --bg-soft: #18201c;
      --surface: rgba(27, 36, 31, 0.86);
      --surface-strong: #1e2923;
      --ink: #e5ede6;
      --ink-soft: #b3c0b5;
      --ink-faint: #8fa092;
      --line: rgba(175, 201, 176, 0.14);
      --line-strong: rgba(175, 201, 176, 0.24);
      --accent: #7e9c7d;
      --accent-strong: #b8c8b8;
      --gold: #bda273;
      --shadow: 0 24px 72px rgba(0, 0, 0, 0.34);
      --shadow-soft: 0 14px 34px rgba(0, 0, 0, 0.26);
      --content: min(1220px, calc(100% - 40px));
    }}

    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(189, 162, 115, 0.12), transparent 25%),
        radial-gradient(circle at 86% 12%, rgba(126, 156, 125, 0.14), transparent 18%),
        linear-gradient(180deg, #101512 0%, #151c18 36%, #1a241f 100%);
      font-family: "Avenir Next", "Segoe UI", Helvetica, Arial, sans-serif;
      overflow-x: hidden;
    }}

    body::before {{
      content: "";
      position: fixed;
      inset: 0;
      background-image:
        linear-gradient(rgba(81, 104, 83, 0.02) 1px, transparent 1px),
        linear-gradient(90deg, rgba(81, 104, 83, 0.02) 1px, transparent 1px);
      background-size: 70px 70px;
      pointer-events: none;
      opacity: 0.45;
    }}

    img {{ max-width: 100%; display: block; }}
    a {{ color: inherit; }}

    .shell {{ position: relative; z-index: 1; }}
    .container {{ width: var(--content); margin: 0 auto; }}

    .announcement {{ border-bottom: 1px solid rgba(175, 201, 176, 0.10); background: rgba(18, 26, 22, 0.82); backdrop-filter: blur(12px); }}
    .announcement-inner {{ width: var(--content); margin: 0 auto; min-height: 42px; display: flex; align-items: center; justify-content: space-between; gap: 12px; color: var(--ink-soft); font-size: 0.84rem; letter-spacing: 0.03em; }}
    .announcement strong {{ color: var(--accent-strong); }}

    .nav-wrap {{ position: sticky; top: 0; z-index: 10; padding-top: 16px; }}
    .navbar {{ width: var(--content); margin: 0 auto; border: 1px solid rgba(175, 201, 176, 0.13); border-radius: 999px; padding: 14px 20px; display: flex; align-items: center; justify-content: space-between; gap: 22px; background: rgba(24, 33, 28, 0.82); backdrop-filter: blur(16px); box-shadow: var(--shadow-soft); }}

    .brand {{ text-decoration: none; display: flex; align-items: center; gap: 12px; }}
    .brand-mark {{ width: 42px; height: 42px; border-radius: 14px; display: grid; place-items: center; background: linear-gradient(145deg, #2f4137 0%, #4f6752 100%); color: #f0eadf; font-size: 1.1rem; box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.14); }}
    .brand-copy {{ display: flex; flex-direction: column; gap: 2px; }}
    .brand-name {{ font-family: Georgia, "Times New Roman", serif; font-size: 1.02rem; letter-spacing: 0.08em; text-transform: uppercase; }}
    .brand-sub {{ color: var(--ink-faint); font-size: 0.75rem; letter-spacing: 0.1em; text-transform: uppercase; }}

    .nav-links {{ display: flex; align-items: center; justify-content: center; gap: 18px; flex: 1; }}
    .nav-links a {{ color: var(--ink-soft); text-decoration: none; font-size: 0.92rem; transition: color 0.24s ease, transform 0.24s ease; }}
    .nav-links a:hover {{ color: var(--accent-strong); transform: translateY(-1px); }}

    .nav-cta {{ display: flex; align-items: center; gap: 10px; }}
    .button {{ min-height: 46px; padding: 0 18px; border-radius: 999px; border: 1px solid transparent; display: inline-flex; align-items: center; justify-content: center; text-decoration: none; transition: transform 0.26s ease, box-shadow 0.26s ease, background 0.26s ease; }}
    .button:hover {{ transform: translateY(-2px); }}
    .button-primary {{ background: linear-gradient(135deg, #4f6752 0%, #718d72 100%); color: #f2ede4; box-shadow: 0 14px 26px rgba(0, 0, 0, 0.26); }}
    .button-secondary {{ background: rgba(32, 44, 37, 0.82); border-color: rgba(175, 201, 176, 0.16); color: var(--accent-strong); }}

    .hero {{ width: var(--content); margin: 32px auto 0; border: 1px solid rgba(175, 201, 176, 0.14); border-radius: 40px; padding: 30px; background: linear-gradient(140deg, rgba(26, 35, 30, 0.96) 0%, rgba(21, 29, 25, 0.96) 100%), radial-gradient(circle at top right, rgba(189, 162, 115, 0.14), transparent 28%); box-shadow: var(--shadow); position: relative; overflow: hidden; }}
    .hero::before {{ content: ""; position: absolute; width: 220px; height: 220px; border-radius: 999px; right: -70px; top: -60px; background: rgba(179, 144, 88, 0.14); }}
    .hero-grid {{ display: grid; grid-template-columns: 1.08fr 0.92fr; gap: 32px; position: relative; z-index: 1; }}
    .eyebrow {{ display: inline-flex; padding: 8px 14px; border-radius: 999px; background: rgba(81, 104, 83, 0.08); color: var(--accent-strong); font-size: 0.78rem; letter-spacing: 0.16em; text-transform: uppercase; }}
    .hero h1, .section-heading h2, .cta h2, .story-card h3, .feature-panel h3, .benefit h3, .category-card h3, .hero-card-title, .hero-stat-value, .footer-brand {{ font-family: Georgia, "Times New Roman", serif; font-weight: 600; letter-spacing: -0.03em; }}
    .hero h1 {{ margin: 20px 0 16px; font-size: clamp(3rem, 7vw, 6rem); line-height: 0.9; max-width: 10ch; }}
    .hero p {{ margin: 0; color: var(--ink-soft); line-height: 1.8; font-size: 1.05rem; max-width: 66ch; }}
    .hero-actions {{ display: flex; flex-wrap: wrap; gap: 12px; margin-top: 28px; }}
    .hero-meta {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 28px; }}
    .meta-pill {{ border-radius: 999px; padding: 11px 15px; background: rgba(38, 51, 43, 0.78); border: 1px solid rgba(175, 201, 176, 0.12); color: var(--ink-soft); font-size: 0.87rem; }}

    .hero-portrait {{ min-height: 520px; border-radius: 34px; overflow: hidden; position: relative; background: #d9cbb8; box-shadow: var(--shadow-soft); }}
    .hero-portrait img {{ width: 100%; height: 100%; object-fit: cover; }}
    .hero-card {{ position: absolute; left: 20px; right: 20px; bottom: 20px; border-radius: 24px; padding: 18px; background: rgba(23, 34, 29, 0.78); border: 1px solid rgba(175, 201, 176, 0.14); backdrop-filter: blur(16px); }}
    .hero-card-title {{ font-size: 1.72rem; margin: 0 0 6px; }}
    .hero-card-copy {{ margin: 0; color: var(--ink-soft); line-height: 1.7; }}

    .hero-stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 16px; }}
    .hero-stat {{ border-radius: 22px; padding: 16px; background: rgba(27, 38, 32, 0.90); border: 1px solid rgba(175, 201, 176, 0.12); box-shadow: var(--shadow-soft); }}
    .hero-stat-label {{ color: var(--ink-faint); font-size: 0.78rem; letter-spacing: 0.08em; text-transform: uppercase; }}
    .hero-stat-value {{ margin-top: 8px; font-size: clamp(1.6rem, 4vw, 2.6rem); }}

    section {{ padding-top: 100px; }}
    .section-heading {{ display: flex; align-items: end; justify-content: space-between; gap: 18px; margin-bottom: 28px; }}
    .section-kicker {{ color: var(--gold); letter-spacing: 0.16em; text-transform: uppercase; font-size: 0.78rem; }}
    .section-heading h2 {{ margin: 10px 0 0; font-size: clamp(2.2rem, 4vw, 3.5rem); line-height: 0.98; max-width: 11ch; }}
    .section-heading p {{ margin: 0; max-width: 58ch; color: var(--ink-soft); line-height: 1.8; }}

    .card-grid {{ display: grid; gap: 20px; }}
    .category-grid {{ grid-template-columns: repeat(4, minmax(0, 1fr)); }}
    .benefits-grid {{ grid-template-columns: repeat(4, minmax(0, 1fr)); }}
    .story-grid {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}

    .category-card, .benefit, .story-card, .feature-panel, .about-grid, .warning-card, .timeline-panel, .cta, .footer-grid {{ border: 1px solid rgba(175, 201, 176, 0.12); background: rgba(25, 35, 30, 0.84); box-shadow: var(--shadow-soft); }}
    .category-card {{ padding: 24px; border-radius: 28px; position: relative; overflow: hidden; transition: transform 0.30s ease, box-shadow 0.30s ease, border-color 0.30s ease; }}
    .category-card::after {{ content: ""; position: absolute; width: 126px; height: 126px; border-radius: 999px; right: -26px; bottom: -26px; background: rgba(81, 104, 83, 0.07); }}
    .category-card:hover, .benefit:hover, .story-card:hover, .feature-card:hover, .recent-entry:hover, .saved-entry:hover {{ transform: translateY(-6px); box-shadow: 0 24px 40px rgba(58, 46, 31, 0.11); border-color: rgba(44, 63, 52, 0.16); }}
    .category-index {{ color: var(--gold); letter-spacing: 0.14em; text-transform: uppercase; font-size: 0.84rem; }}
    .category-card h3 {{ margin: 16px 0 10px; font-size: 1.58rem; }}
    .category-card p {{ margin: 0; color: var(--ink-soft); line-height: 1.75; }}
    .category-stat {{ margin-top: 20px; color: var(--accent-strong); font-weight: 700; }}

    .benefit {{ border-radius: 28px; padding: 24px; transition: transform 0.30s ease, box-shadow 0.30s ease; }}
    .benefit-icon {{ width: 50px; height: 50px; border-radius: 16px; display: grid; place-items: center; background: linear-gradient(135deg, rgba(81, 104, 83, 0.16), rgba(179, 144, 88, 0.21)); color: var(--accent-strong); font-size: 1.28rem; }}
    .benefit h3 {{ margin: 16px 0 10px; font-size: 1.3rem; }}
    .benefit p {{ margin: 0; color: var(--ink-soft); line-height: 1.75; }}

    .about-grid {{ border-radius: 34px; padding: 28px; display: grid; grid-template-columns: 1.06fr 0.94fr; gap: 20px; position: relative; overflow: hidden; }}
    .about-grid::before {{ content: ""; position: absolute; width: 280px; height: 280px; border-radius: 999px; right: -120px; top: -120px; background: rgba(179, 144, 88, 0.10); }}
    .about-copy, .about-visual {{ position: relative; z-index: 1; }}
    .about-copy p {{ margin: 0 0 18px; color: var(--ink-soft); line-height: 1.9; }}
    .about-metrics {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-top: 24px; }}
    .metric {{ border-radius: 20px; padding: 16px; background: rgba(35, 47, 40, 0.78); border: 1px solid rgba(175, 201, 176, 0.12); }}
    .metric strong {{ display: block; margin-bottom: 6px; font-family: Georgia, "Times New Roman", serif; font-size: 1.95rem; }}
    .metric span {{ color: var(--ink-faint); font-size: 0.88rem; }}

    .about-visual-card {{ min-height: 100%; border-radius: 28px; padding: 24px; display: flex; flex-direction: column; justify-content: space-between; gap: 20px; background: linear-gradient(180deg, rgba(43, 62, 49, 0.95) 0%, rgba(33, 47, 38, 0.98) 100%); color: #f5ecdf; box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08); }}
    .about-visual-card p {{ margin: 0; color: rgba(245, 236, 223, 0.76); line-height: 1.8; }}
    .mini-track {{ display: grid; gap: 12px; }}
    .mini-track-card {{ display: grid; grid-template-columns: 62px 1fr; gap: 12px; align-items: center; }}
    .mini-track-card img {{ width: 62px; height: 62px; border-radius: 18px; object-fit: cover; }}

    .feature-layout {{ display: grid; grid-template-columns: 1.07fr 0.93fr; gap: 20px; }}
    .feature-panel {{ border-radius: 34px; padding: 26px; }}
    .tabs {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 22px 0 18px; }}
    .tab-button {{ min-height: 44px; border-radius: 999px; border: 1px solid rgba(175, 201, 176, 0.12); background: rgba(37, 50, 42, 0.80); color: var(--ink-soft); padding: 0 16px; cursor: pointer; transition: all 0.25s ease; }}
    .tab-button.active, .tab-button:hover {{ background: var(--accent-strong); color: #f7f0e4; border-color: var(--accent-strong); }}
    .tab-panel {{ display: none; }}
    .tab-panel.active {{ display: block; animation: fadeIn 0.4s ease; }}

    .feature-list {{ display: grid; gap: 12px; }}
    .feature-card {{ border-radius: 24px; border: 1px solid rgba(175, 201, 176, 0.12); background: rgba(33, 45, 38, 0.82); padding: 14px; display: grid; grid-template-columns: 50px 70px 1fr auto; gap: 12px; align-items: center; transition: transform 0.28s ease, box-shadow 0.28s ease, border-color 0.28s ease; }}
    .rank-number {{ font-family: Georgia, "Times New Roman", serif; font-size: 1.65rem; color: var(--gold); text-align: center; }}
    .thumb {{ width: 70px; height: 70px; border-radius: 20px; object-fit: cover; background: #d8c7ae; }}
    .item-title {{ font-weight: 700; font-size: 1.06rem; }}
    .item-meta {{ margin-top: 4px; color: var(--ink-soft); line-height: 1.6; }}
    .item-note {{ margin-top: 4px; color: var(--ink-faint); font-size: 0.9rem; }}
    .text-link {{ color: var(--accent-strong); text-decoration: none; font-weight: 700; white-space: nowrap; }}
    .text-link:hover {{ text-decoration: underline; }}

    .spotlight {{ border-radius: 34px; padding: 26px; color: #f6eddf; background: linear-gradient(180deg, rgba(36, 53, 43, 0.97) 0%, rgba(44, 62, 50, 0.99) 100%); position: relative; overflow: hidden; }}
    .spotlight::after {{ content: ""; position: absolute; width: 210px; height: 210px; border-radius: 999px; right: -70px; bottom: -70px; background: rgba(179, 144, 88, 0.10); }}
    .spotlight > * {{ position: relative; z-index: 1; }}
    .spotlight-label {{ color: rgba(246, 237, 223, 0.70); letter-spacing: 0.12em; text-transform: uppercase; font-size: 0.78rem; }}
    .spotlight h3 {{ margin: 14px 0 8px; font-size: 1.95rem; }}
    .spotlight p {{ margin: 0; color: rgba(246, 237, 223, 0.76); line-height: 1.8; }}
    .spotlight-art {{ margin-top: 22px; border-radius: 26px; overflow: hidden; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.20); }}
    .spotlight-art img {{ width: 100%; aspect-ratio: 4 / 4.5; object-fit: cover; }}
    .spotlight-meta {{ display: grid; gap: 8px; margin-top: 14px; }}
    .spotlight-meta span {{ color: rgba(246, 237, 223, 0.82); }}

    .story-card {{ border-radius: 30px; padding: 24px; transition: transform 0.30s ease, box-shadow 0.30s ease; }}
    .story-tag {{ color: var(--gold); text-transform: uppercase; letter-spacing: 0.14em; font-size: 0.76rem; }}
    .story-card h3 {{ margin: 16px 0 10px; font-size: 1.45rem; }}
    .story-card p {{ margin: 0; color: var(--ink-soft); line-height: 1.8; }}
    .story-foot {{ margin-top: 16px; color: var(--accent-strong); font-weight: 700; }}

    .timeline-layout {{ display: grid; grid-template-columns: 1.07fr 0.93fr; gap: 20px; }}
    .timeline-panel {{ border-radius: 34px; padding: 26px; }}
    .timeline-list {{ display: grid; gap: 12px; }}

    .recent-entry, .saved-entry {{ border-radius: 24px; border: 1px solid rgba(175, 201, 176, 0.10); background: rgba(34, 46, 39, 0.82); display: grid; grid-template-columns: 70px 1fr; gap: 12px; align-items: center; padding: 14px; transition: transform 0.28s ease, box-shadow 0.28s ease, border-color 0.28s ease; }}
    .saved-icon {{ width: 70px; height: 70px; border-radius: 20px; display: grid; place-items: center; background: linear-gradient(135deg, rgba(81, 104, 83, 0.16), rgba(179, 144, 88, 0.18)); color: var(--accent-strong); font-size: 1.5rem; }}
    .entry-title {{ font-weight: 700; font-size: 1.02rem; }}
    .entry-sub {{ margin-top: 4px; color: var(--ink-soft); }}
    .entry-note {{ margin-top: 5px; color: var(--ink-faint); font-size: 0.9rem; line-height: 1.6; }}

    .genre-cloud {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 16px; }}
    .genre-chip {{ border-radius: 999px; padding: 9px 14px; background: rgba(81, 104, 83, 0.10); border: 1px solid rgba(44, 63, 52, 0.10); color: var(--accent-strong); font-size: 0.9rem; }}

    .warning-card {{ border-radius: 28px; padding: 20px 24px; background: rgba(179, 144, 88, 0.12); }}
    .warning-card ul {{ margin: 12px 0 0; padding-left: 18px; color: var(--ink-soft); line-height: 1.8; }}

    .cta {{ margin-top: 100px; border-radius: 36px; padding: 32px; display: grid; grid-template-columns: 1fr auto; gap: 20px; align-items: center; background: linear-gradient(135deg, rgba(28, 38, 32, 0.92) 0%, rgba(24, 33, 28, 0.94) 100%), radial-gradient(circle at top right, rgba(126, 156, 125, 0.12), transparent 24%); }}
    .cta h2 {{ margin: 0 0 10px; font-size: clamp(2rem, 4vw, 3.1rem); }}
    .cta p {{ margin: 0; color: var(--ink-soft); line-height: 1.8; max-width: 62ch; }}

    .footer {{ padding: 34px 0 50px; }}
    .footer-grid {{ width: var(--content); margin: 28px auto 0; border-radius: 30px; padding: 24px 28px; display: grid; grid-template-columns: 1.2fr 0.8fr 0.8fr; gap: 20px; }}
    .footer-brand {{ font-size: 1.55rem; margin-bottom: 10px; }}
    .footer p, .footer li, .footer a {{ color: var(--ink-soft); line-height: 1.8; text-decoration: none; }}
    .footer ul {{ list-style: none; margin: 0; padding: 0; }}
    .footer a:hover {{ color: var(--accent-strong); }}
    .footer-title {{ margin: 0 0 10px; color: var(--accent-strong); letter-spacing: 0.12em; text-transform: uppercase; font-size: 0.86rem; }}

    .empty {{ margin: 0; color: var(--ink-faint); line-height: 1.8; }}
    .reveal {{ opacity: 0; transform: translateY(32px); transition: opacity 0.8s ease, transform 0.8s ease; }}
    .reveal.is-visible {{ opacity: 1; transform: translateY(0); }}

    @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}

    @media (max-width: 1080px) {{
      .hero-grid, .feature-layout, .timeline-layout, .about-grid, .cta, .footer-grid {{ grid-template-columns: 1fr; }}
      .category-grid, .benefits-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .story-grid {{ grid-template-columns: 1fr; }}
      .section-heading {{ flex-direction: column; align-items: start; }}
    }}

    @media (max-width: 860px) {{
      .announcement-inner, .navbar {{ width: min(100% - 22px, 100%); }}
      .navbar {{ border-radius: 30px; padding: 16px; flex-wrap: wrap; justify-content: center; }}
      .nav-links {{ order: 3; width: 100%; flex-wrap: wrap; gap: 12px; }}
      .nav-cta {{ width: 100%; justify-content: center; }}
      .hero {{ width: min(100% - 22px, 100%); padding: 20px; border-radius: 30px; }}
      .hero-portrait {{ min-height: 420px; }}
      .hero-stats {{ grid-template-columns: 1fr; }}
      section {{ padding-top: 80px; }}
    }}

    @media (max-width: 640px) {{
      :root {{ --content: min(100% - 22px, 100%); }}
      .announcement-inner {{ min-height: auto; padding: 10px 0; flex-direction: column; align-items: start; }}
      .hero h1 {{ max-width: none; font-size: clamp(2.5rem, 14vw, 3.8rem); }}
      .section-heading h2 {{ max-width: none; }}
      .category-grid, .benefits-grid, .about-metrics {{ grid-template-columns: 1fr; }}
      .feature-card {{ grid-template-columns: 42px 58px 1fr; }}
      .feature-card .text-link {{ grid-column: 2 / span 2; }}
      .thumb, .recent-entry img, .saved-icon {{ width: 58px; height: 58px; border-radius: 18px; }}
      .recent-entry, .saved-entry {{ grid-template-columns: 58px 1fr; }}
      .hero-card, .feature-panel, .timeline-panel, .story-card, .benefit, .category-card, .cta, .about-grid {{ padding: 20px; }}
    }}
  </style>
</head>
<body>
  <div class='shell'>
    <div class='announcement'>
      <div class='announcement-inner'>
        <span><strong>Edicion premium del informe</strong> - Snapshot generado el {escape(snapshot.generated_at)}</span>
        <span>Spotify Web API + favoritos locales de esta CLI</span>
      </div>
    </div>

    <div class='nav-wrap'>
      <nav class='navbar'>
        <a class='brand' href='#top'>
          <span class='brand-mark'>S</span>
          <span class='brand-copy'>
            <span class='brand-name'>Spotify Portrait</span>
            <span class='brand-sub'>Music report</span>
          </span>
        </a>
        <div class='nav-links'>
          <a href='#categories'>Resumen general</a>
          <a href='#featured'>Top tracks y artists</a>
          <a href='#timeline'>Actividad reciente</a>
          <a href='#about'>Historia musical</a>
          <a href='#footer'>Metodologia</a>
        </div>
        <div class='nav-cta'>
          <a class='button button-secondary' href='#footer'>Metodologia</a>
          {profile_cta}
        </div>
      </nav>
    </div>

    <header class='hero reveal' id='top'>
      <div class='hero-grid'>
        <div class='hero-copy'>
          <span class='eyebrow'>Cuenta sonora curada</span>
          <h1>{escape(profile['display_name'])}</h1>
          <p>
            Una lectura editorial de tu identidad musical: tus obsesiones recientes, tus artistas mas recurrentes,
            las canciones que has decidido guardar y la huella que esta CLI ha ido construyendo contigo.
          </p>
          <div class='hero-actions'>
            <a class='button button-primary' href='#featured'>Ver destacados</a>
            <a class='button button-secondary' href='#timeline'>Explorar actividad</a>
          </div>
          <div class='hero-meta'>
            <span class='meta-pill'>@{escape(profile['user_id'])}</span>
            <span class='meta-pill'>Informe local y responsive</span>
            <span class='meta-pill'>Disenado para lectura rapida</span>
          </div>
        </div>

        <div>
          <div class='hero-portrait'>
            <img src='{escape(avatar)}' alt='Avatar de Spotify'>
            <div class='hero-card'>
              <div class='hero-card-title'>Tu perfil, en modo editorial</div>
              <p class='hero-card-copy'>Una portada limpia para entrar en tu panorama de escucha sin perder contexto ni detalle.</p>
            </div>
          </div>

          <div class='hero-stats'>
            <div class='hero-stat'>
              <div class='hero-stat-label'>Playlists accesibles</div>
              <div class='hero-stat-value'>{snapshot.summary['playlist_count']}</div>
            </div>
            <div class='hero-stat'>
              <div class='hero-stat-label'>Escuchas recientes</div>
              <div class='hero-stat-value'>{snapshot.summary['recent_count']}</div>
            </div>
            <div class='hero-stat'>
              <div class='hero-stat-label'>Favoritos locales</div>
              <div class='hero-stat-value'>{snapshot.summary['liked_local_count']}</div>
            </div>
          </div>
        </div>
      </div>
    </header>

    <main class='container'>
      {warnings_html}

      <section class='reveal' id='categories'>
        <div class='section-heading'>
          <div>
            <div class='section-kicker'>Resumen curado</div>
            <h2>Las capas que componen tu panorama musical.</h2>
          </div>
          <p>Inspirado en una landing premium, pero adaptado al contenido real del informe: cada bloque te presenta una faceta distinta de tu escucha.</p>
        </div>
        <div class='card-grid category-grid'>
          {self._render_categories(categories)}
        </div>
      </section>

      <section class='reveal' id='benefits'>
        <div class='section-heading'>
          <div>
            <div class='section-kicker'>Beneficios</div>
            <h2>Un informe pensado para verse tan bien como se entiende.</h2>
          </div>
          <p>No es solo un listado de datos: es una lectura visual con ritmo, contraste y una narrativa clara sobre tu cuenta.</p>
        </div>
        <div class='card-grid benefits-grid'>
          {self._render_benefits(benefits)}
        </div>
      </section>

      <section class='reveal' id='about'>
        <div class='section-heading'>
          <div>
            <div class='section-kicker'>About / Brand story</div>
            <h2>La historia de escucha que esta CLI puede contar hoy.</h2>
          </div>
          <p>La pagina conserva el comportamiento actual del proyecto, pero ahora lo viste con una identidad mas refinada, luminosa y editorial.</p>
        </div>

        <div class='about-grid'>
          <div class='about-copy'>
            <p>
              Este retrato mezcla lo que Spotify permite ver desde su Web API con la memoria local creada por la aplicacion.
              El resultado no intenta imitar un Wrapped oficial: busca ofrecer una lectura elegante, util y con mucho mas caracter visual.
            </p>
            <p>
              Tus tops marcan el gusto dominante, la actividad reciente aporta contexto del momento y los favoritos locales
              revelan las decisiones personales que has guardado en el camino.
            </p>
            <div class='about-metrics'>
              <div class='metric'>
                <strong>{snapshot.summary['top_track_count']}</strong>
                <span>Entradas top disponibles entre periodos</span>
              </div>
              <div class='metric'>
                <strong>{len(snapshot.top_artists.get('short_term', []))}</strong>
                <span>Artistas destacados en la vista mas reciente</span>
              </div>
              <div class='metric'>
                <strong>{len(snapshot.local_stats.get('top_genres', []))}</strong>
                <span>Generos locales detectados por la app</span>
              </div>
              <div class='metric'>
                <strong>{len(snapshot.recent_tracks)}</strong>
                <span>Momentos recientes listos para revisar</span>
              </div>
            </div>
          </div>

          <div class='about-visual'>
            <div class='about-visual-card'>
              <div>
                <div class='section-kicker' style='color: rgba(246, 237, 223, 0.62);'>Edicion destacada</div>
                <h3 style='margin: 12px 0 10px; font-size: 1.95rem;'>Una mezcla de API, memoria y criterio visual.</h3>
                <p>La pagina prioriza aire, tipografia y composicion. Menos dashboard tecnico, mas retrato musical con sensacion premium.</p>
              </div>
              <div class='mini-track'>
                {self._render_mini_highlights(top_track, top_artist)}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class='reveal' id='featured'>
        <div class='section-heading'>
          <div>
            <div class='section-kicker'>Destacados</div>
            <h2>Tus tops convertidos en una vitrina principal.</h2>
          </div>
          <p>Se mantienen los datos y periodos originales, pero con una presentacion mas inmersiva, con mejor jerarquia visual y hover mas elegante.</p>
        </div>

        <div class='feature-layout'>
          <article class='feature-panel'>
            <div class='section-kicker'>Top tracks</div>
            <h3 style='margin: 12px 0 0; font-size: 2rem;'>Canciones que definen el tono</h3>
            <div class='tabs'>
              <button class='tab-button active' data-target='tracks-short_term'>Ultimas 4 semanas</button>
              <button class='tab-button' data-target='tracks-medium_term'>Ultimos 6 meses</button>
              <button class='tab-button' data-target='tracks-long_term'>Ultimo ano</button>
            </div>
            {self._render_tabs(snapshot.top_tracks, 'track', 'tracks')}
          </article>

          <aside class='spotlight'>
            <div class='spotlight-label'>Track protagonista</div>
            <h3>{escape(top_track.get('name', 'Sin titulo'))}</h3>
            <p>{escape(top_track.get('artists', 'Sin artista'))}</p>
            <div class='spotlight-art'>
              <img src='{escape(top_track.get('image_url', avatar))}' alt='Track destacado'>
            </div>
            <div class='spotlight-meta'>
              <span>Album: {escape(top_track.get('album', 'No disponible'))}</span>
              <a class='text-link' href='{escape(top_track.get('spotify_url', '#'))}' target='_blank' rel='noreferrer'>Abrir en Spotify</a>
            </div>
          </aside>
        </div>

        <div class='feature-layout' style='margin-top: 20px;'>
          <aside class='spotlight'>
            <div class='spotlight-label'>Artista protagonista</div>
            <h3>{escape(top_artist.get('name', 'Artista desconocido'))}</h3>
            <p>{escape(top_artist.get('genres', 'Genero no disponible'))}</p>
            <div class='spotlight-art'>
              <img src='{escape(top_artist.get('image_url', avatar))}' alt='Artista destacado'>
            </div>
            <div class='spotlight-meta'>
              <span>Seleccionado desde tus tops del periodo mas reciente.</span>
              <a class='text-link' href='{escape(top_artist.get('spotify_url', '#'))}' target='_blank' rel='noreferrer'>Ver artista</a>
            </div>
          </aside>

          <article class='feature-panel'>
            <div class='section-kicker'>Top artists</div>
            <h3 style='margin: 12px 0 0; font-size: 2rem;'>Nombres que sostienen tu escucha</h3>
            <div class='tabs'>
              <button class='tab-button active' data-target='artists-short_term'>Ultimas 4 semanas</button>
              <button class='tab-button' data-target='artists-medium_term'>Ultimos 6 meses</button>
              <button class='tab-button' data-target='artists-long_term'>Ultimo ano</button>
            </div>
            {self._render_tabs(snapshot.top_artists, 'artist', 'artists')}
          </article>
        </div>
      </section>

      <section class='reveal' id='stories'>
        <div class='section-heading'>
          <div>
            <div class='section-kicker'>Customer stories reinterpretado</div>
            <h2>Historias recientes que dan vida al informe.</h2>
          </div>
          <p>En lugar de testimonios ficticios, esta pagina usa tu actividad y tus guardados locales para contar pequenas historias reales.</p>
        </div>
        <div class='card-grid story-grid'>
          {self._render_story_cards(stories)}
        </div>
      </section>

      <section class='reveal' id='timeline'>
        <div class='section-heading'>
          <div>
            <div class='section-kicker'>Actividad y favoritos</div>
            <h2>Tu movimiento reciente y la huella local de la app.</h2>
          </div>
          <p>Dos columnas complementarias: lo que ha sonado hace poco y lo que decidiste conservar desde esta herramienta.</p>
        </div>

        <div class='timeline-layout'>
          <article class='timeline-panel'>
            <div class='section-kicker'>Escuchado recientemente</div>
            <h3 style='margin: 12px 0 18px; font-size: 1.95rem; font-family: Georgia, "Times New Roman", serif;'>Momentos en reproduccion</h3>
            <div class='timeline-list'>
              {self._render_recent(snapshot.recent_tracks)}
            </div>
          </article>

          <article class='timeline-panel'>
            <div class='section-kicker'>Favoritos guardados</div>
            <h3 style='margin: 12px 0 18px; font-size: 1.95rem; font-family: Georgia, "Times New Roman", serif;'>Memoria local curada</h3>
            <div class='genre-cloud'>
              {self._render_genres(snapshot.local_stats['top_genres'])}
            </div>
            <div class='timeline-list'>
              {self._render_saved(snapshot.local_stats['recent_saved'])}
            </div>
          </article>
        </div>
      </section>

      <section class='cta reveal'>
        <div>
          <div class='section-kicker'>Cierre</div>
          <h2>Tu informe ya tiene mas identidad, mas aire y mejor presencia.</h2>
          <p>Vuelve a generar esta pagina cuando quieras refrescar tus datos. El contenido sigue saliendo de la opcion 4, pero con una experiencia visual mucho mas cuidada.</p>
        </div>
        <div class='hero-actions'>
          <a class='button button-primary' href='#top'>Volver arriba</a>
          <a class='button button-secondary' href='#featured'>Revisar destacados</a>
        </div>
      </section>
    </main>

    <footer class='footer' id='footer'>
      <div class='footer-grid'>
        <div>
          <div class='footer-brand'>Spotify Portrait</div>
          <p>Informe HTML generado localmente desde la opcion 4 de la CLI. Mantiene la logica original del proyecto y eleva su identidad visual hacia un lenguaje mas premium, limpio y natural.</p>
        </div>
        <div>
          <div class='footer-title'>Navegacion</div>
          <ul>
            <li><a href='#categories'>Resumen</a></li>
            <li><a href='#featured'>Destacados</a></li>
            <li><a href='#timeline'>Actividad</a></li>
            <li><a href='#top'>Inicio</a></li>
          </ul>
        </div>
        <div>
          <div class='footer-title'>Metodologia</div>
          <p>Spotify no expone minutos totales de escucha ni un Wrapped oficial desde su Web API. Este informe usa tops, actividad reciente y favoritos locales para ofrecer una lectura util y visualmente refinada.</p>
        </div>
      </div>
    </footer>
  </div>

  <script>
    document.querySelectorAll('.tab-button').forEach((button) => {{
      button.addEventListener('click', () => {{
        const group = button.dataset.target.split('-')[0];
        document.querySelectorAll(`.tab-button[data-target^="${{group}}-"]`).forEach((item) => item.classList.remove('active'));
        document.querySelectorAll(`.tab-panel[id^="${{group}}-"]`).forEach((item) => item.classList.remove('active'));
        button.classList.add('active');
        const panel = document.getElementById(button.dataset.target);
        if (panel) panel.classList.add('active');
      }});
    }});

    const revealNodes = document.querySelectorAll('.reveal');
    const revealObserver = new IntersectionObserver((entries) => {{
      entries.forEach((entry) => {{
        if (entry.isIntersecting) {{
          entry.target.classList.add('is-visible');
          revealObserver.unobserve(entry.target);
        }}
      }});
    }}, {{ threshold: 0.16 }});

    revealNodes.forEach((node) => revealObserver.observe(node));
  </script>
</body>
</html>"""

    @staticmethod
    def _pick_primary_item(items_by_range: dict[str, list[dict[str, str]]]) -> dict[str, str]:
        for key in TIME_RANGE_LABELS:
            items = items_by_range.get(key, [])
            if items:
                return items[0]
        return {
            "name": "Sin datos disponibles",
            "artists": "Spotify no devolvio resultados para esta seccion.",
            "genres": "Spotify no devolvio resultados para esta seccion.",
            "album": "No disponible",
            "image_url": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?auto=format&fit=crop&w=900&q=80",
            "spotify_url": "#",
        }

    @staticmethod
    def _build_categories(snapshot: StatsSnapshot) -> list[dict[str, str]]:
        return [
            {
                "index": "01",
                "title": "Top tracks",
                "copy": "Las canciones mas recurrentes en tus periodos principales, tratadas como una seleccion destacada.",
                "stat": f"{snapshot.summary['top_track_count']} entradas agregadas",
            },
            {
                "index": "02",
                "title": "Top artists",
                "copy": "Los nombres que mas peso tienen en tu escucha y que ayudan a definir el caracter del informe.",
                "stat": f"{len(snapshot.top_artists.get('short_term', []))} artistas en corto plazo",
            },
            {
                "index": "03",
                "title": "Actividad reciente",
                "copy": "Una cronologia estilizada para leer rapidamente lo que ha sonado hace poco en tu cuenta.",
                "stat": f"{snapshot.summary['recent_count']} reproducciones recientes",
            },
            {
                "index": "04",
                "title": "Favoritos locales",
                "copy": "La capa mas personal: canciones guardadas desde esta app y generos que se repiten en tu propio uso.",
                "stat": f"{snapshot.summary['liked_local_count']} guardados locales",
            },
        ]

    @staticmethod
    def _build_benefits(snapshot: StatsSnapshot) -> list[dict[str, str]]:
        return [
            {
                "icon": "~",
                "title": "Lectura por periodos",
                "copy": "Top tracks y top artists siguen separados por horizonte temporal para leer cambios de corto, medio y largo plazo.",
            },
            {
                "icon": "+",
                "title": "Datos locales y oficiales",
                "copy": "Combina la informacion disponible en Spotify con la memoria local creada por tus canciones guardadas en la CLI.",
            },
            {
                "icon": "*",
                "title": "Visual premium y ligero",
                "copy": "HTML standalone, sin librerias pesadas, con movimiento suave y una composicion mas intencional.",
            },
            {
                "icon": "->",
                "title": "Acciones directas",
                "copy": "Los elementos destacados mantienen accesos directos a Spotify cuando la API aporta enlaces utiles.",
            },
        ]

    @staticmethod
    def _build_story_cards(snapshot: StatsSnapshot) -> list[dict[str, str]]:
        top_track = snapshot.top_tracks.get("short_term", [])
        top_artist = snapshot.top_artists.get("short_term", [])
        recent = snapshot.recent_tracks[:1]
        local_saved = snapshot.local_stats.get("recent_saved", [])[:1]

        cards = [
            {
                "tag": "Track mood",
                "title": top_track[0]["name"] if top_track else "Sin track destacado",
                "copy": top_track[0].get("artists", "No hay informacion suficiente para este periodo.") if top_track else "Spotify no devolvio tops en corto plazo.",
                "foot": top_track[0].get("album", "Album no disponible") if top_track else "Sin album disponible",
            },
            {
                "tag": "Artist direction",
                "title": top_artist[0]["name"] if top_artist else "Sin artista destacado",
                "copy": top_artist[0].get("genres", "Genero no disponible") if top_artist else "Spotify no devolvio artistas en corto plazo.",
                "foot": "Top artist del periodo reciente",
            },
            {
                "tag": "Local memory",
                "title": local_saved[0].get("title", "Sin guardados locales") if local_saved else "Sin guardados locales",
                "copy": local_saved[0].get("artist", "Todavia no hay canciones guardadas en esta capa local.") if local_saved else "Todavia no hay canciones guardadas desde la app.",
                "foot": f"Genero: {local_saved[0].get('genre_queried', 'sin dato')}" if local_saved else "La seccion se activara cuando guardes canciones",
            },
        ]

        if recent:
            cards[2] = {
                "tag": "Recent moment",
                "title": recent[0].get("name", "Sin titulo"),
                "copy": recent[0].get("artists", "Sin artista"),
                "foot": f"Escuchada en: {recent[0].get('played_at', 'sin fecha')}",
            }

        return cards

    @staticmethod
    def _render_warning_block(warnings: list[str]) -> str:
        if not warnings:
            return ""
        items = "".join(f"<li>{escape(item)}</li>" for item in warnings)
        return (
            "<section class='reveal'>"
            "<div class='warning-card'>"
            "<div class='section-kicker'>Secciones parciales</div>"
            "<h3 style='margin: 12px 0 0; font-size: 1.8rem; font-family: Georgia, \"Times New Roman\", serif;'>Algunos bloques no pudieron cargarse del todo.</h3>"
            f"<ul>{items}</ul>"
            "</div>"
            "</section>"
        )

    @staticmethod
    def _render_categories(items: list[dict[str, str]]) -> str:
        return "".join(
            "<article class='category-card'>"
            f"<div class='category-index'>{escape(item['index'])}</div>"
            f"<h3>{escape(item['title'])}</h3>"
            f"<p>{escape(item['copy'])}</p>"
            f"<div class='category-stat'>{escape(item['stat'])}</div>"
            "</article>"
            for item in items
        )

    @staticmethod
    def _render_benefits(items: list[dict[str, str]]) -> str:
        return "".join(
            "<article class='benefit'>"
            f"<div class='benefit-icon'>{escape(item['icon'])}</div>"
            f"<h3>{escape(item['title'])}</h3>"
            f"<p>{escape(item['copy'])}</p>"
            "</article>"
            for item in items
        )

    @staticmethod
    def _render_story_cards(items: list[dict[str, str]]) -> str:
        return "".join(
            "<article class='story-card'>"
            f"<div class='story-tag'>{escape(item['tag'])}</div>"
            f"<h3>{escape(item['title'])}</h3>"
            f"<p>{escape(item['copy'])}</p>"
            f"<div class='story-foot'>{escape(item['foot'])}</div>"
            "</article>"
            for item in items
        )

    def _render_mini_highlights(self, track: dict[str, str], artist: dict[str, str]) -> str:
        return "".join(
            [
                self._render_mini_highlight_card(
                    image_url=track.get("image_url", ""),
                    title=track.get("name", "Sin track"),
                    subtitle=track.get("artists", "Sin artista"),
                ),
                self._render_mini_highlight_card(
                    image_url=artist.get("image_url", ""),
                    title=artist.get("name", "Sin artista"),
                    subtitle=artist.get("genres", "Genero no disponible"),
                ),
            ]
        )

    @staticmethod
    def _render_mini_highlight_card(image_url: str, title: str, subtitle: str) -> str:
        resolved_image = image_url or "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=240&q=80"
        return (
            "<div class='mini-track-card'>"
            f"<img src='{escape(resolved_image)}' alt='Highlight'>"
            f"<div><div style='font-weight: 700;'>{escape(title)}</div><div style='color: rgba(245, 236, 223, 0.66); margin-top: 4px;'>{escape(subtitle)}</div></div>"
            "</div>"
        )

    def _render_tabs(self, items_by_range: dict[str, list[dict[str, str]]], kind: str, prefix: str) -> str:
        parts: list[str] = []
        for key in TIME_RANGE_LABELS:
            active = " active" if key == "short_term" else ""
            items = items_by_range.get(key, [])
            cards = "".join(self._render_rank_card(item, kind) for item in items)
            if not cards:
                cards = "<p class='empty'>Sin datos disponibles para este periodo.</p>"
            parts.append(
                f"<div class='tab-panel{active}' id='{prefix}-{key}'>"
                f"<p class='empty' style='margin-bottom: 16px;'>{escape(TIME_RANGE_LABELS[key])}</p>"
                f"<div class='feature-list'>{cards}</div>"
                "</div>"
            )
        return "".join(parts)

    @staticmethod
    def _render_rank_card(item: dict[str, str], kind: str) -> str:
        subtitle = item.get("artists", "") if kind == "track" else item.get("genres", "")
        detail = item.get("album", "") if kind == "track" else "Top artist"
        image_url = item.get("image_url") or "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=240&q=80"
        link = item.get("spotify_url") or "#"
        return (
            "<article class='feature-card'>"
            f"<div class='rank-number'>{escape(str(item.get('rank', '')))}</div>"
            f"<img class='thumb' src='{escape(image_url)}' alt='Portada'>"
            "<div>"
            f"<div class='item-title'>{escape(item.get('name', ''))}</div>"
            f"<div class='item-meta'>{escape(subtitle)}</div>"
            f"<div class='item-note'>{escape(detail)}</div>"
            "</div>"
            f"<a class='text-link' href='{escape(link)}' target='_blank' rel='noreferrer'>Abrir</a>"
            "</article>"
        )

    @staticmethod
    def _render_recent(items: list[dict[str, str]]) -> str:
        if not items:
            return "<p class='empty'>Sin actividad reciente disponible.</p>"

        parts: list[str] = []
        for item in items:
            image_url = item.get("image_url") or "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?auto=format&fit=crop&w=240&q=80"
            context = item.get("context_type") or "contexto desconocido"
            spotify_url = item.get("spotify_url") or "#"
            parts.append(
                "<article class='recent-entry'>"
                f"<img class='thumb' src='{escape(image_url)}' alt='Portada reciente'>"
                "<div>"
                f"<div class='entry-title'>{escape(item.get('name', ''))}</div>"
                f"<div class='entry-sub'>{escape(item.get('artists', ''))}</div>"
                f"<div class='entry-note'>Reproducida: {escape(item.get('played_at', ''))} - {escape(context)}</div>"
                f"<div class='entry-note'><a class='text-link' href='{escape(spotify_url)}' target='_blank' rel='noreferrer'>Abrir en Spotify</a></div>"
                "</div>"
                "</article>"
            )
        return "".join(parts)

    @staticmethod
    def _render_saved(items: list[dict[str, str]]) -> str:
        if not items:
            return "<p class='empty'>No hay canciones guardadas localmente todavia.</p>"

        parts: list[str] = []
        for item in items:
            parts.append(
                "<article class='saved-entry'>"
                "<div class='saved-icon'>♪</div>"
                "<div>"
                f"<div class='entry-title'>{escape(item.get('title', ''))}</div>"
                f"<div class='entry-sub'>{escape(item.get('artist', ''))}</div>"
                f"<div class='entry-note'>Genero consultado: {escape(item.get('genre_queried', 'sin dato'))}</div>"
                "</div>"
                "</article>"
            )
        return "".join(parts)

    @staticmethod
    def _render_genres(genres: list[tuple[str, int]]) -> str:
        if not genres:
            return "<p class='empty'>Todavia no hay generos locales suficientes.</p>"
        return "".join(
            f"<span class='genre-chip'>{escape(name)} <strong>{count}</strong></span>"
            for name, count in genres
        )
