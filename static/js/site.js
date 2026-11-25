/* LocalHelp AI prototype - frontend logic (vanilla JavaScript), STATIC version for GitHub Pages.
   Same screens as the Flask version (static/js/app.js). The only difference: api() calls local-api.js,
   which does the work inside the browser, so no Python server is needed.
*/
(function () {
  'use strict';

  // The Flask version records usage data with tracker.js. The static version does not, so this is an empty stand-in.
  const Tracker = {
    code: '', sessionId: 'static',
    step: function () {}, error: function () {}, backtrack: function () {}, finish: function () {}
  };

  /* ---------- data and text ---------- */
  const CATS = [
    { id: 'home', ic: 'i-home', en: 'Home Repair', hi: 'घर की मरम्मत' },
    { id: 'electrical', ic: 'i-bolt', en: 'Electrical', hi: 'बिजली' },
    { id: 'plumbing', ic: 'i-drop', en: 'Plumbing', hi: 'प्लंबिंग' },
    { id: 'vehicle', ic: 'i-car', en: 'Vehicle Repair', hi: 'वाहन मरम्मत' },
    { id: 'electronics', ic: 'i-tv', en: 'Electronics', hi: 'इलेक्ट्रॉनिक्स' },
    { id: 'cleaning', ic: 'i-spark', en: 'Cleaning', hi: 'सफाई' },
    { id: 'carpentry', ic: 'i-saw', en: 'Carpentry', hi: 'बढ़ईगिरी' },
    { id: 'other', ic: 'i-more', en: 'Other', hi: 'अन्य' }
  ];
  const POPULAR = [
    { id: 'plumbing', en: 'Plumber', hi: 'प्लंबर', from: 300 },
    { id: 'electrical', en: 'Electrician', hi: 'इलेक्ट्रीशियन', from: 250 },
    { id: 'vehicle', en: 'Bike Mechanic', hi: 'बाइक मैकेनिक', from: 200 },
    { id: 'electronics', en: 'AC Repair', hi: 'AC रिपेयर', from: 400 }
  ];
  const TX = {
    en: {
      tag: 'AI Powered Local Services', h1a: 'Your Local Problems,', h1b: 'Smarter Solutions',
      sub: 'Describe your problem, upload a photo, and get the right local professionals with trusted reviews, fair pricing and real-time availability.',
      find: 'Find Help', ph: 'What do you need help with?', t1: 'Verified Professionals', t1s: 'ID and skill checked before listing',
      t2: 'AI Problem Analysis', t2s: 'Photo or text, we find the likely issue', t3: 'Fair Price Estimate', t3s: 'Know the cost range before you book',
      popular: 'Popular Services Near You',
      demo: 'Demo project: providers and prices are sample data, and the analysis uses simple keyword rules. Nothing is really booked.',
      back: '← Back', from: 'From ',
      steps: ['Select Category', 'Upload Photo / Describe', 'AI Analysis', 'Nearby Providers', 'Provider Details', 'Book Service', 'Tracking', 'Service Completed']
    },
    hi: {
      tag: 'AI से चलने वाली लोकल सेवाएं', h1a: 'आपकी लोकल समस्याएं,', h1b: 'स्मार्ट समाधान',
      sub: 'अपनी समस्या बताएं, फोटो डालें और भरोसेमंद रिव्यू, सही दाम और अभी की उपलब्धता के साथ सही लोकल प्रोफेशनल पाएं।',
      find: 'मदद खोजें', ph: 'आपको किस चीज़ में मदद चाहिए?', t1: 'वेरिफाइड प्रोफेशनल', t1s: 'लिस्टिंग से पहले ID और स्किल की जांच',
      t2: 'AI समस्या विश्लेषण', t2s: 'फोटो या टेक्स्ट से संभावित दिक्कत पता चलती है', t3: 'सही दाम का अनुमान', t3s: 'बुक करने से पहले खर्च की रेंज जानें',
      popular: 'आपके पास की लोकप्रिय सेवाएं',
      demo: 'डेमो प्रोजेक्ट: प्रोवाइडर और दाम सैंपल डेटा हैं, और विश्लेषण सरल कीवर्ड नियमों से होता है। कुछ भी सच में बुक नहीं होता।',
      back: '← वापस', from: 'शुरुआत ',
      steps: ['कैटेगरी चुनें', 'फोटो / विवरण', 'AI विश्लेषण', 'पास के प्रोवाइडर', 'प्रोवाइडर की जानकारी', 'सेवा बुक करें', 'ट्रैकिंग', 'सेवा पूरी हुई']
    }
  };

  /* ---------- small helpers ---------- */
  let lang = 'en';
  let step = 1;
  let timer = null;
  let S = {};
  const $ = function (id) { return document.getElementById(id); };
  const T = function (k) { return TX[lang][k]; };
  const rs = function (n) { return '₹' + n; };
  const icon = function (id) { return '<svg aria-hidden="true"><use href="#' + id + '"/></svg>'; };
  const esc = function (s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  };
  const catOf = function (id) { return CATS.filter(function (c) { return c.id === id; })[0]; };
  const catName = function (c) { return lang === 'hi' ? c.hi : c.en; };
  // Providers added through /provider have no rating or distance yet, so show "New provider" and the area.
  function ratingHtml(p, word) {
    return p.rating != null
      ? '<span class="star">★</span> ' + p.rating + ' (' + p.reviews + (word || '') + ')'
      : '<span class="pill">New provider</span>';
  }
  function distText(p, suffix) {
    return p.distance_km != null ? p.distance_km + ' km' + (suffix || '') : esc(p.areas);
  }

  function resetState() {
    S = {
      cat: null, text: '', photo: null, an: null, providers: [], prov: null,
      date: 'Today', time: 'ASAP (Within 1 hour)', notes: '', rating: 0, review: '',
      requestId: null, eta: 12, total: 0
    };
  }
  resetState();

  function toast(msg) {
    const t = $('toast');
    t.textContent = msg; t.hidden = false;
    clearTimeout(toast.h);
    toast.h = setTimeout(function () { t.hidden = true; }, 2600);
  }

  // Static version: the "server" is local-api.js, running in the browser.
  async function api(path, options) {
    return LocalAPI.handle(path, options);
  }

  function showError(id, msg) {
    const el = $(id);
    el.textContent = msg; el.hidden = false;
    Tracker.error(msg);
  }
  function clearError(id) { $(id).hidden = true; }

  /* ---------- language ---------- */
  function applyLang() {
    document.querySelectorAll('[data-t]').forEach(function (e) { e.textContent = T(e.dataset.t); });
    document.querySelectorAll('[data-tp]').forEach(function (e) { e.placeholder = T(e.dataset.tp); });
    $('l-en').setAttribute('aria-pressed', String(lang === 'en'));
    $('l-hi').setAttribute('aria-pressed', String(lang === 'hi'));
    document.documentElement.lang = lang;
    renderHome();
    if (!$('v-flow').hidden) render();
  }
  $('l-en').addEventListener('click', function () { lang = 'en'; applyLang(); });
  $('l-hi').addEventListener('click', function () { lang = 'hi'; applyLang(); });

  /* ---------- home ---------- */
  function renderHome() {
    $('cats').innerHTML = CATS.map(function (c) {
      return '<button type="button" class="cat" data-c="' + c.id + '"><span class="ic">' + icon(c.ic) + '</span>' + esc(catName(c)) + '</button>';
    }).join('');
    $('cats').querySelectorAll('.cat').forEach(function (b) {
      b.addEventListener('click', function () { resetState(); S.cat = b.dataset.c; go(2); });
    });
    $('pop').innerHTML = POPULAR.map(function (p) {
      return '<button type="button" data-c="' + p.id + '"><b>' + esc(lang === 'hi' ? p.hi : p.en) + '</b><span>' + T('from') + rs(p.from) + '</span></button>';
    }).join('');
    $('pop').querySelectorAll('button').forEach(function (b) {
      b.addEventListener('click', function () { resetState(); S.cat = b.dataset.c; go(2); });
    });
  }

  $('homeSearch').addEventListener('submit', async function (e) {
    e.preventDefault();
    clearError('homeError');
    const v = $('q').value.trim();
    resetState();
    if (!v) { go(1); return; }
    S.text = v;
    try {
      await runAnalysis();
      go(3);
    } catch (err) { showError('homeError', err.message); }
  });

  $('mic').addEventListener('click', function () {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { toast('Voice input is not available in this browser. Please type your problem.'); return; }
    try {
      const r = new SR();
      r.lang = lang === 'hi' ? 'hi-IN' : 'en-IN';
      r.onresult = function (ev) { $('q').value = ev.results[0][0].transcript; };
      r.onerror = function () { toast('Voice input failed. Please type your problem.'); };
      r.start();
    } catch (e) { toast('Voice input is not available. Please type your problem.'); }
  });

  /* ---------- flow control ---------- */
  function showFlow(on) {
    $('v-home').hidden = on;
    $('v-flow').hidden = !on;
    window.scrollTo(0, 0);
  }
  function go(n) { step = n; showFlow(true); render(); }

  $('back').addEventListener('click', function () {
    Tracker.backtrack();
    if (step <= 2) { stopTrack(); showFlow(false); return; }
    go(step - 1);
  });

  function bar() {
    $('steps').innerHTML = [1, 2, 3, 4, 5, 6, 7, 8].map(function (i) { return '<i class="' + (i <= step ? 'on' : '') + '"></i>'; }).join('');
    $('stepname').textContent = T('steps')[step - 1];
    $('stepcount').textContent = step + ' / 8';
    $('back').textContent = T('back');
    $('back').hidden = (step === 7 || step === 8);
  }

  function render() {
    stopTrack();
    clearError('flowError');
    bar();
    Tracker.step(step);
    [null, vCat, vDesc, vAI, vProv, vDet, vBook, vTrack, vDone][step]();
    window.scrollTo(0, 0);
  }

  /* ---------- analysis (calls Python backend) ---------- */
  async function runAnalysis() {
    const data = await api('/api/analyze', {
      method: 'POST', body: { text: S.text, category: S.cat }
    });
    S.an = data;
    S.cat = data.category;
  }

  /* ---------- step 1: category ---------- */
  function vCat() {
    $('stage').innerHTML = '<div class="card"><h2>' + (lang === 'hi' ? 'आपको किस चीज़ में मदद चाहिए?' : 'What do you need help with?') + '</h2><div class="cats" id="c2" style="margin:8px 0 0"></div></div>';
    $('c2').innerHTML = CATS.map(function (c) {
      return '<button type="button" class="cat" aria-pressed="' + (S.cat === c.id) + '" data-c="' + c.id + '"><span class="ic">' + icon(c.ic) + '</span>' + esc(catName(c)) + '</button>';
    }).join('');
    $('c2').querySelectorAll('.cat').forEach(function (b) {
      b.addEventListener('click', function () { S.cat = b.dataset.c; go(2); });
    });
  }

  /* ---------- step 2: describe ---------- */
  function vDesc() {
    const c = catOf(S.cat);
    $('stage').innerHTML =
      '<div class="card"><h2>' + (lang === 'hi' ? 'अपनी समस्या बताएं' : 'Describe Your Problem') + '</h2>' +
      (c ? '<span class="pill">' + esc(catName(c)) + '</span>' : '') +
      '<div id="pv"></div>' +
      '<label class="drop" for="ph2">' + icon('i-cam') + (lang === 'hi' ? 'फोटो जोड़ें' : 'Add Photo') + '</label>' +
      '<input id="ph2" type="file" accept="image/*" hidden>' +
      '<label class="f" for="tx">' + (lang === 'hi' ? 'समस्या लिखें' : 'Describe the problem') + '</label>' +
      '<textarea id="tx" maxlength="500" placeholder="' + (lang === 'hi' ? 'जैसे: पाइप से पानी टपक रहा है' : 'e.g. Water is leaking from this pipe.') + '">' + esc(S.text) + '</textarea>' +
      '<div class="meta" style="justify-content:flex-end"><span id="cnt">0/500</span></div>' +
      '<button type="button" class="btn full" id="an">' + (lang === 'hi' ? 'AI से विश्लेषण करें' : 'Analyze with AI') + '</button></div>';

    const tx = $('tx');
    function upd() { S.text = tx.value; $('cnt').textContent = tx.value.length + '/500'; }
    tx.addEventListener('input', upd); upd();

    function pv() {
      $('pv').innerHTML = S.photo
        ? '<div class="preview"><img alt="Photo of the problem" src="' + S.photo + '"><button type="button" id="rm" aria-label="Remove photo">✕</button></div>' : '';
      if (S.photo) $('rm').addEventListener('click', function () { S.photo = null; pv(); });
    }
    pv();

    $('ph2').addEventListener('change', function (e) {
      const f = e.target.files && e.target.files[0];
      if (!f) return;
      if (!/^image\//.test(f.type)) { showError('flowError', 'Please choose an image file (JPG or PNG).'); return; }
      if (f.size > 5 * 1024 * 1024) { showError('flowError', 'The photo is larger than 5 MB. Please choose a smaller one.'); return; }
      clearError('flowError');
      const r = new FileReader();
      r.onload = function () { S.photo = r.result; pv(); };
      r.readAsDataURL(f);   // photo stays in the browser; it is never uploaded
    });

    $('an').addEventListener('click', async function () {
      clearError('flowError');
      if (!S.cat && S.text.trim().length < 3) {
        showError('flowError', 'Please choose a category or describe the problem (at least 3 letters).');
        return;
      }
      this.disabled = true;
      try { await runAnalysis(); go(3); }
      catch (err) { showError('flowError', err.message); this.disabled = false; }
    });
  }

  /* ---------- step 3: AI analysis ---------- */
  function vAI() {
    const a = S.an;
    if (!a) { go(2); return; }
    const c = catOf(S.cat);
    const urgClass = a.urgency === 'Low' ? 'good' : 'warn';
    $('stage').innerHTML =
      (S.photo ? '<div class="card" style="padding:0;overflow:hidden"><img alt="Your photo" src="' + S.photo + '" style="width:100%;max-height:220px;object-fit:cover;display:block"></div>' : '') +
      '<div class="ai"><small>✓ AI Analysis</small><h3>' + esc(a.issue) + '</h3><p>' + esc(a.tip) + '</p></div>' +
      '<div class="card">' +
      '<div class="row"><span>' + (lang === 'hi' ? 'जरूरत' : 'Urgency') + '</span><span class="pill ' + urgClass + '">' + esc(a.urgency) + '</span></div>' +
      '<div class="row"><span>' + (lang === 'hi' ? 'कैटेगरी' : 'Category') + '</span><span class="pill">' + esc(c ? catName(c) : a.category) + '</span></div>' +
      '<div class="row"><span>' + (lang === 'hi' ? 'सुझाई गई सेवा' : 'Recommended Service') + '</span><span class="pill">' + esc(a.service) + '</span></div>' +
      '<div class="row"><span>' + (lang === 'hi' ? 'अनुमानित खर्च' : 'Estimated Cost Range') + '</span><b>' + rs(a.est_min) + ' – ' + rs(a.est_max) + '</b></div>' +
      '<p class="meta" style="margin:8px 0 0">' + (lang === 'hi' ? 'असली खर्च निरीक्षण के बाद बदल सकता है।' : 'May vary based on actual inspection.') + '</p></div>' +
      '<button type="button" class="btn full" id="nx">' + (lang === 'hi' ? 'पास की मदद खोजें' : 'Find Nearby Help') + '</button>';
    $('nx').addEventListener('click', function () { go(4); });
  }

  /* ---------- step 4: providers (from database) ---------- */
  async function vProv() {
    $('stage').innerHTML =
      '<div class="filters"><label for="so" class="meta" style="margin:0">' + (lang === 'hi' ? 'क्रमबद्ध' : 'Sort by') + '</label>' +
      '<select id="so"><option value="distance">' + (lang === 'hi' ? 'दूरी' : 'Distance') + '</option><option value="rating">' + (lang === 'hi' ? 'रेटिंग' : 'Rating') + '</option><option value="price">' + (lang === 'hi' ? 'कीमत' : 'Price') + '</option></select></div>' +
      '<div id="pl"><p class="meta">Loading providers…</p></div>';

    async function load(sort) {
      try {
        S.providers = await api('/api/providers?category=' + encodeURIComponent(S.cat || 'home') + '&sort=' + sort);
        draw();
      } catch (err) { showError('flowError', err.message); $('pl').innerHTML = ''; }
    }
    function draw() {
      if (!S.providers.length) { $('pl').innerHTML = '<p class="meta">No providers found for this category yet.</p>'; return; }
      $('pl').innerHTML = S.providers.map(function (p) {
        return '<div class="card prov"><div class="av">' + esc(p.name.charAt(0)) + '</div><div class="info"><h3>' + esc(p.name) + '</h3>' +
          '<div class="meta"><span>' + ratingHtml(p) + '</span><span>' + distText(p) + '</span></div>' +
          '<div class="meta"><b style="color:var(--ink)">' + rs(p.price_min) + ' – ' + rs(p.price_max) + '</b>' +
          (p.available_now ? '<span class="pill good">Available Now</span>' : '<span class="pill warn">In 30 mins</span>') + '</div>' +
          '<button type="button" class="btn full" data-id="' + p.id + '">' + (lang === 'hi' ? 'सेवा मांगें' : 'Request Service') + '</button></div></div>';
      }).join('');
      $('pl').querySelectorAll('button').forEach(function (b) {
        b.addEventListener('click', function () {
          S.prov = S.providers.filter(function (p) { return String(p.id) === b.dataset.id; })[0];
          go(5);
        });
      });
    }
    $('so').addEventListener('change', function () { load(this.value); });
    load('distance');
  }

  /* ---------- step 5: provider details ---------- */
  const REVIEWS = [
    ['Amit K.', 5, 'Came on time and fixed it in under an hour. Fair price.'],
    ['Neha S.', 5, 'Polite and clean work. Explained the problem clearly.'],
    ['Rohan P.', 4, 'Good work, arrived a little late.']
  ];
  function vDet() {
    const p = S.prov;
    if (!p) { go(4); return; }
    let tab = 'about';
    function draw() {
      $('dt').innerHTML = tab === 'about'
        ? '<div class="row"><span>Experience</span><b>' + p.experience_years + '+ years</b></div>' +
          '<div class="row"><span>Emergency service</span><span class="pill good">Available</span></div>' +
          '<div class="row"><span>Service areas</span><b style="text-align:right">' + esc(p.areas) + '</b></div>'
        : REVIEWS.map(function (r) {
            return '<div class="row" style="display:block"><b>' + esc(r[0]) + '</b> <span class="star">' + '★'.repeat(r[1]) + '</span><div class="meta" style="margin:2px 0 0">' + esc(r[2]) + '</div></div>';
          }).join('');
      document.querySelectorAll('.tabs button').forEach(function (b) { b.setAttribute('aria-selected', String(b.dataset.t === tab)); });
    }
    $('stage').innerHTML =
      '<div class="card"><div class="prov"><div class="av">' + esc(p.name.charAt(0)) + '</div><div class="info"><h3>' + esc(p.name) + '</h3>' +
      '<div class="meta"><span>' + ratingHtml(p, ' reviews') + '</span><span>' + distText(p, ' away') + '</span></div>' +
      (p.available_now ? '<span class="pill good">Available Now</span>' : '<span class="pill warn">In 30 mins</span>') + '</div></div>' +
      '<div class="ctas"><button type="button" data-a="call">Call</button><button type="button" data-a="chat">Chat</button><button type="button" data-a="wa">WhatsApp</button><button type="button" data-a="dir">Directions</button></div>' +
      '<div id="ct" class="sample" hidden></div></div>' +
      '<div class="card"><div class="tabs" role="tablist"><button type="button" role="tab" data-t="about">About</button><button type="button" role="tab" data-t="rev">Reviews</button></div><div id="dt"></div></div>' +
      '<button type="button" class="btn full" id="rq">' + (lang === 'hi' ? 'सेवा मांगें' : 'Request Service') + '</button>';
    document.querySelectorAll('.tabs button').forEach(function (b) { b.addEventListener('click', function () { tab = b.dataset.t; draw(); }); });
    document.querySelectorAll('.ctas button').forEach(function (b) {
      b.addEventListener('click', function () {
        const m = { call: 'Demo only: a real phone number would be shown here.', chat: 'Demo only: in-app chat would open here.', wa: 'Demo only: a WhatsApp chat would open here.', dir: 'Demo only: map directions would open here.' }[b.dataset.a];
        $('ct').hidden = false; $('ct').textContent = m;
      });
    });
    $('rq').addEventListener('click', function () { go(6); });
    draw();
  }

  /* ---------- step 6: booking (saved to database) ---------- */
  function vBook() {
    const p = S.prov, a = S.an;
    if (!p || !a) { go(4); return; }
    function chips(id, vals, key) {
      return '<div class="chips" id="' + id + '">' + vals.map(function (v) { return '<button type="button" aria-pressed="' + (S[key] === v) + '">' + v + '</button>'; }).join('') + '</div>';
    }
    $('stage').innerHTML =
      '<div class="card"><div class="prov"><div class="av">' + esc(p.name.charAt(0)) + '</div><div class="info"><h3>' + esc(p.name) + '</h3><div class="meta"><span>' + ratingHtml(p) + '</span><span>' + distText(p) + '</span></div></div></div></div>' +
      '<div class="card"><h2>' + (lang === 'hi' ? 'सेवा विवरण' : 'Service Details') + '</h2>' +
      '<div class="row"><span>Problem type</span><b>' + esc(a.issue) + '</b></div>' +
      '<div class="row"><span>Estimated cost</span><b>' + rs(p.price_min) + ' – ' + rs(p.price_max) + '</b></div>' +
      '<label class="f">Preferred date</label>' + chips('dg', ['Today', 'Tomorrow', 'Day after'], 'date') +
      '<label class="f">Preferred time</label>' + chips('tg', ['ASAP (Within 1 hour)', 'Morning', 'Afternoon', 'Evening'], 'time') +
      '<label class="f" for="nt">Additional notes (optional, max 200 letters)</label><textarea id="nt" maxlength="200" style="min-height:70px" placeholder="Please bring required parts if needed.">' + esc(S.notes) + '</textarea></div>' +
      '<button type="button" class="btn full" id="cf">' + (lang === 'hi' ? 'अनुरोध की पुष्टि करें' : 'Confirm Request') + '</button>';
    [['dg', 'date'], ['tg', 'time']].forEach(function (g) {
      $(g[0]).querySelectorAll('button').forEach(function (b) {
        b.addEventListener('click', function () {
          S[g[1]] = b.textContent;
          $(g[0]).querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', String(x === b)); });
        });
      });
    });
    $('nt').addEventListener('input', function () { S.notes = this.value; });
    $('cf').addEventListener('click', async function () {
      clearError('flowError');
      this.disabled = true;
      try {
        const res = await api('/api/requests', {
          method: 'POST',
          body: {
            participant_code: Tracker.code || null, session_id: Tracker.sessionId,
            provider_id: p.id, category: S.cat, problem_text: S.text, has_photo: !!S.photo,
            issue: a.issue, urgency: a.urgency, est_min: a.est_min, est_max: a.est_max,
            date_pref: S.date, time_pref: S.time, notes: S.notes
          }
        });
        S.requestId = res.id;
        S.eta = 12;
        Tracker.finish(true);          // stops the test timer (only runs in test mode)
        go(7);
      } catch (err) { showError('flowError', err.message); this.disabled = false; }
    });
  }

  /* ---------- step 7: tracking (simulated) ---------- */
  function stopTrack() { if (timer) { clearInterval(timer); timer = null; } }
  function vTrack() {
    const p = S.prov;
    $('stage').innerHTML =
      '<div class="eta" id="etab"></div><div class="trk" id="trk"></div>' +
      '<svg class="map" viewBox="0 0 400 200" role="img" aria-label="Provider moving towards your location"><rect width="400" height="200" fill="var(--soft)"/>' +
      '<path d="M0 150 L120 120 L200 140 L300 70 L400 60" stroke="var(--line)" stroke-width="14" fill="none"/>' +
      '<path d="M40 165 L120 120 L200 140 L300 70 L355 62" stroke="var(--accent)" stroke-width="4" stroke-dasharray="8 6" fill="none"/>' +
      '<circle cx="355" cy="62" r="9" fill="var(--accent)"/><g id="pm"><circle r="9" fill="var(--good)"/><circle r="3.5" fill="#fff"/></g></svg>' +
      '<div class="card" style="margin-top:12px"><div class="prov"><div class="av">' + esc(p.name.charAt(0)) + '</div><div class="info"><h3>' + esc(p.name) + '</h3><div class="meta"><span id="dk"></span></div></div></div></div>' +
      '<p class="meta">Demo only: the provider movement below is simulated.</p>' +
      '<button type="button" class="btn ghost full" id="cx">Cancel Request</button><div style="height:8px"></div>' +
      '<button type="button" class="btn full" id="fin" hidden>Mark service complete</button>';
    $('cx').addEventListener('click', function () { stopTrack(); resetState(); showFlow(false); toast('Request cancelled'); });
    $('fin').addEventListener('click', function () { S.total = Math.round((p.price_min + p.price_max) / 2 / 10) * 10; go(8); });
    const pts = [[40, 165], [120, 120], [200, 140], [300, 70], [355, 62]];
    const total = 12;
    function paint() {
      const frac = (total - S.eta) / total;
      let seg = Math.min(3, Math.floor(frac * 4)), f = frac * 4 - seg;
      if (frac >= 1) { seg = 3; f = 1; }
      const a = pts[seg], b = pts[seg + 1];
      $('pm').setAttribute('transform', 'translate(' + (a[0] + (b[0] - a[0]) * f) + ',' + (a[1] + (b[1] - a[1]) * f) + ')');
      const arrived = S.eta <= 0;
      $('etab').textContent = arrived ? 'Provider has arrived' : 'Provider is on the way · ETA: ' + S.eta + ' minutes';
      $('dk').textContent = arrived ? 'At your door' : Math.max(0.1, (p.distance_km != null ? p.distance_km : 2) * S.eta / total).toFixed(1) + ' km away';
      const labels = ['Request Placed', 'Provider Confirmed', 'On the Way', 'Arrived'];
      const on = arrived ? 4 : 3;
      $('trk').innerHTML = labels.map(function (l, i) { return '<div class="' + (i < on ? 'on' : '') + '">' + l + '</div>'; }).join('');
      $('fin').hidden = !arrived;
    }
    paint();
    timer = setInterval(function () { if (S.eta > 0) { S.eta--; paint(); } else stopTrack(); }, 1200);
  }

  /* ---------- step 8: completed + rating (saved to database) ---------- */
  function vDone() {
    const p = S.prov;
    $('stage').innerHTML =
      '<div class="card done"><div class="ok">' + icon('i-check') + '</div><h2>Service Completed</h2>' +
      '<p class="meta" style="justify-content:center">Your problem has been resolved!</p>' +
      '<div class="row"><span>Provider</span><b>' + esc(p.name) + '</b></div>' +
      '<div class="row"><span>Total Amount</span><span class="total">' + rs(S.total) + '</span></div>' +
      '<p class="meta" style="margin:0">Sample amount (demo)</p>' +
      '<h3 style="margin-top:18px;font-size:18px">Rate Your Experience</h3><div class="stars" id="st"></div>' +
      '<label class="sr" for="rv">Review</label><textarea id="rv" maxlength="300" placeholder="Write a review (optional)" style="margin-top:8px"></textarea></div>' +
      '<button type="button" class="btn full" id="dn">Done</button>';
    function stars() {
      $('st').innerHTML = [1, 2, 3, 4, 5].map(function (i) { return '<button type="button" class="' + (i <= S.rating ? 'on' : '') + '" aria-label="' + i + ' star">★</button>'; }).join('');
      $('st').querySelectorAll('button').forEach(function (b, i) { b.addEventListener('click', function () { S.rating = i + 1; stars(); }); });
    }
    stars();
    $('dn').addEventListener('click', async function () {
      if (S.rating && S.requestId) {
        try { await api('/api/requests/' + S.requestId + '/rating', { method: 'POST', body: { rating: S.rating, review: $('rv').value } }); }
        catch (err) { showError('flowError', err.message); return; }
      }
      resetState(); showFlow(false); toast('Thanks for your feedback');
    });
  }

  /* ---------- start ---------- */
  applyLang();
})();
