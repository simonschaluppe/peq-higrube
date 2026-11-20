
// National electricity comparison only. Expects `S` injected by the notebook.
const root = document.getElementById('sector-dashboard');
const mount = root?.querySelector('#sd-content');
if (!mount) throw new Error('Missing #sd-content container');

const esc = value => String(value).replace(/[&<>"']/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
}[char]));
const fmt = value => Number.isFinite(value)
  ? new Intl.NumberFormat('de-DE', { maximumFractionDigits: 2 }).format(value)
  : '–';

mount.innerHTML = `
<style>
#sector-dashboard { font: 15px/1.5 system-ui, sans-serif; color: #203b49; max-width: 1200px; margin: 0 auto; padding: 20px; }
#sector-dashboard * { box-sizing: border-box; }
#sector-dashboard h2 { margin: 4px 0 8px; font-size: 24px; }
#sector-dashboard h3 { margin: 0 0 6px; font-size: 18px; }
#sector-dashboard p { margin: 8px 0 14px; }
#sector-dashboard .sd-eyebrow { font-size: 12px; letter-spacing: .12em; color: #127b78; font-weight: 700; }
#sector-dashboard .sd-muted { color: #536a76; font-size: 13px; }
#sector-dashboard .sd-panel { border: 1px solid #d5e1e5; border-radius: 12px; padding: 18px; margin: 16px 0; background: #fff; }
#sector-dashboard .sd-controls { display: grid; grid-template-columns: repeat(3, minmax(180px, 1fr)); gap: 20px; }
#sector-dashboard label { display: block; font-size: 13px; font-weight: 600; }
#sector-dashboard select, #sector-dashboard input { width: 100%; margin-top: 6px; }
#sector-dashboard select { padding: 9px; border: 1px solid #aabfc9; border-radius: 5px; background: white; color: #203b49; }
#sector-dashboard input[type=range] { accent-color: #126663; }
#sector-dashboard .sd-chart svg { display: block; width: 100%; height: auto; }
#sector-dashboard .sd-legend { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 5px 12px; margin: 8px 0 16px; }
#sector-dashboard .sd-legend-item { display: flex; align-items: center; gap: 7px; font-size: 12px; }
#sector-dashboard .sd-swatch { flex: 0 0 12px; width: 12px; height: 12px; border-radius: 2px; }
#sector-dashboard .sd-note { padding: 12px 15px; background: #f0f5fa; border-left: 4px solid #377b99; }
#sector-dashboard .sd-error { color: #a44736; }
#sector-dashboard details summary { cursor: pointer; }
#sector-dashboard pre { white-space: pre-wrap; overflow-wrap: anywhere; font-size: 12px; }
@media (max-width: 720px) {
  #sector-dashboard .sd-controls { grid-template-columns: 1fr; gap: 12px; }
  #sector-dashboard .sd-legend { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
</style>
<p class="sd-eyebrow">GEBÄUDESEKTOR · STROMBILANZ</p>
<h2>Nationales Energiesystem und Gebäudesektor</h2>
<p class="sd-muted">Top-down-Referenz 2040 im Vergleich mit dem ausgewählten Bottom-up-Gebäudeszenario. Primärenergie- und GFZ-Bewertungen sind nicht Teil dieser Darstellung.</p>
<div class="sd-panel">
  <div class="sd-controls">
    <label>Sektorszenario <select id="sd-scenario"></select></label>
    <label>Gebäudeanteil an nationaler PV: <span id="sd-pv-label"></span>
      <input id="sd-pv-share" type="range" min="0" max="100" value="100" step="1">
    </label>
    <label>MIV-Anteil am Verkehrsstrom: <span id="sd-miv-label"></span>
      <input id="sd-miv" type="range" min="0" max="100" value="80" step="1">
    </label>
  </div>
</div>
<div class="sd-panel">
  <h3>Nationale Strombilanz [PJ/a]</h3>
  <p class="sd-muted">Top-down: Gesamtsystem (Bedarf und Erzeugung). Bottom-up: Gebäudestrom und Gebäude-PV zuzüglich MIV-Allokation und zentraler Restdeckung.</p>
  <div id="sd-national-chart" class="sd-chart" role="group" aria-label="Gestapelte Strombilanzen"></div>
  <div id="sd-national-legend" class="sd-legend"></div>
  <p id="sd-comparison"></p>
  <p id="sd-national-note" class="sd-note"></p>
</div>
<details class="sd-panel">
  <summary>Quellen und Datengrundlage</summary>
  <p id="sd-sources" class="sd-muted"></p>
  <pre id="sd-audit"></pre>
</details>
<p id="sd-error" class="sd-error" role="alert"></p>
`;

const el = id => root.querySelector('#sd-' + id);
const scenarios = Object.keys(S.scenarios);
if (!scenarios.length) throw new Error('No scenarios available');

el('scenario').innerHTML = scenarios.map(name =>
  `<option value="${esc(name)}">${esc(name.replaceAll('_', ' '))}</option>`
).join('');
el('scenario').value = scenarios.includes(S.start) ? S.start : scenarios[0];

const palette = {
  'Gebäude': '#437caa', 'MIV': '#9563b1', 'Übriger Verkehr': '#b39cc5',
  'Industrie': '#64798d', 'Landwirtschaft': '#a9a653',
  'Energiebranche': '#84846c', 'Netzverluste': '#bd8a63',
  'Umwandlung': '#9d735d', 'Nettoexport': '#b1bbc2',
  'Gebäude-PV': '#e4b936', 'Freiflächen-PV': '#b5952d',
  'Wasserkraft': '#3994bb', 'Wind': '#67b7b2', 'Biomasse': '#7c9a4b',
  'Geothermie': '#bb795b', 'H₂-Strom': '#9bc7cb', 'Fossil': '#5e6169',
  'Zentrale Restdeckung': '#63a47c', 'Zentraler Fehlbetrag': '#b75a46'
};

function render() {
  const name = el('scenario').value;
  const bu = S.scenarios[name];
  const g = S.national_full.g;
  const d = S.national_full.d;
  const p = Number(el('pv-share').value) / 100;
  const mivShare = Number(el('miv').value) / 100;

  if (!bu || !g || !d) throw new Error('Scenario or national reference data missing');
  const buPV = bu.pv_pj;
  const buD = bu.demand_pj;
  const tdPV = g.pv * p;
  const tdD = d.gebaeude;
  const miv = d.verkehr * mivShare;

  // Same allocation assumptions as in the previous national() chart.
  const otherDemand = d.industrie + d.landwirtschaft + d.verbrauch_sektor_energie
    + d.transportverluste + d.umwandlungseinsatz;
  const central = g.hydro + g.wind + g.biomass + g.geothermal
    + g.hydrogen_electricity + g.fossil + g.pv * (1 - p);
  const netExportAssumption = 5;
  const credit = central - otherDemand - (d.verkehr - miv) - netExportAssumption;

  el('pv-label').textContent = `${fmt(p * 100)} %`;
  el('miv-label').textContent = `${fmt(mivShare * 100)} %`;

  const columns = [
    {title: 'Top-down Bedarf', parts: [
      ['Gebäude', tdD], ['MIV', miv], ['Übriger Verkehr', d.verkehr - miv],
      ['Industrie', d.industrie], ['Landwirtschaft', d.landwirtschaft],
      ['Energiebranche', d.verbrauch_sektor_energie], ['Netzverluste', d.transportverluste],
      ['Umwandlung', d.umwandlungseinsatz], ['Nettoexport', netExportAssumption]
    ]},
    {title: 'Top-down Deckung', parts: [
      ['Gebäude-PV', tdPV], ['Wasserkraft', g.hydro], ['Wind', g.wind],
      ['Biomasse', g.biomass], ['Geothermie', g.geothermal],
      ['H₂-Strom', g.hydrogen_electricity], ['Fossil', g.fossil],
      ['Freiflächen-PV', g.pv * (1 - p)]
    ]},
    {title: 'Bottom-up Bedarf', parts: [
      ['Gebäude', buD], ['MIV', miv], ['Zentraler Fehlbetrag', Math.max(-credit, 0)]
    ]},
    {title: 'Bottom-up Deckung', parts: [
      ['Gebäude-PV', buPV], ['Zentrale Restdeckung', Math.max(credit, 0)]
    ]}
  ];

  const totals = columns.map(c => c.parts.reduce((sum, [, value]) => sum + value, 0));
  const max = Math.max(1, ...totals) * 1.12;
  const y = v => 375 - (v / max) * 335;
  const xPositions = [105, 310, 565, 770];
  const gridStep = max > 600 ? 200 : max > 300 ? 100 : 50;

  let svg = '<svg viewBox="0 0 960 445" role="img" aria-label="Vier gestapelte Strombilanzen in PJ pro Jahr">';
  for (let v = 0; v <= max; v += gridStep) {
    svg += `<line x1="66" x2="924" y1="${y(v)}" y2="${y(v)}" stroke="#dbe4e7"/>`;
    svg += `<text x="57" y="${y(v) + 4}" text-anchor="end" font-size="12">${fmt(v)}</text>`;
  }
  columns.forEach((column, i) => {
    let sum = 0;
    for (const [label, value] of column.parts) {
      if (value <= 0) continue;
      const h = value / max * 335;
      svg += `<rect x="${xPositions[i]}" y="${y(sum + value)}" width="108" height="${h}" fill="${palette[label]}">`;
      svg += `<title>${esc(label)}: ${fmt(value)} PJ/a</title></rect>`;
      sum += value;
    }
    svg += `<text x="${xPositions[i] + 54}" y="${y(sum) - 11}" text-anchor="middle" font-size="14" font-weight="600">${fmt(sum)}</text>`;
    svg += `<text x="${xPositions[i] + 54}" y="406" text-anchor="middle" font-size="13">${esc(column.title)}</text>`;
  });
  svg += '<text x="66" y="20" font-size="13">PJ Strom/a · einheitlicher Maßstab</text></svg>';
  el('national-chart').innerHTML = svg;

  const labels = [...new Set(columns.flatMap(c => c.parts.filter(([, value]) => value > 0).map(([label]) => label)))];
  el('national-legend').innerHTML = labels.map(label =>
    `<span class="sd-legend-item"><span class="sd-swatch" style="background:${palette[label]}"></span>${esc(label)}</span>`
  ).join('');

  el('comparison').textContent =
    `Gebäude-PV: Bottom-up ${fmt(buPV)} vs. Top-down ${fmt(tdPV)} PJ/a ` +
    `(Δ ${fmt(buPV - tdPV)} PJ/a). ` +
    `Gebäudestrombedarf: Bottom-up ${fmt(buD)} vs. Top-down ${fmt(tdD)} PJ/a ` +
    `(Δ ${fmt(buD - tdD)} PJ/a). ` +
    `Gebäudesaldo: Bottom-up ${fmt(buPV - buD)} vs. Top-down ${fmt(tdPV - tdD)} PJ/a.`;

  const nationalBalance = totals[1] - totals[0];
  const extra = name === 'Bestand_2024' ? 'Bestand 2024 gegenüber der Referenz 2040. ' : '';
  el('national-note').textContent = extra +
    `Nationaler Modellrest: ${fmt(nationalBalance)} PJ/a. ` +
    `Nettoexport: ${fmt(netExportAssumption)} PJ/a Modellannahme (7 PJ/a in der Quelle). ` +
    `Zentrale Restdeckung: ${fmt(credit)} PJ/a; zugeordnetes Budget, keine zusätzliche nationale Erzeugung. ` +
    `Die Slider ändern ausschließlich die Top-down-Allokation und den MIV-Budgetanteil, nicht die Bottom-up-Szenariowerte.`;
}

el('sources').textContent = (S.sources || []).map(s =>
  `${s.Quelle}, ${s.Fundstelle}: ${fmt(s.Wert_PJ)} PJ/a (${s.Datei})`
).join(' · ');
el('audit').textContent = JSON.stringify({
  data_sha256: S.data_sha256, provenance: S.provenance
}, null, 2);

function safeRender() {
  try {
    el('error').textContent = '';
    render();
  } catch (error) {
    el('error').textContent = `Dashboard-Fehler: ${error.message}`;
    console.error(error);
  }
}
el('scenario').addEventListener('change', safeRender);
el('pv-share').addEventListener('input', safeRender);
el('miv').addEventListener('input', safeRender);
safeRender();
