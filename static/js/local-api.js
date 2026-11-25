/* local-api.js - the "backend" of the static version (runs inside the browser).

   The Flask version (app.py, db.py, ai_rules.py) needs a Python server. This static version has no server,
   so GitHub Pages can host it. This file does the same jobs in JavaScript:
     - rule-based problem analysis (same rules as ai_rules.py)
     - sample providers (same data as db.py)
     - saving requests, ratings and provider signups in the browser (localStorage)
   Data stays in the visitor's own browser. Nothing is sent to any server.
   All providers, prices and reviews are fictional sample data.
*/
(function () {
  'use strict';

  var CATEGORIES = ['plumbing', 'electrical', 'vehicle', 'electronics', 'cleaning', 'carpentry', 'home', 'other'];

  /* ---------- problem analysis (same rules as ai_rules.py) ---------- */
  var COST_RANGE = {
    plumbing: [300, 800], electrical: [250, 700], vehicle: [200, 900], electronics: [250, 1200],
    cleaning: [400, 1500], carpentry: [350, 1400], home: [300, 1000], other: [250, 900]
  };
  var RULES = [
    { category: 'plumbing', pattern: /leak|pipe|tap|plumb|drain|toilet|flush|paani|pani|nal\b|cistern|geyser|tank/,
      issue: 'Possible pipe or tap leakage',
      tip: 'It looks like a pipe joint, tap or connector is leaking. Close the water valve near it until help arrives.',
      urgency: 'Medium', service: 'Plumber' },
    { category: 'electrical', pattern: /switch|wire|wiring|fan|light|bulb|short|spark|bijli|electric|mcb|socket|inverter|current/,
      issue: 'Possible wiring or switch fault',
      tip: 'This may be a loose connection or a worn switch. Turn off the main switch for that circuit and do not touch exposed wires.',
      urgency: 'High', service: 'Electrician' },
    { category: 'vehicle', pattern: /bike|car\b|scooter|puncture|engine|tyre|tire|brake|battery|gadi|vehicle|starter/,
      issue: 'Possible vehicle mechanical issue',
      tip: 'It could be a tyre, battery or brake problem. Avoid driving until it is checked.',
      urgency: 'Medium', service: 'Mechanic' },
    { category: 'electronics', pattern: /\bac\b|fridge|refrigerator|\btv\b|laptop|phone|washing|cooler|mobile|computer|microwave|screen/,
      issue: 'Possible appliance or electronics fault',
      tip: 'Unplug the device and note any error code or sound. A technician can run a quick diagnosis.',
      urgency: 'Low', service: 'Technician' },
    { category: 'cleaning', pattern: /clean|safai|dust|stain|sofa|bathroom|kitchen|sanitize|pest/,
      issue: 'Deep cleaning needed',
      tip: 'Share the room count or area so the provider can quote an exact price.',
      urgency: 'Low', service: 'Cleaner' },
    { category: 'carpentry', pattern: /door|wood|table|furniture|cupboard|drawer|hinge|darwaza|lakdi|bed\b|wardrobe/,
      issue: 'Possible furniture or door damage',
      tip: 'Likely a loose hinge, joint or worn wood. A carpenter can usually fix it on site.',
      urgency: 'Low', service: 'Carpenter' }
  ];
  var DEFAULT_RULE = {
    category: 'home', issue: 'General home repair',
    tip: 'Add a few more details or a photo so the provider can prepare the right tools.',
    urgency: 'Low', service: 'Handyman'
  };

  function analyze(text, category) {
    text = String(text || '').toLowerCase();
    var hit = null, matchedBy = 'keyword', i;
    for (i = 0; i < RULES.length; i++) {
      if (RULES[i].pattern.test(text)) { hit = RULES[i]; break; }
    }
    if (!hit && category) {
      for (i = 0; i < RULES.length; i++) { if (RULES[i].category === category) { hit = RULES[i]; break; } }
      matchedBy = 'category';
    }
    if (!hit) { hit = DEFAULT_RULE; matchedBy = 'default'; }
    var range = COST_RANGE[hit.category] || COST_RANGE.home;
    return {
      category: hit.category, issue: hit.issue, tip: hit.tip, urgency: hit.urgency, service: hit.service,
      est_min: range[0], est_max: range[1], matched_by: matchedBy
    };
  }

  /* ---------- sample providers (same data as db.py) ---------- */
  var SEED_NAMES = {
    plumbing: ['Raj Plumbing Services', 'Patel Plumbing', 'Ahmed Plumbing Works'],
    electrical: ['Shree Electricals', 'Bright Wiring Co.', 'Khan Electric Works'],
    vehicle: ['Sharma Auto Care', 'Speedy Bike Garage', 'Mehta Motors'],
    electronics: ['Fix-It Electronics', 'Digital Doctor', 'Joshi Repair Hub'],
    cleaning: ['Sparkle Home Cleaners', 'Clean Nest Services', 'Shine Pro Team'],
    carpentry: ['Solanki Carpentry', 'Woodcraft Works', 'Vishal Furniture Fix'],
    home: ['Om Home Fixers', 'Suraj Repair Team', 'Patel Handyman'],
    other: ['Local Helpers', 'City Task Pros', 'QuickHelp Services']
  };
  var DISTANCE = [1.2, 2.0, 2.4], RATING = [4.7, 4.5, 4.3], REVIEWS = [320, 210, 180];
  var SEED = [];
  (function buildSeed() {
    var id = 1;
    CATEGORIES.forEach(function (cat) {
      SEED_NAMES[cat].forEach(function (name, i) {
        var base = COST_RANGE[cat];
        SEED.push({
          id: id++, name: name, category: cat, rating: RATING[i], reviews: REVIEWS[i], distance_km: DISTANCE[i],
          price_min: base[0] + i * 20, price_max: base[1] - i * 50, experience_years: 5 + i,
          available_now: i === 1 ? 0 : 1, areas: 'Ahmedabad, Danilimda, Bapunagar'
        });
      });
    });
  })();

  /* ---------- storage in the visitor's browser (works even if localStorage is blocked) ---------- */
  var memory = {};
  function read(key) {
    try { var v = localStorage.getItem(key); if (v) return JSON.parse(v); } catch (e) { /* blocked */ }
    return memory[key] || [];
  }
  function write(key, value) {
    memory[key] = value;
    try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) { /* blocked */ }
  }

  function num(v, lo, hi) {
    var n = parseInt(v, 10);
    if (isNaN(n) || (lo != null && n < lo) || (hi != null && n > hi)) return null;
    return n;
  }
  function txt(v, limit) { return String(v == null ? '' : v).trim().slice(0, limit); }
  function fail(msg) { throw new Error(msg); }

  /* ---------- the "routes" (same names as the Flask API) ---------- */
  function listProviders(category, sort) {
    if (CATEGORIES.indexOf(category) === -1) fail('Unknown category');
    var all = SEED.concat(read('lh_signups')).filter(function (p) { return p.category === category; });
    var key = { distance: function (p) { return p.distance_km == null ? 99 : p.distance_km; },
                rating: function (p) { return p.rating == null ? 0 : -p.rating; },
                price: function (p) { return p.price_min; } }[sort];
    if (!key) fail('Unknown sort option');
    return all.map(function (p, i) { return { p: p, i: i }; })
      .sort(function (a, b) { return (key(a.p) - key(b.p)) || (a.i - b.i); })
      .map(function (x) { return x.p; });
  }

  function createRequest(d) {
    var pid = num(d.provider_id, 1);
    if (pid === null) fail('Please choose a provider first.');
    var exists = SEED.concat(read('lh_signups')).some(function (p) { return p.id === pid; });
    if (!exists) fail('That provider does not exist.');
    if (CATEGORIES.indexOf(d.category) === -1) fail('Unknown category');
    var list = read('lh_requests');
    var req = {
      id: list.length + 1, provider_id: pid, category: d.category, problem_text: txt(d.problem_text, 500),
      has_photo: d.has_photo ? 1 : 0, issue: txt(d.issue, 120), urgency: txt(d.urgency, 20),
      est_min: num(d.est_min, 0), est_max: num(d.est_max, 0), date_pref: txt(d.date_pref, 30),
      time_pref: txt(d.time_pref, 40), notes: txt(d.notes, 200), rating: null, review: '',
      created_at: new Date().toISOString()
    };
    list.push(req);
    write('lh_requests', list);
    return { id: req.id };
  }

  function rateRequest(id, d) {
    var rating = num(d.rating, 1, 5);
    if (rating === null) fail('Rating must be a number from 1 to 5.');
    var list = read('lh_requests'), found = false;
    list.forEach(function (r) { if (r.id === id) { r.rating = rating; r.review = txt(d.review, 300); found = true; } });
    if (!found) fail('Request not found.');
    write('lh_requests', list);
    return { ok: true };
  }

  function signup(d) {
    if (d.consent !== true) fail('Please tick the box to confirm that your details can be used in this demo.');
    var name = txt(d.name, 60);
    if (name.length < 3) fail('Enter your name or shop name (at least 3 letters).');
    if (CATEGORIES.indexOf(d.category) === -1) fail('Choose a service category.');
    var area = txt(d.area, 60);
    if (area.length < 2) fail('Enter the area where you work.');
    var exp = num(d.experience_years, 0, 50);
    if (exp === null) fail('Experience must be a number from 0 to 50 years.');
    var pmin = num(d.price_min, 50, 20000), pmax = num(d.price_max, 50, 20000);
    if (pmin === null || pmax === null) fail('Enter your usual charge range in rupees (50 to 20000).');
    if (pmin > pmax) fail('The lowest charge cannot be higher than the highest charge.');
    var list = read('lh_signups');
    list.push({
      id: 100 + list.length, name: name, category: d.category, rating: null, reviews: 0, distance_km: null,
      price_min: pmin, price_max: pmax, experience_years: exp, available_now: 1, areas: area
    });
    write('lh_signups', list);
    return { ok: true };
  }

  /* same call style as the Flask version: handle('/api/...', { method, body }) */
  function handle(path, options) {
    return new Promise(function (resolve, reject) {
      try {
        var url = new URL(path, location.href);
        var p = url.pathname.replace(/^.*\/api\//, '/api/');
        var body = (options && options.body) || {};
        if (typeof body === 'string') body = JSON.parse(body);
        var m;
        if (p === '/api/analyze') {
          if (body.category != null && CATEGORIES.indexOf(body.category) === -1) fail('Unknown category');
          var problem = txt(body.text, 500);
          if (!problem && !body.category) fail('Please choose a category or describe the problem.');
          return resolve(analyze(problem, body.category));
        }
        if (p === '/api/providers') {
          return resolve(listProviders(url.searchParams.get('category') || 'home', url.searchParams.get('sort') || 'distance'));
        }
        if (p === '/api/requests') return resolve(createRequest(body));
        if ((m = p.match(/^\/api\/requests\/(\d+)\/rating$/))) return resolve(rateRequest(parseInt(m[1], 10), body));
        if (p === '/api/provider-signup') return resolve(signup(body));
        fail('Not found');
      } catch (e) { reject(e); }
    });
  }

  window.LocalAPI = { handle: handle, analyze: analyze };
})();
