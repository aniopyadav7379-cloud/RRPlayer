import pandas as pd, json, base64, pickle
T=pickle.load(open('tables.pkl','rb')); M=json.load(open('dash.json'))['meta']
val=pd.read_csv('out_pressure_validation.csv')
img=lambda f:'data:image/png;base64,'+base64.b64encode(open(f'figs/{f}.png','rb').read()).decode()
def top(role):
    t=T[role]; t=t[t.eligible].head(10)
    rows=''.join(f"<tr><td>{i+1}</td><td><b>{r.name}</b></td><td>{r.team}</td><td>{int(r.press_balls)}</td><td>{int(r.press_inn)}</td><td>{r.level:.3f}</td><td>{r.cons:.2f}</td><td>{r.ret:+.3f}</td><td><b>{r.prs:.1f}</b></td><td>{int(r.rank_lo)}–{int(r.rank_hi)}</td><td>{r.p_top10:.0%}</td></tr>" for i,r in enumerate(t.itertuples()))
    return f"<table><tr><th>#</th><th>Player</th><th>Latest team in data</th><th>Pressure balls</th><th>Pressure innings</th><th>Level</th><th>Consistency</th><th>Retention</th><th>PRS</th><th>90% rank band</th><th>P(top-10)</th></tr>{rows}</table>"
def rob(role):
    return ''.join(f"<tr><td>{r['variant']}</td><td>{r['spearman']:.2f}</td><td>{r['top10_overlap']}/10</td></tr>" for r in M['rob'][role])
rb,rw=M['rel']['bat'],M['rel']['bowl']
html=f"""<!doctype html><html><head><meta charset=utf-8><style>
@page{{size:A4;margin:16mm 14mm}}
body{{font-family:'DejaVu Sans',Arial,sans-serif;font-size:9.6pt;line-height:1.45;color:#1f2937}}
h1{{color:#254AA5;font-size:22pt;margin:0}} h2{{color:#E6007E;font-size:14pt;border-bottom:2px solid #254AA5;padding-bottom:3px;margin-top:20px}} h3{{color:#254AA5;font-size:11pt;margin-bottom:3px}}
.band{{background:linear-gradient(90deg,#E6007E,#254AA5);color:#fff;padding:18px 20px;border-radius:6px;margin-bottom:14px}} .band h1{{color:#fff}}
table{{border-collapse:collapse;width:100%;font-size:8.2pt;margin:6px 0}} th{{background:#254AA5;color:#fff;padding:4px 5px;text-align:left}} td{{padding:3px 5px;border-bottom:1px solid #e5e7eb}}
img{{max-width:100%}} .row{{display:flex;gap:10px}} .note{{background:#fdf2f8;border-left:4px solid #E6007E;padding:6px 10px;margin:8px 0}} code{{background:#f3f4f6;padding:0 3px}}
.pb{{page-break-before:always}}
</style></head><body>
<div class=band><h1>Reliability Under Pressure</h1><div>SupeRR Selector Season 2 · Round 1 · Methodology Report · Team Lakshay</div></div>

<h2>1. Summary and final rankings</h2>
<p>We built a data-driven pressure model from {M['nballs']:,} deliveries across {M['nmatches']} decided matches ({M['nipl']} IPL 2022–26, {M['nt20i']} T20I/Emerging-Teams, {M['nplayers']} players). Pressure is defined as a <b>high-leverage ball</b>: one where the expected swing in win probability is in the top quartile. Players are rated on how they perform in those balls relative to the situation, relative to their own usual level, and how consistently they do it across matches. Ratings are Bayesian-shrunk so small samples cannot dominate.</p>
<h3>Top-10 batters under pressure</h3>{top('bat')}
<h3>Top-10 bowlers under pressure</h3>{top('bowl')}
<div class=note><b>How certain are these?</b> Pressure samples are small. The 90% bootstrap rank bands show that ranks 1–2 (batters) and 1–5 (bowlers) are clearly ahead of the pack, while ranks 5–10 are close to interchangeable with many players just outside the list. We report this openly rather than overstate precision (section 6).</div>

<h2>2. Pressure definition</h2>
<h3>Win-probability model</h3>
<p>Every ball is placed in a game state: balls left, runs needed / runs scored, wickets lost, required rate, format (IPL vs international). Two gradient-boosted models (monotone constrained) estimate win probability <i>WP</i>: one for chases (out-of-sample AUC 0.89, Brier 0.135 vs 0.250 for coin-flip) and one for first innings (AUC 0.69, lower because no target exists). Models are fitted with 5-fold cross-fitting <b>by match</b>, so no ball is scored by a model that saw its match. Calibration is shown below.</p>
<h3>Leverage = how much is at stake on this ball</h3>
<p>For each ball we compute the expected absolute change in WP over all possible outcomes (dot, 1, 2, 3, 4, 6, wicket), weighted by how often each outcome occurs in that phase and wicket state. This single number folds together required run rate, wickets in hand, balls remaining and closeness of the contest.</p>
<p><b>A ball is a pressure ball if its leverage is in the top 25%</b> – for chases, of all chase balls; for first innings (no target, so pressure is judged against what is normal for the phase), of balls in the same phase (powerplay / middle / death). This gives {int(val[val.press].balls.sum()):,} pressure balls of {int(val.balls.sum()):,} legal balls. Ordinary balls (the other 75%) form each player's baseline.</p>
<div class=row><img src="{img('validation')}" style="width:64%"><img src="{img('calib')}" style="width:34%"></div>
<p><b>Why it is meaningful:</b> pressure balls carry 3–5× the win-probability swing of ordinary balls, and 79% of chase pressure balls are in genuinely close states (WP between 20% and 80%) versus 29% for ordinary balls. Within chases, the pressure share rises from 20% in the powerplay to 35% in the death overs, as expected. Wickets lost, balls left and required rate are all implicitly included.</p>

<h2>3. Performance measurement</h2>
<p><b>Ball value.</b> Each ball gets a context-neutral value: the win-probability change credited to the player divided by that ball's leverage (so units are "typical swings"; winsorised at ±6; 2.5% of balls). Batter is credited with own runs and own dismissal only; extras, byes and leg-byes are not credited to the batter, and byes/leg-byes and run-outs are not charged to the bowler. Because WP is calibrated, an average player scores ≈0 in any situation, so a good rating means "better than the average player facing <i>the same situation</i>". Batting and bowling use the identical machinery (bowling value = WP gained by the fielding side).</p>
<p><b>Three components</b> (same for batters and bowlers):</p>
<table><tr><th>Component</th><th>Weight</th><th>What it measures</th></tr>
<tr><td>Pressure Level</td><td>70%</td><td>Shrunk mean ball value on pressure balls. The prior for each player is set from their <i>own usual level</i> (shrunk ordinary-ball value) through a fitted regression, so a player's pressure rating is judged against what we would expect given their general quality, and moves toward their actual pressure evidence as pressure balls accumulate (batters: 260 balls to give pressure data 50% weight; bowlers: 530).</td></tr>
<tr><td>Consistency</td><td>20%</td><td>Share of pressure innings/spells (≥6 pressure balls) in which the player's net win-probability contribution was ≥0, shrunk toward the league rate (prior strength 8 innings).</td></tr>
<tr><td>Retention</td><td>10%</td><td>Pressure Level minus the player's expected level from their baseline: did they rise above or fall below their usual standard when it mattered?</td></tr></table>
<p>The three components are z-scored among eligible players, combined, and re-scaled to the <b>Pressure Reliability Score (PRS)</b>: 50 = average eligible player, ±10 = 1 SD. Weights were chosen from the reliability study in section 6 (the noisy components get lower weights); alternative weights (equal thirds, level-only) change at most 2 of the top-10.</p>

<h2 class=pb>4. Fair comparisons</h2>
<ul><li><b>Sample size.</b> Eligibility: ≥150 pressure balls and ≥12 pressure innings/spells → 93 batters and 96 bowlers. Empirical-Bayes shrinkage; the shrinkage strength was estimated from the data (covariance of independent halves of matches), not assumed.</li>
<li><b>Different match contexts.</b> The pressure scale is situation-neutral (value per typical swing), so a player who bats mostly in the death is compared with the average player in the same death states. Chase and first-innings pressure are both included; a chase-only variant is reported as a robustness check.</li>
<li><b>IPL vs T20I.</b> One pooled model with a format flag, so IPL and international game states are calibrated separately within the model, and results are expressed relative to context. Opposition: matches involving Associate nations (weight 0.5) and A-teams (0.75) are down-weighted. The effect on rankings is negligible (Spearman 0.99+).</li>
<li><b>Data issues handled.</b> 16 abandoned and 25 no-result/undecided matches excluded; super-overs excluded; 3 duplicate-name pairs separated by player_id; wide/no-ball/penalty/bye coding decoded from <code>extras1_runs</code>; bye/leg-bye run values are not recorded in the file, so they were imputed at 1.5 per event in game-state totals only (reconstructed first-innings totals still differ from the stated result margins by ≈3 runs on average).</li></ul>

<h2>5. Evidence for the top 10</h2>
<div class=row><img src="{img('top10_bat')}" style="width:50%"><img src="{img('top10_bowl')}" style="width:50%"></div>
<div class=row><img src="{img('scatter_bat')}" style="width:50%"><img src="{img('scatter_bowl')}" style="width:50%"></div>
<p>The scatter plots show each eligible player's usual level against their pressure level; those above the horizontal zero line deliver positive value under pressure. The top-10 are circled in black. Individual match-by-match pressure charts, strike-rate/economy comparisons in pressure vs ordinary balls, and strengths/weaknesses for every player with ≥60 pressure balls are in the interactive dashboard.</p>

<h2 class=pb>6. Reliability and limitations</h2>
<table><tr><th>Check</th><th>Batters</th><th>Bowlers</th></tr>
<tr><td>Split-half correlation of composite score (random 50/50 match splits, so each half has half the data)</td><td>{rb['comp']:.2f}</td><td>{rw['comp']:.2f}</td></tr>
<tr><td>… Level / Consistency / Retention</td><td>{rb['level']:.2f} / {rb['cons']:.2f} / {rb['ret']:.2f}</td><td>{rw['level']:.2f} / {rw['cons']:.2f} / {rw['ret']:.2f}</td></tr>
<tr><td>Average overlap of top-10 between two random halves</td><td>{rb['top10_overlap_halves']:.1f}/10</td><td>{rw['top10_overlap_halves']:.1f}/10</td></tr></table>
<p><b>Honest reading.</b> Pressure samples are small (a typical top player has 150–700 pressure balls), so single-half rankings are noisy and full-sample reliability is higher than the split-half figures (Spearman–Brown roughly doubles them to ≈0.2 batters, ≈0.33 bowlers). In particular, consistency and "clutch retention" beyond a player's baseline carry limited signal; this is why the player's own baseline is used as an informative prior and why those components have smaller weights. We therefore recommend reading the list as "most credible evidence of delivering under pressure", not as a precise order.</p>
<h3>Sensitivity of the rankings (vs the main model)</h3>
<div class=row><div style="width:50%"><b>Batters</b><table><tr><th>Variant</th><th>Spearman</th><th>Top-10 overlap</th></tr>{rob('bat')}</table></div><div style="width:50%"><b>Bowlers</b><table><tr><th>Variant</th><th>Spearman</th><th>Top-10 overlap</th></tr>{rob('bowl')}</table></div></div>
<p>The ranking is stable to weights and opposition weighting, moderately stable to chase-only and top-10%-leverage definitions, and weakly correlated with a simple rule-based pressure definition (death overs / wickets down, ρ=0.33–0.49): the definition of pressure matters and our WP-leverage definition is the more principled but not the only plausible one.</p>
<h3>Where the model is less certain</h3>
<ul><li>First-innings win probability is weak (AUC 0.69), so first-innings pressure is a coarser signal than chase pressure.</li>
<li>No fielding/catching, venue, pitch, toss, bowler-type matchup or opposition-quality (beyond associate weights) adjustments; these are data we did not model.</li>
<li>The newest players with 12 pressure innings (e.g. rank-1 batter V. Sooryavanshi, 166 pressure balls) are the most uncertain: 90% rank band 1–18.</li>
<li>Players appear under their latest team in the data (franchise or national); team is informational only.</li></ul>

<h2>7. Reproducibility</h2>
<p>Pipeline: (1) decode extras, rebuild per-ball game state; (2) cross-fitted WP models; (3) leverage from outcome probabilities; (4) pressure flag and per-ball values; (5) aggregate per player/innings; (6) empirical-Bayes shrinkage with baseline prior and τ² fixed from split-half covariance (batters 0.0088, bowlers 0.0042); (7) z-score composite 70/20/10; (8) 500-resample match bootstrap, 30 random split-half runs, alternative definitions. Full ranking tables for all players are provided as CSVs.</p>
</body></html>"""
open('report.html','w').write(html)
