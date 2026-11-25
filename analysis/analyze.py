"""Statistical analysis for LocalHelp AI.

Run from the project folder:
    python analysis/analyze.py                       (reads localhelp.db)
    python analysis/analyze.py --db path/to/localhelp.db
    python analysis/analyze.py --survey-csv my_form.csv   (survey collected in Google Forms)

What it does
  Stage 2 (Define)  descriptive statistics, charts, correlations, confidence intervals,
                    baseline hypothesis test, ranking of pain points
  Stage 5 (Test)    current method vs prototype: paired test on time, success rates,
                    effect size, SUS score

Output: analysis/output/report.txt and PNG charts. All numbers come from YOUR data.
The script never invents or fills in data. If there is not enough data it says so.

Hypotheses (write your own versions in the Ideate stage BEFORE testing):
  Baseline  H0: mean satisfaction with the current process = 3 (neutral)
            H1: mean satisfaction is below 3
  Time      H0: mean task time with the prototype = mean time with the current method
            H1: mean task time with the prototype is lower   (use --two-sided for "different")
"""
import argparse
import math
import os
import sqlite3
import sys

import numpy as np
import pandas as pd
from scipy import stats

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from survey_config import QUESTIONS  # noqa: E402

LIKERT = [q["id"] for q in QUESTIONS if q["type"] == "likert"]
NUMERIC = [q["id"] for q in QUESTIONS if q["type"] == "number"]
CATEGORICAL = [q["id"] for q in QUESTIONS if q["type"] == "single"]

lines = []


def say(text=""):
    print(text)
    lines.append(text)


def head(title):
    say()
    say("=" * 70)
    say(title)
    say("=" * 70)


def p_text(p):
    return "p < 0.001" if p < 0.001 else f"p = {p:.3f}"


def mean_ci(x, alpha):
    x = np.asarray(x, dtype=float)
    n = len(x)
    m = x.mean()
    if n < 2:
        return m, float("nan"), float("nan")
    half = stats.t.ppf(1 - alpha / 2, n - 1) * x.std(ddof=1) / math.sqrt(n)
    return m, m - half, m + half


def wilson(k, n, alpha):
    """Wilson confidence interval for a proportion k/n."""
    if n == 0:
        return float("nan"), float("nan")
    z = stats.norm.ppf(1 - alpha / 2)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return centre - half, centre + half


def interpret_r(r):
    a = abs(r)
    strength = "very weak" if a < .2 else "weak" if a < .4 else "moderate" if a < .6 else "strong" if a < .8 else "very strong"
    return f"{strength} {'positive' if r > 0 else 'negative'}"


# ---------- loading ----------
def load_survey(db_path, csv_path):
    if csv_path:
        df = pd.read_csv(csv_path)
        df.columns = [c.strip() for c in df.columns]
    else:
        import json
        con = sqlite3.connect(db_path)
        rows = con.execute("SELECT answers FROM survey_responses").fetchall()
        con.close()
        df = pd.DataFrame([json.loads(r[0]) for r in rows])
    for c in LIKERT + NUMERIC:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def load_table(db_path, table):
    con = sqlite3.connect(db_path)
    try:
        return pd.read_sql_query(f"SELECT * FROM {table}", con)
    finally:
        con.close()


# ---------- Stage 2: survey ----------
def survey_analysis(df, out, alpha):
    n = len(df)
    head(f"STAGE 2 - SURVEY ANALYSIS (n = {n})")
    if n < 30:
        say(f"Note: the brief asks for at least 30 responses. You have {n}. Results below are preliminary.")
    if n < 3:
        say("Not enough responses to analyse. Collect more data first.")
        return

    say()
    say("Sampling note: describe how respondents were chosen (random / stratified / convenience) and the limits of your sample in the report.")

    head("Descriptive statistics")
    cols = [c for c in NUMERIC + LIKERT if c in df.columns]
    rows = []
    for c in cols:
        x = df[c].dropna()
        if len(x) == 0:
            continue
        m, lo, hi = mean_ci(x, alpha)
        mode = x.mode()
        rows.append({
            "variable": c, "n": len(x), "mean": round(m, 2), "median": round(x.median(), 2),
            "mode": round(float(mode.iloc[0]), 2), "sd": round(x.std(ddof=1), 2) if len(x) > 1 else float("nan"),
            "min": x.min(), "max": x.max(), f"CI{int((1 - alpha) * 100)}_low": round(lo, 2), f"CI{int((1 - alpha) * 100)}_high": round(hi, 2),
        })
    say(pd.DataFrame(rows).to_string(index=False))

    head("Frequency tables (multiple-choice questions)")
    for c in CATEGORICAL:
        if c in df.columns:
            vc = df[c].value_counts()
            say(f"\n{c}")
            for k, v in vc.items():
                say(f"  {k}: {v} ({v / df[c].notna().sum() * 100:.0f}%)")

    # charts
    if "minutes_to_find" in df.columns and df["minutes_to_find"].notna().any():
        plt.figure(figsize=(6, 4))
        plt.hist(df["minutes_to_find"].dropna(), bins=8, color="#1f5fe6", edgecolor="white")
        plt.xlabel("Minutes to find a provider (last time)")
        plt.ylabel("Number of respondents")
        plt.title("Time taken to find a provider")
        plt.tight_layout(); plt.savefig(os.path.join(out, "hist_minutes_to_find.png"), dpi=150); plt.close()
    if "how_found" in df.columns and df["how_found"].notna().any():
        vc = df["how_found"].value_counts()
        plt.figure(figsize=(7, 4))
        plt.barh(vc.index[::-1], vc.values[::-1], color="#1f5fe6")
        plt.xlabel("Number of respondents"); plt.title("How providers are found today")
        plt.tight_layout(); plt.savefig(os.path.join(out, "bar_how_found.png"), dpi=150); plt.close()
    lk = [c for c in LIKERT if c in df.columns and df[c].notna().any()]
    if lk:
        plt.figure(figsize=(8, 4.5))
        plt.boxplot([df[c].dropna() for c in lk])
        plt.xticks(range(1, len(lk) + 1), lk, rotation=20)
        plt.ylabel("Score (1 to 5)"); plt.title("Likert items")
        plt.tight_layout()
        plt.savefig(os.path.join(out, "box_likert.png"), dpi=150); plt.close()

    head("Correlations (Pearson and Spearman)")
    pairs = [("minutes_to_find", "frustration"), ("calls_made", "frustration"),
             ("minutes_to_find", "satisfaction"), ("trust", "satisfaction")]
    for a, b in pairs:
        if a in df.columns and b in df.columns:
            sub = df[[a, b]].dropna()
            if len(sub) >= 3 and sub[a].nunique() > 1 and sub[b].nunique() > 1:
                r, p = stats.pearsonr(sub[a], sub[b])
                rho, ps = stats.spearmanr(sub[a], sub[b])
                say(f"{a} vs {b} (n={len(sub)}): Pearson r = {r:.2f} ({interpret_r(r)}, {p_text(p)}); "
                    f"Spearman rho = {rho:.2f} ({p_text(ps)})")
            else:
                say(f"{a} vs {b}: not enough varied data.")
    say("Reminder: correlation does not prove that one thing causes the other.")

    if {"minutes_to_find", "satisfaction"} <= set(df.columns):
        sub = df[["minutes_to_find", "satisfaction"]].dropna()
        if len(sub) >= 3 and sub["minutes_to_find"].nunique() > 1:
            res = stats.linregress(sub["minutes_to_find"], sub["satisfaction"])
            say(f"\nSimple regression: satisfaction = {res.intercept:.2f} + {res.slope:.4f} x minutes_to_find; "
                f"R-squared = {res.rvalue ** 2:.2f}, {p_text(res.pvalue)}")

    head("Baseline hypothesis test (current process)")
    say("H0: mean satisfaction = 3 (neutral)    H1: mean satisfaction < 3")
    if "satisfaction" in df.columns:
        x = df["satisfaction"].dropna()
        if len(x) >= 3 and x.nunique() > 1:
            t, p = stats.ttest_1samp(x, 3, alternative="less")
            say(f"One-sample t-test: mean = {x.mean():.2f}, t({len(x) - 1}) = {t:.2f}, {p_text(p)} -> "
                f"{'reject H0' if p < alpha else 'fail to reject H0'} at alpha = {alpha}")
            try:
                w, pw = stats.wilcoxon(x - 3, alternative="less")
                say(f"Wilcoxon signed-rank (if Likert data are not normal): {p_text(pw)}")
            except ValueError:
                say("Wilcoxon test not possible (all values equal to 3).")
            m, lo, hi = mean_ci(x, alpha)
            say(f"{int((1 - alpha) * 100)}% CI for mean satisfaction: [{lo:.2f}, {hi:.2f}]")
        else:
            say("Not enough varied satisfaction data.")

    head("Pain points ranked by how many users are affected")
    items = []
    def add(label, mask):
        valid = mask.dropna()
        if len(valid):
            k = int(valid.sum()); lo, hi = wilson(k, len(valid), alpha)
            items.append((label, k, len(valid), k / len(valid) * 100, lo * 100, hi * 100))
    if "frustration" in df.columns: add("Finds the search frustrating (4 or 5)", df["frustration"].dropna().ge(4))
    if "satisfaction" in df.columns: add("Not satisfied (1 or 2)", df["satisfaction"].dropna().le(2))
    if "trust" in df.columns: add("Low trust in providers (1 or 2)", df["trust"].dropna().le(2))
    if "price_fair" in df.columns: add("Not sure of a fair price (1 or 2)", df["price_fair"].dropna().le(2))
    if "overcharged" in df.columns: add("Felt overcharged", df["overcharged"].dropna().eq("Yes"))
    if "price_known" in df.columns: add("Did not know the price beforehand", df["price_known"].dropna().eq("No"))
    items.sort(key=lambda r: -r[3])
    if items:
        say(f"{'Pain point':45s} {'affected':>10s} {'share':>7s}   CI")
        for label, k, nn, pc, lo, hi in items:
            say(f"{label:45s} {k:>4d}/{nn:<5d} {pc:6.0f}%   [{lo:.0f}%, {hi:.0f}%]")
    else:
        say("Not enough data.")


# ---------- Stage 5: tasks and SUS ----------
def task_analysis(tasks, alpha, two_sided):
    head("STAGE 5 - CURRENT METHOD vs PROTOTYPE")
    if tasks.empty:
        say("No task trials recorded yet. Use the /test panel and the prototype test mode first.")
        return
    cur = tasks[tasks.method == "current"].groupby("participant_code").last()
    pro = tasks[tasks.method == "prototype"].groupby("participant_code").last()
    both = cur.index.intersection(pro.index)
    say(f"Participants with the current method: {len(cur)}; with the prototype: {len(pro)}; with both (paired): {len(both)}")
    if len(both) < 3:
        say("Need at least 3 participants who tried BOTH methods for a paired test (aim for 10 or more).")
        return
    c = cur.loc[both]; p = pro.loc[both]
    alt = "two-sided" if two_sided else "less"

    head("Task time (seconds)")
    for name, x in (("Current method", c.seconds), ("Prototype", p.seconds)):
        m, lo, hi = mean_ci(x, alpha)
        say(f"{name}: n={len(x)}, mean={m:.1f}s, median={x.median():.1f}s, sd={x.std(ddof=1):.1f}s, {int((1 - alpha) * 100)}% CI [{lo:.1f}, {hi:.1f}]")
    diff = (p.seconds - c.seconds).astype(float)
    say(f"Difference (prototype - current): mean = {diff.mean():.1f}s")
    pct = (c.seconds.mean() - p.seconds.mean()) / c.seconds.mean() * 100 if c.seconds.mean() else float("nan")
    say(f"Average time saved: {pct:.0f}%")
    say(f"H0: no difference in mean time    H1: {'times differ' if two_sided else 'prototype time is lower'}    alpha = {alpha}")

    normal = True
    if len(diff) >= 3 and diff.nunique() > 1:
        sh_w, sh_p = stats.shapiro(diff)
        normal = sh_p >= alpha
        say(f"Normality of differences (Shapiro-Wilk): {p_text(sh_p)} -> {'looks normal, use paired t-test' if normal else 'not normal, use Wilcoxon signed-rank'}")
    if normal:
        t, pv = stats.ttest_rel(p.seconds, c.seconds, alternative=alt)
        say(f"Paired t-test: t({len(diff) - 1}) = {t:.2f}, {p_text(pv)} -> {'reject H0' if pv < alpha else 'fail to reject H0'}")
    else:
        try:
            w, pv = stats.wilcoxon(p.seconds, c.seconds, alternative=alt)
            say(f"Wilcoxon signed-rank: W = {w:.1f}, {p_text(pv)} -> {'reject H0' if pv < alpha else 'fail to reject H0'}")
        except ValueError:
            say("Wilcoxon test not possible (all differences are zero).")
    m, lo, hi = mean_ci(diff, alpha)
    say(f"{int((1 - alpha) * 100)}% CI for mean difference: [{lo:.1f}, {hi:.1f}] seconds")
    if diff.std(ddof=1) > 0:
        dz = diff.mean() / diff.std(ddof=1)
        size = "small" if abs(dz) < .5 else "medium" if abs(dz) < .8 else "large"
        say(f"Effect size (Cohen's dz) = {dz:.2f} ({size})")

    plt.figure(figsize=(5, 4.5))
    for cs, ps in zip(c.seconds, p.seconds):
        plt.plot([0, 1], [cs, ps], color="#9aa8c4", marker="o", linewidth=1)
    plt.xticks([0, 1], ["Current method", "Prototype"]); plt.ylabel("Seconds")
    plt.title("Task time per participant"); plt.tight_layout()
    plt.savefig(os.path.join(OUT, "paired_time.png"), dpi=150); plt.close()

    head("Errors")
    if c.errors.notna().any() and p.errors.notna().any():
        say(f"Mean errors: current = {c.errors.mean():.2f}, prototype = {p.errors.mean():.2f}")
    if p.clicks.notna().any():
        say(f"Prototype: mean clicks = {p.clicks.mean():.1f}, mean backtracks = {p.backtracks.mean():.1f}")

    head("Task success")
    kc, kp, nn = int(c.success.sum()), int(p.success.sum()), len(both)
    for name, k in (("Current method", kc), ("Prototype", kp)):
        lo, hi = wilson(k, nn, alpha)
        say(f"{name}: {k}/{nn} succeeded ({k / nn * 100:.0f}%), {int((1 - alpha) * 100)}% Wilson CI [{lo * 100:.0f}%, {hi * 100:.0f}%]")
    b = int(((c.success == 1) & (p.success == 0)).sum())   # worked only with current
    cc = int(((c.success == 0) & (p.success == 1)).sum())  # worked only with prototype
    if b + cc > 0:
        pv = stats.binomtest(cc, b + cc, 0.5).pvalue
        say(f"McNemar exact test (paired): only-prototype = {cc}, only-current = {b}, {p_text(pv)}")
    else:
        say("McNemar test: both methods gave the same result for everyone.")
    table = np.array([[kp, nn - kp], [kc, nn - kc]])
    if table.min() >= 0 and table.sum() > 0:
        odds, pf = stats.fisher_exact(table)
        say(f"Fisher exact test (treating groups as independent, use if you tested separate groups): {p_text(pf)}")
        if table.sum(axis=0).all() and table.sum(axis=1).all():
            expected = stats.contingency.expected_freq(table)
            if expected.min() < 5:
                say("Some expected counts are below 5, so Fisher's exact test is preferred over chi-square.")
            else:
                chi2, pc, _, _ = stats.chi2_contingency(table, correction=False)
                say(f"Chi-square test: chi2 = {chi2:.2f}, {p_text(pc)}")


def sus_analysis(sus, alpha):
    head("SYSTEM USABILITY SCALE (SUS)")
    if sus.empty:
        say("No SUS forms recorded yet.")
        return
    x = sus.score.dropna()
    m, lo, hi = mean_ci(x, alpha)
    say(f"n = {len(x)}, mean SUS = {m:.1f}, median = {x.median():.1f}, sd = {x.std(ddof=1) if len(x) > 1 else float('nan'):.1f}, "
        f"{int((1 - alpha) * 100)}% CI [{lo:.1f}, {hi:.1f}]")
    verdict = "above the commonly used average of 68" if m >= 68 else "below the commonly used average of 68"
    say(f"Interpretation: the mean is {verdict}. (68 is a widely quoted benchmark, 80 or more is considered very good.)")
    if len(x) >= 3 and x.nunique() > 1:
        t, p = stats.ttest_1samp(x, 68, alternative="greater")
        say(f"One-sample t-test against 68 (H1: SUS > 68): t = {t:.2f}, {p_text(p)}")


def main():
    global OUT
    ap = argparse.ArgumentParser(description="LocalHelp AI statistical analysis")
    ap.add_argument("--db", default=os.path.join(ROOT, "localhelp.db"))
    ap.add_argument("--survey-csv", help="CSV exported from Google Forms (rename the columns to the question ids)")
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--two-sided", action="store_true", help="use two-sided tests for the time comparison")
    ap.add_argument("--out", default=os.path.join(HERE, "output"))
    args = ap.parse_args()
    OUT = args.out
    os.makedirs(OUT, exist_ok=True)

    if not os.path.exists(args.db) and not args.survey_csv:
        sys.exit(f"Database not found: {args.db}. Run the app first (python app.py).")

    say(f"LocalHelp AI analysis | database: {args.db} | alpha = {args.alpha}")
    survey = load_survey(args.db, args.survey_csv)
    survey_analysis(survey, OUT, args.alpha)

    if os.path.exists(args.db):
        task_analysis(load_table(args.db, "tasks"), args.alpha, args.two_sided)
        sus_analysis(load_table(args.db, "sus"), args.alpha)

    head("HONEST LIMITS (add to your report)")
    say("- State your sample size, how people were chosen, and who is missing from the sample.")
    say("- Small samples give wide confidence intervals. A non-significant result does not prove there is no effect.")
    say("- Testers may be friends who want to be kind. Say how you reduced this bias.")
    say("- If the prototype did not improve things, report that honestly and explain possible reasons.")

    with open(os.path.join(OUT, "report.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\nSaved report and charts in: {OUT}")


OUT = os.path.join(HERE, "output")

if __name__ == "__main__":
    main()
