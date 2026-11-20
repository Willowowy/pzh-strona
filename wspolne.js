/* =========================================================
   WSPÓLNE DLA WSZYSTKICH STRON
   (data, przewijany pasek, licznik odwiedzin, wyszukiwarka na podstronach)
   ========================================================= */

/* ---------- data w górnym pasku i rok w stopce ---------- */
(function () {
  var teraz = new Date();
  document.getElementById('data').textContent = 'Dziś jest ' +
    teraz.toLocaleDateString('pl-PL', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
  document.getElementById('rok').textContent = teraz.getFullYear();
})();

/* ---------- przewijany pasek – tytuły z Tadziennika (newsy.json) ---------- */
(function () {
  var tasma = document.getElementById('tasma-tekst');
  function wypelnij(tytuly) {
    tytuly = ['Subskrybuj kanał!'].concat(tytuly);
    tasma.textContent = '';
    tytuly.forEach(function (t, i) {
      if (i) { var b = document.createElement('b'); b.textContent = '+++'; tasma.appendChild(b); }
      tasma.appendChild(document.createTextNode(t));
    });
  }
  wypelnij([]);
  fetch('newsy.json', { cache: 'no-cache' })
    .then(function (odp) { if (!odp.ok) throw new Error(odp.status); return odp.json(); })
    .then(function (newsy) {
      if (Array.isArray(newsy)) wypelnij(newsy.map(function (n) { return n.tytul; }));
    })
    .catch(function () {});
})();

/* ---------- licznik odwiedzin (liczy wizyty w tej przeglądarce) ---------- */
(function () {
  var cyfry = document.getElementById('cyfry');
  if (!cyfry) return;
  var start = 13742; // "historyczne" odwiedziny – zmień jak chcesz
  var wizyty = 1;
  try {
    wizyty = parseInt(localStorage.getItem('pzh-wizyty') || '0', 10) + 1;
    localStorage.setItem('pzh-wizyty', wizyty);
  } catch (e) {}
  String(start + wizyty).padStart(7, '0').split('').forEach(function (c) {
    var s = document.createElement('span');
    s.textContent = c;
    cyfry.appendChild(s);
  });
})();
