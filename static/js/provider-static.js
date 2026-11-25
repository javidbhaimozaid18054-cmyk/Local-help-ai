/* Provider signup page (static version): checks the form, then saves the provider in this browser.
   The provider then appears in the customer list as "New provider". */
(function () {
  'use strict';
  const $ = function (id) { return document.getElementById(id); };
  const form = $('provForm');
  const errBox = $('provError');

  function fail(msg) {
    errBox.textContent = msg; errBox.hidden = false;
    errBox.scrollIntoView({ block: 'center' });
  }

  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    errBox.hidden = true;
    const pmin = parseInt($('pmin').value, 10);
    const pmax = parseInt($('pmax').value, 10);
    const exp = parseInt($('experience').value, 10);

    if ($('name').value.trim().length < 3) return fail('Enter your name or shop name (at least 3 letters).');
    if (!$('category').value) return fail('Choose the service you provide.');
    if ($('area').value.trim().length < 2) return fail('Enter the area where you work.');
    if (isNaN(exp) || exp < 0 || exp > 50) return fail('Experience must be a number from 0 to 50 years.');
    if (isNaN(pmin) || isNaN(pmax) || pmin < 50 || pmax > 20000) return fail('Enter your usual charge range in rupees (50 to 20000).');
    if (pmin > pmax) return fail('The lowest charge cannot be higher than the highest charge.');
    if (!$('consent').checked) return fail('Please tick the box to continue.');

    const btn = form.querySelector('button[type="submit"]');
    btn.disabled = true;
    try {
      await LocalAPI.handle('/api/provider-signup', {
        method: 'POST',
        body: {
          name: $('name').value, category: $('category').value, area: $('area').value,
          experience_years: exp, price_min: pmin, price_max: pmax,
          about: $('about').value, consent: $('consent').checked
        }
      });
      form.hidden = true;
      $('provDone').hidden = false;
      window.scrollTo(0, 0);
    } catch (err) {
      fail(err.message); btn.disabled = false;
    }
  });
})();
