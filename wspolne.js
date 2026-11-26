/* =========================================================
   WSPÓLNE DLA WSZYSTKICH STRON
   (data, przewijany pasek, licznik odwiedzin, wyszukiwarka na podstronach)
   ========================================================= */

/* ---------- rok w stopce ---------- */
(function () {
  var rok = document.getElementById('rok');
  if (rok) rok.textContent = new Date().getFullYear();
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

/* ---------- tymczasowo wyłączone przyciski menu ---------- */
document.querySelectorAll('#menu a.zablokowany').forEach(function (a) {
  a.addEventListener('click', function (e) { e.preventDefault(); });
});

/* ---------- stopka: czas od ostatniej aktualizacji (ostatni commit na GitHubie, bez commitów bota od newsów) ---------- */
(function () {
  var stopka = document.getElementById('stopka');
  if (!stopka) return;
  var REPO = 'Willowowy/pzh-strona';
  var KLUCZ = 'pzh-ostatni-commit-2';

  var box = document.createElement('div');
  box.className = 'aktualizacja';
  box.innerHTML = '<span class="aktualizacja-tytul">OSTATNIA AKTUALIZACJA</span>' +
    '<span class="aktualizacja-data">…</span><span class="aktualizacja-timer">--:--:--</span>';
  stopka.appendChild(box);
  var poleData = box.querySelector('.aktualizacja-data');
  var poleTimer = box.querySelector('.aktualizacja-timer');

  function dwa(n) { return (n < 10 ? '0' : '') + n; }
  function start(kiedy) {
    var d = new Date(kiedy);
    if (isNaN(d)) { poleData.textContent = 'brak danych'; poleTimer.textContent = ''; return; }
    poleData.textContent = dwa(d.getDate()) + '.' + dwa(d.getMonth() + 1) + '.' + d.getFullYear() + ' ' + dwa(d.getHours()) + ':' + dwa(d.getMinutes());
    function tik() {
      var s = Math.max(0, Math.floor((Date.now() - d.getTime()) / 1000));
      var dni = Math.floor(s / 86400); s %= 86400;
      poleTimer.textContent = (dni ? dni + ' d ' : '') + dwa(Math.floor(s / 3600)) + ':' + dwa(Math.floor(s / 60) % 60) + ':' + dwa(s % 60) + ' temu';
    }
    tik();
    setInterval(tik, 1000);
  }

  /* zapamiętujemy na 10 minut, żeby nie pytać GitHuba przy każdej podstronie */
  try {
    var zapis = JSON.parse(sessionStorage.getItem(KLUCZ) || 'null');
    if (zapis && Date.now() - zapis.t < 10 * 60 * 1000) { start(zapis.data); return; }
  } catch (e) {}

  fetch('https://api.github.com/repos/' + REPO + '/commits?per_page=100')
    .then(function (odp) { if (!odp.ok) throw new Error(odp.status); return odp.json(); })
    .then(function (lista) {
      var wlasny = lista.filter(function (c) {
        var login = (c.author && c.author.login) || '';
        return !/\[bot\]$/.test(login) && !/^Tadziennik:/.test(c.commit.message);
      })[0];
      if (!wlasny) throw new Error('brak');
      var data = wlasny.commit.committer.date;
      try { sessionStorage.setItem(KLUCZ, JSON.stringify({ t: Date.now(), data: data })); } catch (e) {}
      start(data);
    })
    .catch(function () {
      /* awaryjnie: data ostatniej zmiany pliku z serwera */
      start(location.protocol.indexOf('http') === 0 ? document.lastModified : NaN);
    });
})();
