"use strict";

const state = new Proxy(
  {
    mailStep: 0,
    version: "one",
    labMode: "hash",
    room: "doctor",
  },
  {
    set(target, key, value) {
      if (target[key] === value) return true;
      target[key] = value;
      window.dispatchEvent(new CustomEvent("site-state", { detail: { key, value } }));
      return true;
    },
  },
);

class ReactiveElement extends HTMLElement {
  connectedCallback() {
    this._onState = (event) => {
      if (!this.stateKeys || this.stateKeys.includes(event.detail.key)) this.render();
    };
    window.addEventListener("site-state", this._onState);
    this.render();
  }

  disconnectedCallback() {
    window.removeEventListener("site-state", this._onState);
  }

  render() {}
}

const mailSteps = [
  {
    label: "A nyitott lap",
    title: "Ami nincs lezárva, azt a postás is elolvashatja",
    body: "Egy képeslap szövege szabad szemmel látható. A hagyományos, nem végpontok között titkosított üzenetnél a szolgáltató gépe is hozzáférhet a tartalomhoz.",
    note: "Találkozunk 6-kor a parkban?",
    open: true,
    lock: false,
    scanner: false,
    before: false,
  },
  {
    label: "A lezárt boríték · kulcs nélkül olvashatatlan",
    title: "A végpontok közötti titkosításnál kulcs nélkül csak értelmetlen jelsor látszik",
    body: "A küldő telefonja az olvasható üzenetet titkosított jelsorrá alakítja. Ha a postás, a szolgáltató vagy egy támadó kulcs nélkül próbálja megnyitni, csak összekuszált karaktereket lát. Az eredeti mondatot kizárólag a címzett készüléke tudja visszaállítani a rajta lévő kulccsal.",
    note: "Találkozunk 6-kor a parkban?",
    cipher: "7F A9 C2 10 · 4D 8B E1 6C",
    open: false,
    lock: true,
    encrypted: true,
    scanner: false,
    before: false,
  },
  {
    label: "Ellenőrzés útközben",
    title: "A lezárt levelet útközben csak felnyitva lehet átvizsgálni",
    body: "Ha a szolgáltató szerverén akarják ellenőrizni a tartalmat, hozzáférés kell a tiszta szöveghez vagy képhez. Ezzel a zár eredeti biztonsági ígérete megváltozik.",
    note: "A tartalomhoz hozzáférés szükséges.",
    open: true,
    lock: false,
    scanner: true,
    before: false,
  },
  {
    label: "Ellenőrzés lezárás előtt",
    title: "A készüléken végzett vizsgálat a lezárás előtti ellenőrzés",
    body: "A készüléken végzett ellenőrzésnél az üzenetet még elküldés előtt vizsgálják át. Az adatátvitel ezután titkosított maradhat, de a tartalom a lezárás előtt már hozzáférhető volt a vizsgáló rendszer számára.",
    note: "Ellenőrizve, aztán lezárva.",
    open: true,
    lock: true,
    scanner: true,
    before: true,
  },
];

class MailStory extends ReactiveElement {
  stateKeys = ["mailStep"];

  render() {
    const item = mailSteps[state.mailStep];
    this.innerHTML = `
      <div class="interactive-card" aria-live="polite">
        <div class="interactive-topline">
          <span>Levéltörténet · ${state.mailStep + 1}/${mailSteps.length}</span>
          <div class="step-dots" aria-label="Történet lépései">
            ${mailSteps
              .map(
                (_, index) => `<button class="step-dot" type="button" data-step="${index}" ${
                  index === state.mailStep ? 'aria-current="step"' : ""
                }><span class="sr-only">${index + 1}. lépés</span></button>`,
              )
              .join("")}
          </div>
        </div>
        <div class="mail-stage">
          <div class="mail-illustration" aria-hidden="true">
            <div class="postman mail-postman mail-postman--step-${state.mailStep}">
              <span class="postman-head"></span><span class="postman-cap"></span><span class="postman-body"></span>
              <span class="postman-arm postman-arm--front"></span><span class="postman-arm postman-arm--back"></span>
              <span class="postman-leg postman-leg--front"></span><span class="postman-leg postman-leg--back"></span>
              <span class="postman-bag">✉</span>
            </div>
            <div class="mail-object ${item.open ? "is-open" : ""} ${item.encrypted ? "is-e2ee" : ""} ${state.mailStep === 0 ? "is-postman-opened" : ""}">
              <div class="mail-note">
                ${item.cipher ? `<span class="mail-note-cipher">${item.cipher}</span>` : ""}
                <span class="mail-note-plain">${item.note}</span>
              </div>
              ${state.mailStep === 0 ? '<span class="mail-opening-label">A postás felnyitja</span>' : ""}
              ${item.lock ? '<span class="mail-lock"></span>' : ""}
            </div>
            ${item.encrypted ? `
              <div class="mail-e2ee-no-key">
                <b>Kulcs nélküli próbálkozás</b>
                <code>${item.cipher}</code>
                <span>Olvashatatlan titkosított adat</span>
              </div>
              <div class="mail-e2ee-key">
                <i aria-hidden="true"></i>
                <span><b>Kulcs a címzett készülékén</b><small>Csak ezzel áll helyre az üzenet</small></span>
              </div>
              <i class="mail-e2ee-key-traveller" aria-hidden="true"></i>` : ""}
            ${item.scanner ? '<span class="mail-scanner"></span>' : ""}
            ${item.before ? '<span class="before-seal">ÁTVILÁGÍTÁS<br>LEZÁRÁS ELŐTT</span>' : ""}
          </div>
          <div class="mail-copy">
            <p class="mini-label">${item.label}</p>
            <h3>${item.title}</h3>
            <p>${item.body}</p>
            ${item.encrypted ? `
              <div class="mail-key-comparison" aria-label="Kulcs nélkül és a címzett kulcsával">
                <div>
                  <span>Kulcs nélkül</span>
                  <code>${item.cipher}</code>
                  <small>Csak a titkosított jelsor látszik.</small>
                </div>
                <i aria-hidden="true">→</i>
                <div>
                  <span>A címzett kulcsával</span>
                  <strong>${item.note}</strong>
                  <small>A címzett készüléke visszaállítja az eredeti üzenetet.</small>
                </div>
              </div>` : ""}
            <div class="mail-controls">
              <button class="round-button" type="button" data-mail-prev ${state.mailStep === 0 ? "disabled" : ""}>← Vissza</button>
              <button class="round-button next" type="button" data-mail-next ${state.mailStep === mailSteps.length - 1 ? "disabled" : ""}>Tovább →</button>
            </div>
          </div>
        </div>
      </div>`;

    this.querySelectorAll("[data-step]").forEach((button) =>
      button.addEventListener("click", () => (state.mailStep = Number(button.dataset.step))),
    );
    this.querySelector("[data-mail-prev]")?.addEventListener("click", () => (state.mailStep -= 1));
    this.querySelector("[data-mail-next]")?.addEventListener("click", () => (state.mailStep += 1));
  }
}

const encryptionModes = {
  https: {
    tab: "Átvitel közben · HTTPS/TLS",
    title: "A cső zárva van, de a szolgáltató végén kinyílik",
    body: "A HTTPS vagy TLS megakadályozza, hogy egy kávézó Wi-Fi-jén vagy az internet útvonalán valaki egyszerűen beleolvasson az adatforgalomba. A kapcsolat azonban a szolgáltató szerverén véget ér, ahol a tartalom ismét olvasható lehet.",
    keyOwner: "A kapcsolat kulcsait a készülék és a szolgáltató szervere kezeli.",
    provider: "Igen — a szerveren a szolgáltató hozzáférhet a tiszta tartalomhoz.",
    protects: "Útközbeni lehallgatás ellen.",
    limit: "Nem védi a tartalmat magától a szolgáltatótól vagy egy szerverfeltöréstől.",
    packet: "Útközben zárva",
    keyAt: ["sender", "provider", "recipient"],
    providerCanRead: true,
    storageCanRead: true,
  },
  providerRest: {
    tab: "Tároláskor · szolgáltatói kulcs",
    title: "A raktár zárva van, de a raktárosnál van a kulcs",
    body: "A lemez vagy adatbázis titkosítása védi az ellopott merevlemezt és bizonyos üzemeltetési hibákat. Ha a feloldó kulcsot ugyanaz a szolgáltató kezeli, jogosult rendszerként továbbra is fel tudja oldani a tárolt tartalmat.",
    keyOwner: "A tárolási kulcs a szolgáltató kulcskezelő rendszerében van.",
    provider: "Igen — a szolgáltató a saját kulcsával feloldhatja.",
    protects: "Ellopott adathordozó és egyes infrastruktúra-támadások ellen.",
    limit: "Nem jelent szolgáltató előli tartalmi titkosságot.",
    packet: "A raktárban zárva",
    keyAt: ["provider"],
    providerCanRead: true,
    storageCanRead: false,
  },
  userRest: {
    tab: "Tároláskor · felhasználói kulcs",
    title: "A raktár őrzi a dobozt, de nincs nála a kulcs",
    body: "Végponti vagy úgynevezett nulla tudású tárolásnál a fájl már a feltöltés előtt titkosítható. A szolgáltató a titkosított adatot őrzi, miközben a feloldó kulcs a felhasználónál marad.",
    keyOwner: "A feloldó kulcs a felhasználó készülékén vagy saját helyreállítási kulcsában van.",
    provider: "Nem — ha a megvalósítás valóban nem küldi el neki a kulcsot.",
    protects: "A tárolót és magát a szolgáltatót érő hozzáférés ellen is.",
    limit: "A végpont feltörése, a gyenge jelszó és a metaadatok ettől még kockázatot jelenthetnek.",
    packet: "A felhasználó zárja le",
    keyAt: ["sender"],
    providerCanRead: false,
    storageCanRead: false,
  },
  e2ee: {
    tab: "Végponttól végpontig · E2EE",
    title: "A küldő zárja le, és csak a címzett nyitja ki",
    body: "Végpontok közötti titkosításnál az üzenet a küldő készülékén válik olvashatatlanná, és a címzett készülékén válik újra olvashatóvá. A közvetítő szolgáltató továbbítja és tárolhatja a titkosított adatot, de nem kap tartalomfeloldó kulcsot.",
    keyOwner: "A tartalomkulcsok a beszélgetés résztvevőinek végpontjain vannak.",
    provider: "Nem — a helyesen megvalósított rendszerben nincs nála tartalomfeloldó kulcs.",
    protects: "Útközben, a szolgáltatónál és a tárolás során is védi a tartalmat.",
    limit: "A résztvevők készülékét, képernyőmentéseit és a kommunikáció metaadatait nem teszi láthatatlanná.",
    packet: "Végig zárva",
    keyAt: ["sender", "recipient"],
    providerCanRead: false,
    storageCanRead: false,
  },
};

class EncryptionLayers extends HTMLElement {
  connectedCallback() {
    this.active = this.active || "https";
    this.render();
  }

  render() {
    const item = encryptionModes[this.active];
    this.innerHTML = `
      <section class="encryption-shell" aria-labelledby="encryption-title">
        <div class="encryption-heading">
          <p class="chapter-number">Három külön zár · nem ugyanazt védik</p>
          <h3 id="encryption-title">Ki tudja kinyitni, és hol?</h3>
          <p>A „titkosított” szó önmagában kevés. Válassz egy megoldást: az ábra megmutatja, hol nyílik ki a tartalom, és kinél van a kulcs.</p>
        </div>
        <div class="encryption-tabs" role="tablist" aria-label="Titkosítási megoldások">
          ${Object.entries(encryptionModes).map(([key, mode]) => `<button type="button" role="tab" data-encryption="${key}" aria-selected="${key === this.active}" tabindex="${key === this.active ? 0 : -1}">${mode.tab}</button>`).join("")}
        </div>
        <div class="encryption-panel mode-${this.active}" role="tabpanel" tabindex="0">
          <div class="crypto-diagram" aria-hidden="true">
            <div class="crypto-flow">
              <div class="crypto-node crypto-sender">
                <span class="crypto-device"><i></i></span><b>Te</b>
                <em class="crypto-key-chip ${item.keyAt.includes("sender") ? "has-key" : "no-key"}"><i></i>Kulcs</em>
              </div>
              <div class="crypto-route"><span class="crypto-packet"><i></i><b>${item.packet}</b></span><i></i></div>
              <div class="crypto-middle">
                <div class="crypto-node crypto-service">
                  <span class="crypto-server"><i></i><i></i><i></i></span><b>Szolgáltató</b>
                  <em class="crypto-key-chip ${item.keyAt.includes("provider") ? "has-key" : "no-key"}"><i></i>Kulcs</em>
                  <strong class="crypto-access-state ${item.providerCanRead ? "is-readable" : "is-sealed"}">${item.providerCanRead ? "olvasható" : "zárva"}</strong>
                </div>
                <div class="crypto-node crypto-storage">
                  <span class="crypto-database"><i></i><i></i></span><b>Tárolás</b>
                  <strong class="crypto-access-state ${item.storageCanRead ? "is-readable" : "is-sealed"}">${item.storageCanRead ? "olvasható" : "zárva"}</strong>
                </div>
              </div>
              <div class="crypto-route crypto-route--second"><span class="crypto-packet"><i></i><b>${item.packet}</b></span><i></i></div>
              <div class="crypto-node crypto-recipient">
                <span class="crypto-device"><i></i></span><b>Címzett</b>
                <em class="crypto-key-chip ${item.keyAt.includes("recipient") ? "has-key" : "no-key"}"><i></i>Kulcs</em>
              </div>
            </div>
            <p class="crypto-diagram-note"><span class="is-key"></span>A kulcs birtokosa fel tudja oldani a tartalmat. <span class="is-sealed"></span>A zárt állapot önmagában nem mondja meg, kinél van a kulcs.</p>
          </div>
          <div class="encryption-copy">
            <p class="mini-label">${item.tab}</p>
            <h4>${item.title}</h4>
            <p>${item.body}</p>
            <dl>
              <div><dt>Kinél van a kulcs?</dt><dd>${item.keyOwner}</dd></div>
              <div><dt>Olvashatja a szolgáltató?</dt><dd>${item.provider}</dd></div>
              <div><dt>Mitől véd?</dt><dd>${item.protects}</dd></div>
              <div><dt>Mit nem old meg?</dt><dd>${item.limit}</dd></div>
            </dl>
          </div>
        </div>
      </section>`;
    this.querySelectorAll("[data-encryption]").forEach((button) => {
      button.addEventListener("click", () => { this.active = button.dataset.encryption; this.render(); });
      button.addEventListener("keydown", (event) => {
        const keys = Object.keys(encryptionModes);
        const index = keys.indexOf(this.active);
        let next = index;
        if (event.key === "ArrowLeft") next = (index - 1 + keys.length) % keys.length;
        if (event.key === "ArrowRight") next = (index + 1) % keys.length;
        if (next === index) return;
        event.preventDefault();
        this.active = keys[next];
        this.render();
        this.querySelector(`[data-encryption="${this.active}"]`)?.focus();
      });
    });
  }
}

const versions = {
  one: {
    short: "Ideiglenes kivétel",
    title: "Chat Control 1.0",
    status: "Lejárt · a visszaállítása még függőben",
    statusClass: "status-dot--off",
    posterClass: "",
    badge: "Önkéntes<br>lehetőség",
    intro:
      "A 2021/1232 rendelet átmenetileg kivett bizonyos üzenetküldő szolgáltatásokat az ePrivacy titkossági szabálya alól, hogy a szolgáltatók önként folytathassák a magánüzenetek tartalmának vizsgálatát gyermekbántalmazási anyagok és behálózás felismerésére.",
    facts: [
      ["1", "Nem a felhasználó önkéntes döntéséről volt szó. A <b>szolgáltató választhatta</b> a vizsgálatot olyan üzeneteknél, amelyek tartalmához technikailag hozzáfért."],
      ["2", "Ez a nem végpontok között titkosított magánüzenetek szövegének, képeinek és videóinak vizsgálatát is jelenthette — nem csupán nyilvános bejegyzésekét."],
      ["3", "Ismert és új anyag, valamint a gyermekek szexuális célú behálózására utaló teljes beszélgetési összefüggés is a hatályába kerülhetett. A szabály 2026. április 3-án <b>lejárt</b>."],
    ],
    why: "Miért aggályos? A levelezés attól még magánbeszélgetés, hogy nem E2EE védi. Az 1.0 éppen e szolgáltató által olvasható üzenetek széles vizsgálatához adott külön jogi teret; az „önkéntes” a szolgáltatóra, nem rád vonatkozott.",
  },
  two: {
    short: "Állandó rendeletterv",
    title: "Chat Control 2.0",
    status: "Trilógusban · nincs végleges megállapodás",
    statusClass: "status-dot--pending",
    posterClass: "is-two",
    badge: "Kötelező<br>keret",
    intro:
      "A Bizottság 2022-es javaslata állandó megelőzési, kockázatértékelési, felderítési, bejelentési és eltávolítási rendszert hozna létre. A Tanács és a Parlament sok ponton eltérő változatot támogat.",
    facts: [
      ["1", "Hatóság által kért <b>felderítési végzés</b> kötelezhetne szolgáltatót meghatározott tartalom keresésére."],
      ["2", "A legnagyobb vita az új tartalom és a behálózás felismerése, illetve a <b>titkosítás tényleges védelme</b> körül van."],
      ["3", "2026 júliusában még tárgyalják. <b>Nincs végleges szöveg</b>, ezért a pontos kimenetel nyitott."],
    ],
    why: "Miért fontos? Egy jogilag korlátozott célra épített technikai képesség később más keresési listával is működhet — ez a cél későbbi kiterjesztésének kockázata.",
  },
};

class VersionSwitcher extends ReactiveElement {
  stateKeys = ["version"];

  render() {
    const item = versions[state.version];
    this.innerHTML = `
      <div class="version-shell">
        <div class="version-tabs" role="tablist" aria-label="Chat Control változatok">
          <button class="version-tab" id="version-tab-one" role="tab" type="button" data-version="one" aria-controls="version-panel" aria-selected="${state.version === "one"}" tabindex="${state.version === "one" ? 0 : -1}">1.0 · ideiglenes</button>
          <button class="version-tab" id="version-tab-two" role="tab" type="button" data-version="two" aria-controls="version-panel" aria-selected="${state.version === "two"}" tabindex="${state.version === "two" ? 0 : -1}">2.0 · tervezett</button>
        </div>
        <div class="version-card" id="version-panel" role="tabpanel" aria-labelledby="version-tab-${state.version}" tabindex="0">
          <div class="version-poster ${item.posterClass}">
            <span class="version-poster__number">${state.version === "one" ? "1.0" : "2.0"}</span>
            <div class="version-poster__art" aria-hidden="true">
              <span class="poster-envelope"></span>
              <span class="poster-badge">${item.badge}</span>
            </div>
            <span class="version-status"><i class="status-dot ${item.statusClass}"></i>${item.status}</span>
          </div>
          <div class="version-panel">
            <p class="mini-label">${item.short}</p>
            <h3>${item.title}</h3>
            <p>${item.intro}</p>
            <div class="version-facts">
              ${item.facts
                .map(
                  ([number, text]) => `<div class="version-fact"><span>${number}</span><p>${text}</p></div>`,
                )
                .join("")}
            </div>
            <p class="version-why"><b>${item.why.split(" ").slice(0, 2).join(" ")}</b> ${item.why.split(" ").slice(2).join(" ")}</p>
          </div>
        </div>
      </div>`;

    this.querySelectorAll("[data-version]").forEach((button) => {
      button.addEventListener("click", () => (state.version = button.dataset.version));
      button.addEventListener("keydown", (event) => {
        if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return;
        event.preventDefault();
        state.version = state.version === "one" ? "two" : "one";
        requestAnimationFrame(() => this.querySelector(`[data-version="${state.version}"]`)?.focus());
      });
    });
  }
}

const labModes = {
  hash: {
    label: "Ismert kép másolata",
    kicker: "Digitális ujjlenyomat",
    title: "Mintha egy pontos körözési fotót hasonlítanánk össze",
    body:
      "Egy már szakértők által azonosított tiltott fájlból digitális lenyomat készül. A pontos kriptográfiai lenyomat csak azonos fájlt talál; az átalakításokat is felismerő perceptuális lenyomat hasonlósági küszöböt használ, ezért téves egyezése is lehet.",
    analogy: "A postás nem a levél jelentését találgatja: egy előre megadott pecsétmintát keres. Ha a hasonló pecséteket is elfogadja, már nem csak pontos egyezést talál.",
    art: `<div class="wanted-card"><div class="wanted-card__image">◎</div><b>Ismert lenyomat</b><div class="hash-lines"><span></span><span></span><span></span></div></div>`,
  },
  ai: {
    label: "Új kép becslése",
    kicker: "Valószínűségi modell",
    title: "Mintha a postásnak kellene megítélnie minden új fényképet",
    body:
      "Az új, korábban nem látott képnél a gép minták alapján valószínűséget becsül. Nem tudja biztosan, mit lát. Családi fotó, egészségügyi kép vagy műalkotás is téves jelzést kaphat.",
    analogy: "Itt nincs pontos körözési fotó. A gép azt mondja: „ez hasonlít valamire” — és néha téved.",
    art: `<div class="ai-card"><div class="ai-card__image">?</div><b>A gép becslése: 63%</b><div class="ai-meter"><span></span></div></div>`,
  },
  grooming: {
    label: "Beszélgetés értelmezése",
    kicker: "Nyelv és összefüggés",
    title: "Mintha valaki egy teljes levelezés szándékát próbálná megérteni",
    body:
      "A gyermekek szexuális célú behálózásának felismeréséhez a mondatok közti összefüggést, az életkort, a humort, a beceneveket és a manipuláció jeleit kellene értelmezni. Ugyanaz a mondat lehet ártatlan vagy veszélyes a helyzettől függően.",
    analogy: "Egyetlen szó nem elég. A rendszernek a beszélgetés előzményeit is vizsgálnia kell. Az előzmények nélkül nem dönthető el megbízhatóan.",
    art: `<div class="chat-stack"><span class="chat-bubble">Szia, hogy vagy ma?</span><span class="chat-bubble">Jól, köszi 🙂</span><span class="chat-bubble is-question">Ez ártatlan vagy manipuláció?</span><span class="chat-bubble">A környezet nélkül nem biztos.</span></div>`,
  },
};

class DetectionLab extends ReactiveElement {
  stateKeys = ["labMode"];

  connectedCallback() {
    this.falseRate = this.falseRate ?? 0.5;
    this.sensitivity = this.sensitivity ?? 90;
    this.prevalence = this.prevalence ?? 0.1;
    super.connectedCallback();
  }

  render() {
    const item = labModes[state.labMode];
    this.innerHTML = `
      <div class="lab-shell">
        <div class="lab-tabs" role="tablist" aria-label="Felismerési módok">
          ${Object.entries(labModes)
            .map(
              ([key, mode]) => `<button class="lab-tab" id="lab-tab-${key}" role="tab" type="button" data-lab="${key}" aria-controls="lab-panel" aria-selected="${state.labMode === key}" tabindex="${state.labMode === key ? 0 : -1}">${mode.label}</button>`,
            )
            .join("")}
        </div>
        <div class="lab-board" id="lab-panel" role="tabpanel" aria-labelledby="lab-tab-${state.labMode}" tabindex="0">
          <div class="lab-visual" aria-hidden="true">${item.art}</div>
          <div class="lab-copy">
            <p class="mini-label">${item.kicker}</p>
            <h3>${item.title}</h3>
            <p>${item.body}</p>
            <div class="lab-analogy"><span aria-hidden="true">✉</span><p><b>Postai hasonlat:</b> ${item.analogy}</p></div>
          </div>
        </div>
        <section class="base-rate" aria-labelledby="base-rate-title">
          <div class="base-rate__head">
            <div><p class="mini-label">Szemléltető alaparány-példa</p><h3 id="base-rate-title">A ritka találat matematikája</h3></div>
            <p><b>Feltételezés:</b> 10 000 üzenet kimenetét látod. Te állítod, valójában mennyi tiltott közöttük, ezekből mennyit talál meg a rendszer, és hány ártatlan üzenetet jelöl tévesen. Ezek szemléltető értékek, nem egy tervezett uniós rendszer mért teljesítménye.</p>
          </div>
          <p class="rate-explainer"><b>Három külön számról van szó.</b> Az alaparány azt mondja meg, mennyi a valóban tiltott üzenet. Az érzékenység ezek közül talál meg valamennyit. A tévespozitív-arány pedig csak az ártatlan üzenetekre vonatkozik. Mindhárom csúszka 0–100% között állítható.</p>
          <div class="base-rate__control-grid">
            <div class="base-rate__controls">
              <label for="prevalence"><span>Valódi alaparány: az üzenetek hány százaléka ténylegesen tiltott?</span><output data-prevalence-output>${this.formatRate(this.prevalence)}%</output></label>
              <input id="prevalence" type="range" min="0" max="100" step="0.1" value="${this.prevalence}" aria-describedby="rateNote" />
              <div class="rate-presets" aria-label="Valódi alaparány példaértékek">
                ${[0, 0.1, 1, 10, 50, 100].map((rate) => `<button type="button" data-prevalence="${rate}">${rate}%</button>`).join("")}
              </div>
            </div>
            <div class="base-rate__controls">
              <label for="sensitivity"><span>Érzékenység: a tiltott tartalmak hány százalékát találja meg?</span><output data-sensitivity-output>${this.sensitivity}%</output></label>
              <input id="sensitivity" type="range" min="0" max="100" step="1" value="${this.sensitivity}" aria-describedby="rateNote" />
              <div class="rate-presets" aria-label="Érzékenységi példaértékek">
                ${[0, 50, 70, 90, 100].map((rate) => `<button type="button" data-sensitivity="${rate}">${rate}%</button>`).join("")}
              </div>
            </div>
            <div class="base-rate__controls">
              <label for="falseRate"><span>Tévespozitív-arány: az ártatlan üzenetek hány százalékát jelölje meg?</span><output data-rate-output>${this.formatRate(this.falseRate)}%</output></label>
              <input id="falseRate" type="range" min="0" max="100" step="0.1" value="${this.falseRate}" aria-describedby="rateNote" />
              <div class="rate-presets" aria-label="Tévespozitív példaértékek">
                ${[0, 0.1, 0.5, 1, 10, 100].map((rate) => `<button type="button" data-rate="${rate}">${rate}%</button>`).join("")}
              </div>
            </div>
          </div>
          <div class="rate-visuals">
            <figure><canvas class="population-canvas" width="500" height="500" aria-label="Tízezer üzenet kimeneteinek pontábrája"></canvas><figcaption>10 000 üzenet · egy pont egy üzenet</figcaption></figure>
            <figure><canvas class="alert-canvas" width="500" height="250" aria-label="A riasztások kinagyított pontábrája"></canvas><figcaption data-alert-caption>A riasztások kinagyítva · egy pont egy riasztás</figcaption></figure>
          </div>
          <section class="rate-magnifier" aria-labelledby="rate-magnifier-title">
            <div><p class="mini-label">Láthatósági nagyítás</p><h4 id="rate-magnifier-title">A kevés találat se vesszen el a tízezer pont között</h4></div>
            <p>Legfeljebb 20 nagy jelölést rajzolunk ki kategóriánként. A mellettük álló szám mutatja a teljes, egész üzenetre kerekített darabszámot.</p>
            <div class="rare-count-grid" data-rare-counts></div>
          </section>
          <div class="rate-results" aria-live="polite">
            <div class="true-result"><b data-tp>9</b><span>valódi találat</span></div>
            <div class="missed-result"><b data-fn>1</b><span>elszalasztott tiltott tartalom</span></div>
            <div class="false-result"><b data-fp>50</b><span>téves riasztás</span></div>
            <div class="true-negative-result"><b data-tn>9 940</b><span>helyesen békén hagyott üzenet</span></div>
          </div>
          <p class="rate-rounding">A darabszámok várható értékek, egész üzenetre kerekítve.</p>
          <div class="rate-derived" aria-live="polite">
            <div><span>Beállított specificitás</span><b data-specificity>99,5%</b><small>100% mínusz a tévespozitív-arány</small></div>
            <div><span>Pozitív prediktív érték</span><b data-ppv>15,3%</b><small>A valódi találatok aránya az összes riasztás között</small></div>
          </div>
          <p class="rate-summary" id="rateNote" data-rate-summary></p>
          <div class="rate-legend" aria-label="Jelmagyarázat"><span class="is-tp">valódi találat</span><span class="is-fn">elszalasztott</span><span class="is-fp">téves riasztás</span><span class="is-tn">helyesen negatív</span></div>
        </section>
      </div>`;

    this.querySelectorAll("[data-lab]").forEach((button) => {
      button.addEventListener("click", () => (state.labMode = button.dataset.lab));
      button.addEventListener("keydown", (event) => {
        const keys = Object.keys(labModes);
        const current = keys.indexOf(state.labMode);
        let next = current;
        if (event.key === "ArrowLeft") next = (current - 1 + keys.length) % keys.length;
        if (event.key === "ArrowRight") next = (current + 1) % keys.length;
        if (next === current) return;
        event.preventDefault();
        state.labMode = keys[next];
        requestAnimationFrame(() => this.querySelector(`[data-lab="${state.labMode}"]`)?.focus());
      });
    });
    const slider = this.querySelector("#falseRate");
    const sensitivitySlider = this.querySelector("#sensitivity");
    const prevalenceSlider = this.querySelector("#prevalence");
    slider.addEventListener("input", () => {
      this.falseRate = Number(slider.value);
      this.updateMetrics();
    });
    sensitivitySlider.addEventListener("input", () => {
      this.sensitivity = Number(sensitivitySlider.value);
      this.updateMetrics();
    });
    prevalenceSlider.addEventListener("input", () => {
      this.prevalence = Number(prevalenceSlider.value);
      this.updateMetrics();
    });
    this.querySelectorAll("[data-rate]").forEach((button) => button.addEventListener("click", () => {
      this.falseRate = Number(button.dataset.rate);
      slider.value = String(this.falseRate);
      this.updateMetrics();
    }));
    this.querySelectorAll("[data-sensitivity]").forEach((button) => button.addEventListener("click", () => {
      this.sensitivity = Number(button.dataset.sensitivity);
      sensitivitySlider.value = String(this.sensitivity);
      this.updateMetrics();
    }));
    this.querySelectorAll("[data-prevalence]").forEach((button) => button.addEventListener("click", () => {
      this.prevalence = Number(button.dataset.prevalence);
      prevalenceSlider.value = String(this.prevalence);
      this.updateMetrics();
    }));
    this.updateMetrics();
  }

  formatRate(rate) {
    return rate < 0.1 ? rate.toFixed(2) : rate.toFixed(rate % 1 ? 1 : 0);
  }

  updateMetrics() {
    const total = 10000;
    const positives = Math.round(total * (this.prevalence / 100));
    const tp = Math.round(positives * (this.sensitivity / 100));
    const fn = positives - tp;
    const fp = Math.round((total - positives) * (this.falseRate / 100));
    const tn = total - positives - fp;
    const flagged = tp + fp;
    const falseShare = flagged ? (fp / flagged) * 100 : null;
    const positivePredictiveValue = flagged ? (tp / flagged) * 100 : null;
    const specificity = 100 - this.falseRate;
    const numberLocale = document.documentElement.lang || "hu";
    this.querySelector("[data-prevalence-output]").textContent = `${this.formatRate(this.prevalence)}%`;
    this.querySelector("[data-sensitivity-output]").textContent = `${this.sensitivity}%`;
    this.querySelector("[data-rate-output]").textContent = `${this.formatRate(this.falseRate)}%`;
    this.querySelector("[data-tp]").textContent = tp.toLocaleString(numberLocale);
    this.querySelector("[data-fn]").textContent = fn.toLocaleString(numberLocale);
    this.querySelector("[data-fp]").textContent = fp.toLocaleString(numberLocale);
    this.querySelector("[data-tn]").textContent = tn.toLocaleString(numberLocale);
    this.querySelector("[data-specificity]").textContent = `${specificity.toLocaleString(numberLocale, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`;
    this.querySelector("[data-ppv]").textContent = positivePredictiveValue === null
      ? "Nem értelmezhető"
      : `${positivePredictiveValue.toLocaleString(numberLocale, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`;
    this.querySelector("[data-rate-summary]").innerHTML = flagged
      ? `<b>${flagged.toLocaleString(numberLocale)} riasztásból ${fp.toLocaleString(numberLocale)} téves:</b> az ellenőrzendő jelzések ${falseShare.toLocaleString(numberLocale, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%-a ártatlan üzenetre mutatna. A pozitív prediktív érték ${positivePredictiveValue.toLocaleString(numberLocale, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%.`
      : "<b>Nincs riasztás ennél a beállításnál.</b> A pozitív prediktív érték nem értelmezhető, mert nincs pozitívnak jelölt üzenet.";
    this.querySelectorAll("[data-rate]").forEach((button) => button.classList.toggle("is-active", Number(button.dataset.rate) === this.falseRate));
    this.querySelectorAll("[data-sensitivity]").forEach((button) => button.classList.toggle("is-active", Number(button.dataset.sensitivity) === this.sensitivity));
    this.querySelectorAll("[data-prevalence]").forEach((button) => button.classList.toggle("is-active", Number(button.dataset.prevalence) === this.prevalence));
    this.drawPopulation(tp, fn, fp, positives);
    this.drawAlerts(tp, fp);
    this.drawRareCounts({ tp, fn, fp, tn });
  }

  drawPopulation(tp, fn, fp, positives) {
    const canvas = this.querySelector(".population-canvas");
    const ctx = canvas.getContext("2d");
    const size = 5;
    const colors = { tn: "#657878", fp: "#ff7764", tp: "#62d1bc", fn: "#efb54a" };
    ctx.fillStyle = "#243c3d";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    for (let slot = 0; slot < 10000; slot += 1) this.drawCell(ctx, slot, size, colors.tn);
    const positiveSlots = Array.from({ length: positives }, (_, index) => Math.floor((index * 10000) / Math.max(1, positives)));
    const positiveSet = new Set(positiveSlots);
    positiveSlots.forEach((slot, index) => {
      const category = index < tp ? "tp" : "fn";
      const categoryCount = category === "tp" ? tp : fn;
      this.drawCell(ctx, slot, size, colors[category], categoryCount > 0 && categoryCount <= 20);
    });
    let painted = 0;
    let cursor = 137;
    while (painted < fp) {
      const slot = cursor % 10000;
      cursor += 7919;
      if (positiveSet.has(slot)) continue;
      this.drawCell(ctx, slot, size, colors.fp, fp > 0 && fp <= 20);
      painted += 1;
    }
  }

  drawCell(ctx, slot, size, color, highlight = false) {
    const x = (slot % 100) * size;
    const y = Math.floor(slot / 100) * size;
    ctx.fillStyle = color;
    ctx.fillRect(x + 0.6, y + 0.6, size - 1.2, size - 1.2);
    if (!highlight) return;
    ctx.strokeStyle = "#fffdf8";
    ctx.lineWidth = 1.4;
    ctx.strokeRect(x + 0.7, y + 0.7, size - 1.4, size - 1.4);
  }

  drawAlerts(tp, fp) {
    const canvas = this.querySelector(".alert-canvas");
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#243c3d";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    const total = tp + fp;
    const shown = Math.min(total, 1000);
    const shownTrue = total ? Math.round(shown * (tp / total)) : 0;
    const columns = 50;
    const size = 9;
    for (let i = 0; i < shown; i += 1) {
      ctx.fillStyle = i < shownTrue ? "#62d1bc" : "#ff7764";
      const x = 18 + (i % columns) * size;
      const y = 18 + Math.floor(i / columns) * size;
      ctx.beginPath();
      ctx.arc(x, y, Math.max(1.5, size * 0.34), 0, Math.PI * 2);
      ctx.fill();
    }
    const caption = total === 0
      ? "Nincs riasztás a beállított példában"
      : total > 1000
        ? `Az összes ${total.toLocaleString(document.documentElement.lang || "hu")} riasztás arányait mutató 1 000 pontos minta`
        : `A riasztások kinagyítva · ${total.toLocaleString(document.documentElement.lang || "hu")} pont, egy pont egy riasztás`;
    this.querySelector("[data-alert-caption]").textContent = caption;
    canvas.setAttribute("aria-label", caption);
  }

  drawRareCounts(counts) {
    const numberLocale = document.documentElement.lang || "hu";
    const categories = [
      ["tp", "Valódi találat"],
      ["fn", "Elszalasztott tiltott tartalom"],
      ["fp", "Téves riasztás"],
      ["tn", "Helyesen békén hagyott"],
    ];
    this.querySelector("[data-rare-counts]").innerHTML = categories.map(([key, label]) => {
      const count = counts[key];
      const shown = Math.min(count, 20);
      const dots = count === 0
        ? '<i class="rare-dot is-empty"></i>'
        : Array.from({ length: shown }, () => '<i class="rare-dot"></i>').join("");
      const more = count > shown ? '<i class="rare-more">+</i>' : "";
      return `<article class="rare-count rare-count--${key}" aria-label="${label}: ${count.toLocaleString(numberLocale)}">
        <div class="rare-dots" aria-hidden="true">${dots}${more}</div>
        <b>${count.toLocaleString(numberLocale)}</b><span>${label}</span>
      </article>`;
    }).join("");
  }
}

const rooms = {
  doctor: {
    icon: "⚕",
    gear: "✚",
    tab: "Orvos",
    role: "Páciens és orvos",
    kicker: "Egészségügyi titok",
    title: "Amikor egy intim tünetről kérdezel",
    message: "Küldök egy fotót a kiütésről. Nagyon aggódom — lehet ez valami komoly?",
    why: "A téves képfelismerés érzékeny egészségügyi fotót emelhet ki. Már az emberi felülvizsgálattól való félelem is visszatarthat a segítségkéréstől.",
  },
  lawyer: {
    icon: "§",
    gear: "§",
    tab: "Ügyvéd",
    role: "Ügyfél és ügyvéd",
    kicker: "Bizalmas jogi tanács",
    title: "Amikor csak őszintén lehet jól védekezni",
    message: "Leírom pontosan, mi történt. Kérlek, ezt egyelőre senki mással ne oszd meg.",
    why: "Az ügyvédi titok a tisztességes eljárást védi. Egy általános vizsgálati rendszer megváltoztatja, mennyire mer valaki teljesen őszinte lenni.",
  },
  journalist: {
    icon: "✎",
    gear: "PRESS",
    tab: "Újságíró",
    role: "Forrás és újságíró",
    kicker: "Forrásvédelem",
    title: "Amikor egy visszaélés bizonyítékát küldöd",
    message: "A dokumentum bizonyítja a csalást. Ha kiderül, hogy én küldtem, elveszítem az állásomat.",
    why: "A források sokszor csak erős titkosítás mellett beszélnek. A készüléken futó ellenőrző képesség önmagában is új támadási célpont lehet.",
  },
  teen: {
    icon: "☺",
    gear: "♫",
    tab: "Tinédzser",
    role: "Fiatal és segítő",
    kicker: "Biztonságos segítségkérés",
    title: "Amikor egy fiatal bizalmasan kér segítséget",
    message: "Valaki nyomást gyakorol rám az interneten. Még nem merem elmondani otthon. Mit tegyek?",
    why: "A gyermekvédelem célja éppen a segítség. Ha a fiatal attól tart, hogy gép vagy idegen is olvashatja, lehet, hogy nem ír a segítőnek.",
  },
  partner: {
    icon: "♥",
    gear: "♥",
    tab: "Pár",
    role: "Két felnőtt",
    kicker: "Intim magánélet",
    title: "Amikor a közelség csak rátok tartozik",
    message: "Hiányzol. Ezt a képet csak neked küldöm — kérlek, maradjon köztünk.",
    why: "Felnőttek jogszerű intim kommunikációja hasonlíthat a keresett mintákhoz. A téves riasztás különösen megalázó és nehezen visszafordítható.",
  },
  organizer: {
    icon: "✊",
    gear: "!",
    tab: "Szervező",
    role: "Tüntetésszervezők",
    kicker: "Politikai szerveződés",
    title: "Amikor egy békés tüntetés útvonalát egyeztetitek",
    message: "A találkozási pontot csak a csoportban osszuk meg. Kérlek, a résztvevők nevét ne továbbítsd.",
    why: "A politikai szerveződés résztvevőinek feltérképezése elrettenthet a jogszerű részvételtől. Egy később más célra átállított ellenőrzési képesség különösen veszélyes lehet rájuk.",
  },
  whistleblower: {
    icon: "⚑",
    gear: "AKTA",
    tab: "Bejelentő",
    role: "Közérdekű bejelentő",
    kicker: "Biztonságos bizonyítékátadás",
    title: "Amikor belső iratokkal bizonyítasz egy visszaélést",
    message: "A mellékletből látszik, ki rendelte el. Az azonosságomat addig se fedd fel, amíg nincs biztonságos eljárás.",
    why: "A bejelentő személyazonosságának vagy kapcsolatainak kiszivárgása megtorláshoz vezethet. Az öncenzúra közvetlen társadalmi kár: bizonyítékok maradhatnak rejtve.",
  },
};

class PrivacyRoom extends ReactiveElement {
  stateKeys = ["room"];

  render() {
    const item = rooms[state.room];
    this.innerHTML = `
      <div class="room-shell">
        <div class="room-tabs" role="tablist" aria-label="Bizalmas élethelyzetek">
          ${Object.entries(rooms)
            .map(
              ([key, room]) => `<button class="room-tab" id="room-tab-${key}" role="tab" type="button" data-room="${key}" aria-controls="room-panel" aria-selected="${state.room === key}" tabindex="${state.room === key ? 0 : -1}"><span aria-hidden="true">${room.icon}</span>${room.tab}</button>`,
            )
            .join("")}
        </div>
        <div class="room-card" id="room-panel" role="tabpanel" aria-labelledby="room-tab-${state.room}" tabindex="0">
          <div class="room-visual" aria-hidden="true">
            <span class="privacy-signal privacy-signal--one">titkosítva</span>
            <span class="privacy-signal privacy-signal--two">csak nektek</span>
            <span class="scan-beam"></span>
            <div class="person-figure person-figure--${state.room}">
              <span class="person-head"><i class="person-hair"></i></span><span class="person-body"><i class="person-outfit"></i></span>
              <span class="person-gear">${item.gear}</span>
              <span class="person-phone">${item.icon}</span><span class="person-role">${item.role}</span>
            </div>
          </div>
          <div class="room-copy">
            <p class="mini-label">${item.kicker}</p>
            <h3>${item.title}</h3>
            <p class="message-example">${item.message}</p>
            <div class="room-why"><span aria-hidden="true">!</span><p><b>Miért számít?</b> ${item.why}</p></div>
          </div>
        </div>
      </div>`;

    this.querySelectorAll("[data-room]").forEach((button) => {
      button.addEventListener("click", () => (state.room = button.dataset.room));
      button.addEventListener("keydown", (event) => {
        const keys = Object.keys(rooms);
        const current = keys.indexOf(state.room);
        let next = current;
        if (event.key === "ArrowLeft") next = (current - 1 + keys.length) % keys.length;
        if (event.key === "ArrowRight") next = (current + 1) % keys.length;
        if (next === current) return;
        event.preventDefault();
        state.room = keys[next];
        requestAnimationFrame(() => this.querySelector(`[data-room="${state.room}"]`)?.focus());
      });
    });
  }
}

const surveillanceModes = {
  targeted: {
    tab: "Célzott vizsgálat",
    kicker: "Előbb a konkrét gyanú, utána az adatgyűjtés",
    title: "Egy körülhatárolt személy vagy fiók kerül a vizsgálatba",
    summary: "A hatóság egy megnevezett célpontra, meghatározott adatkörre és időtartamra kér engedélyt. A vizsgálat elvben a kijelölt célpontra és az engedélyben meghatározott körre korlátozódik; mások adatai csak e körön belül kerülhetnek bele.",
    who: "Egy előre azonosított célpont és az engedélyben meghatározott kör.",
    suspicion: "A vizsgálat előtt kell konkrét, ellenőrizhető indok.",
    system: "Csak az engedélyben meghatározott adatokat és időszakot; a felhasználás célja is kötött.",
    later: "Az engedély lejárta, az adatok törlése, a naplózás és a jogorvoslat korlátozhatja a további felhasználást.",
  },
  mass: {
    tab: "Általános átvizsgálás",
    kicker: "Előbb mindenki a szűrőben, utána jön a kiválasztás",
    title: "A teljes vagy nagyon széles felhasználói kör kommunikációját gép vizsgálja",
    summary: "Nem kell embernek kézzel elolvasnia minden üzenetet. Már az is széles körű vizsgálat, ha minden üzenet tartalmából vagy jellemzőiből ellenőrzési adat készül, minden fájlt összevetnek egy keresőlistával, vagy minden beszélgetést gép osztályoz, és a rendszer csak ezután emel ki embereket.",
    who: "Minden érintett, függetlenül attól, áll-e vele szemben egyedi gyanú; a kiválasztás csak a feldolgozás után történik.",
    suspicion: "Az adatfeldolgozás már azelőtt megkezdődhet, hogy az érintettel szemben konkrét gyanú merülne fel.",
    system: "A beállítástól függően tartalmat, lenyomatot, találati adatot vagy metaadatot.",
    later: "A keresési lista, a küszöb vagy a cél későbbi módosítása új embereket tehet láthatóvá.",
  },
};

class SurveillanceContrast extends HTMLElement {
  connectedCallback() {
    this.active = this.active || "targeted";
    this.render();
  }

  render() {
    const item = surveillanceModes[this.active];
    const people = Array.from({ length: 30 }, (_, index) => {
      const isTarget = index === 12;
      const isFlagged = this.active === "mass" && [4, 12, 25].includes(index);
      return `<span class="surveillance-person ${isTarget ? "is-target" : ""} ${isFlagged ? "is-flagged" : ""}" aria-hidden="true"><i></i></span>`;
    }).join("");
    this.innerHTML = `
      <section class="surveillance-shell" aria-labelledby="surveillance-title">
        <div class="surveillance-tabs" role="tablist" aria-label="A megfigyelés hatókörének összehasonlítása">
          ${Object.entries(surveillanceModes).map(([key, mode]) => `<button type="button" id="surveillance-tab-${key}" role="tab" data-surveillance="${key}" aria-controls="surveillance-panel" aria-selected="${key === this.active}" tabindex="${key === this.active ? 0 : -1}">${mode.tab}</button>`).join("")}
        </div>
        <div class="surveillance-panel" id="surveillance-panel" role="tabpanel" aria-labelledby="surveillance-tab-${this.active}" tabindex="0">
          <div class="surveillance-visual surveillance-visual--${this.active}" aria-label="${this.active === "targeted" ? "Harminc emberből egy előre kijelölt célpont kerül a vizsgálatba" : "Mind a harminc ember kommunikációja átmegy a szűrőn, amely hármat megjelöl"}">
            <div class="surveillance-people">${people}</div>
            <div class="surveillance-pipeline" aria-hidden="true"><span>${this.active === "targeted" ? "Célpontra szóló engedély" : "Mindenki átvizsgálása"}</span><i></i><b>${this.active === "targeted" ? "1 kijelölt célpont" : "3 gépi jelzés"}</b></div>
            <p>${this.active === "targeted" ? "A rendszer nem vizsgálja át automatikusan mind a harminc ember teljes kommunikációját." : "A rendszer mind a 30 ember adatait feldolgozta, mielőtt hármat megjelölt."}</p>
          </div>
          <div class="surveillance-copy">
            <p class="mini-label">${item.kicker}</p>
            <h3 id="surveillance-title">${item.title}</h3>
            <p class="surveillance-summary">${item.summary}</p>
            <dl class="surveillance-facts">
              <div><dt>Ki kerül be?</dt><dd>${item.who}</dd></div>
              <div><dt>Mikor van gyanú?</dt><dd>${item.suspicion}</dd></div>
              <div><dt>Mit lát a rendszer?</dt><dd>${item.system}</dd></div>
              <div><dt>Mi történhet később?</dt><dd>${item.later}</dd></div>
            </dl>
          </div>
        </div>
        <div class="metadata-note">
          <span aria-hidden="true">◎</span>
          <p><b>A metaadat sem „csak technikai adat”.</b> A címzett, időpont, hely, gyakoriság és csoporttagság a szöveg elolvasása nélkül is utalhat arra, hogy ki kivel dolgozik, ki járhat orvoshoz, szervezhet tüntetést vagy kérhet segítséget. A tartalom és a metaadat más, de mindkettő lehet érzékeny.</p>
        </div>
        <p class="surveillance-caveat"><b>Pontos megfogalmazás:</b> nem minden automatizált ellenőrzést minősít minden bíróság vagy jogszabály ugyanúgy „tömeges megfigyelésnek”. A technikai hatókört ezért külön mutatjuk meg: kinek az adatait dolgozza fel a rendszer még az egyedi gyanú felmerülése előtt.</p>
        <div class="surveillance-consequences">
          <article><span>01</span><h4>A gépi ellenőrzés is ellenőrzés</h4><p>A hozzáférés és a visszaélés kockázata akkor is fennáll, ha először algoritmus elemzi a tartalmat. Téves jelzésnél a privát tartalom emberi ellenőrhöz kerülhet.</p></article>
          <article><span>02</span><h4>Visszatartó hatás</h4><p>Ha nem tudhatod, mikor emelnek ki egy beszélgetést, jogszerű, érzékeny kérdésekről is hallgathatsz. Ez újságírókat és forrásaikat, ügyvédeket és ügyfeleiket, orvosokat és betegeiket, aktivistákat és családokat is érinthet.</p></article>
          <article><span>03</span><h4>Célkiterjesztés</h4><p>A szűk célra kiépített rendszer később más tartalmak keresésére, további jogsértések felderítésére vagy új hatóságok használatára is átállítható. Ezért számít a technikai korlát, nem csak a mai ígéret.</p></article>
          <article><span>04</span><h4>A jó célhoz is kellenek korlátok</h4><p>Fontos közérdekű cél mellett is vizsgálni kell a szükségességet, az arányosságot, a független engedélyezést és felügyeletet, a törlést, az auditot és a jogorvoslatot.</p></article>
        </div>
        <div class="surveillance-sources" aria-label="A tömeges megfigyelés magyarázatának elsődleges forrásai">
          <a href="https://infocuria.curia.europa.eu/tabs/redirect/juris/liste.jsf?language=hu&num=C-511/18" target="_blank" rel="noreferrer">Európai Unió Bírósága · általános és különbségtétel nélküli adatmegőrzés <span aria-hidden="true">↗</span></a>
          <a href="https://hudoc.echr.coe.int/eng?i=001-210077" target="_blank" rel="noreferrer">EJEB · célzott és tömeges lehallgatás garanciái <span aria-hidden="true">↗</span></a>
          <a href="https://www.coe.int/en/web/portal/-/council-of-europe-alerts-governments-on-risks-of-digital-tracking-and-surveillance" target="_blank" rel="noreferrer">Európa Tanács · túl széles megfigyelés és öncenzúra <span aria-hidden="true">↗</span></a>
        </div>
      </section>`;

    this.querySelectorAll("[data-surveillance]").forEach((button) => {
      button.addEventListener("click", () => {
        this.active = button.dataset.surveillance;
        this.render();
      });
      button.addEventListener("keydown", (event) => {
        if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return;
        event.preventDefault();
        this.active = this.active === "targeted" ? "mass" : "targeted";
        this.render();
        requestAnimationFrame(() => this.querySelector(`[data-surveillance="${this.active}"]`)?.focus());
      });
    });
  }
}

const abuseScenarios = [
  {
    key: "scope",
    tab: "Célkiterjesztés",
    icon: "↗",
    fact: "A tartalom-ellenőrző rendszernek valamilyen keresési szabályt vagy listát kell kapnia.",
    path: "Ha a lista frissítésének nincs erős, ellenőrizhető korlátja, egy későbbi döntéshozó más képet, dokumentumot vagy politikai jelképet is felvehet rá.",
    guard: "Szigorú célhoz kötöttség, nyilvános jogalap és kriptográfiailag ellenőrizhető listafrissítés.",
  },
  {
    key: "false-match",
    tab: "Hamis találat",
    icon: "≠",
    fact: "A hasonlóságot kereső perceptuális lenyomat és a gépi osztályozás tévesen is jelezhet.",
    path: "Egy manipulált vagy véletlen egyezés politikailag kényes ügyet indíthat el, miközben az eredeti tartalom ártatlan.",
    guard: "Automatikus jelzés alapján önmagában ne indulhasson intézkedés; legyen független emberi ellenőrzés és gyors jogorvoslat.",
  },
  {
    key: "selective",
    tab: "Szelektív eljárás",
    icon: "⌁",
    fact: "A gépi jelzést szolgáltatói, hatósági és ügyészi döntések láncolata követheti.",
    path: "A lánc egyes szereplői azonos jelzések közül szelektíven emelhetnek ki ellenzéki, kisebbségi vagy civil szereplőket.",
    guard: "Független bírói engedély, manipulációt jelző napló, rendszeres külső audit és összehasonlítható átláthatósági adatok.",
  },
  {
    key: "source",
    tab: "Forrásvédelem",
    icon: "✎",
    fact: "Az újságírói forrás és a közérdekű bejelentő gyakran csak bizalmas csatornán ad át bizonyítékot.",
    path: "Már az ellenőrzés lehetősége is öncenzúrát okozhat; egy megszerzett kapcsolati háló pedig felfedheti a forrást.",
    guard: "Szakmai titkok kifejezett védelme, végpontok közötti titkosítás kizárása a vizsgálatból és célzott eljárás.",
  },
  {
    key: "intimate",
    tab: "Lejáratás",
    icon: "!",
    fact: "Az ellenőrzés intim képekhez, egészségügyi adatokhoz és magánbeszélgetésekhez férhet hozzá.",
    path: "Kiszivárogtatott vagy kiragadott magánadat alkalmas lehet egy politikus, aktivista vagy tisztviselő lejáratására.",
    guard: "Adatminimalizálás, rövid törlési határidő, szigorú hozzáférés-kezelés, büntethető naplótörlés és értesítési kötelezettség.",
  },
  {
    key: "identity",
    tab: "Életkor és azonosítás",
    icon: "18",
    fact: "Az életkor ellenőrzése egyes megoldásoknál személyazonosító vagy biometrikus adatot kapcsolhat a fiókhoz.",
    path: "Ha az életkori igazolás tartós személyazonosság-térképpé válik, a névtelen politikai részvétel és segítségkérés is sérülhet.",
    guard: "Adatvédő életkor-igazolás, amely csak a korhatár teljesülését bizonyítja, de nem fedi fel és nem tárolja a személyazonosságot.",
  },
];

class AbuseSimulator extends HTMLElement {
  connectedCallback() {
    this.active = this.active || abuseScenarios[0].key;
    this.render();
  }

  render() {
    const item = abuseScenarios.find((scenario) => scenario.key === this.active);
    this.innerHTML = `
      <div class="abuse-shell">
        <div class="abuse-tabs" role="tablist" aria-label="Politikai visszaélési útvonalak">
          ${abuseScenarios.map((scenario) => `<button type="button" role="tab" data-abuse="${scenario.key}" aria-selected="${scenario.key === this.active}" tabindex="${scenario.key === this.active ? 0 : -1}"><span aria-hidden="true">${scenario.icon}</span>${scenario.tab}</button>`).join("")}
        </div>
        <div class="abuse-path" role="tabpanel" tabindex="0">
          <article><span>1 · Ami ma tény</span><p>${item.fact}</p></article>
          <i aria-hidden="true">→</i>
          <article class="abuse-path__risk"><span>2 · A visszaélési út · következtetés</span><p>${item.path}</p></article>
          <i aria-hidden="true">→</i>
          <article class="abuse-path__guard"><span>3 · Mi védene?</span><p>${item.guard}</p></article>
        </div>
        <p class="abuse-principle"><b>A demokratikus garanciákat nemcsak a jelenlegi döntéshozók jó szándékára, hanem a későbbi rosszhiszemű használatra is méretezni kell.</b> Nemcsak azt kell kérdezni, mire szánják ma a rendszert, hanem azt is, mire lesz képes holnap.</p>
      </div>`;
    this.querySelectorAll("[data-abuse]").forEach((button) => {
      button.addEventListener("click", () => {
        this.active = button.dataset.abuse;
        this.render();
      });
      button.addEventListener("keydown", (event) => {
        const index = abuseScenarios.findIndex((scenario) => scenario.key === this.active);
        let next = index;
        if (event.key === "ArrowLeft") next = (index - 1 + abuseScenarios.length) % abuseScenarios.length;
        if (event.key === "ArrowRight") next = (index + 1) % abuseScenarios.length;
        if (next === index) return;
        event.preventDefault();
        this.active = abuseScenarios[next].key;
        this.render();
        this.querySelector(`[data-abuse="${this.active}"]`)?.focus();
      });
    });
  }
}

const abuseHistoryCases = [
  {
    key: "hungary-pegasus", type: "political", place: "Magyarország", year: "2021–2023", title: "Pegasus újságírók, ügyvédek és politikai szereplők telefonján", evidence: "Parlamenti és hatósági vizsgálat",
    proven: "Az Európai Parlament PEGA-jelentése szerint több mint 300 magyar telefonszám kerülhetett célkeresztbe, köztük oknyomozó újságíróké, ügyvédeké, aktivistáké és egy ellenzéki politikusé. A NAIH megerősítette, hogy több megnevezett személlyel szemben engedélyköteles titkos információgyűjtés folyt.",
    disputed: "A NAIH a megvizsgált ügyekben nem állapított meg jogellenességet; a kiválasztás jogszerűségének és politikai céljának megítélése vitatott.",
    lesson: "A formális engedély önmagában nem oldja meg a politikai célkiválasztás kérdését. Független felügyelet, utólagos értesítés és valódi jogorvoslat is kell.",
    sources: [["Európai Parlament PEGA-jelentés · magyarul", "https://www.europarl.europa.eu/doceo/document/A-9-2023-0189_HU.html"], ["NAIH-jelentés · magyarul", "https://www.naih.hu/adatvedelmi-jelentesek/file/486-jelentes-a-nemzeti-adatvedelmi-es-informaciosszabadsag-hatosag-hivatalbol-inditott-vizsgalatanak-megallapitasai-a-pegasus-kemszoftver-magyarorszagon-torteno-alkalmazasaval-osszuefueggesben"]],
  },
  {
    key: "hungary-reliability", type: "state", place: "Magyarország", year: "2026", title: "A megbízhatósági vizsgálat túl széles megfigyelési kerete", evidence: "Jogerős EJEB-ítélet",
    proven: "Az Emberi Jogok Európai Bírósága egyhangúlag megállapította a magánélethez való jog megsértését. A korrupcióellenes rendszert előzetes gyanú nélkül terjesztették ki orvosokra és más állami dolgozókra, megfelelő értesítés és hatékony független jogorvoslat nélkül.",
    disputed: "Az ítélet nem állította, hogy minden felperest ténylegesen megfigyeltek; magát a kellő garanciák nélküli jogi keretet minősítette jogsértőnek.",
    lesson: "A cél és az érintetti kör későbbi kiterjesztése nem pusztán elméleti veszély. A korlátokat a jogszabályban és a technikai rendszerben is rögzíteni kell.",
    sources: [["EJEB: Szelényi és mások kontra Magyarország · angolul", "https://hudoc.echr.coe.int/eng?i=001-248199"], ["Közérthető összefoglaló · magyarul", "https://telex.hu/belfold/2026/02/03/strasbourg-torveny-itelet-megfigyeles-allamigazgatasban-dolgozok"]],
  },
  {
    key: "poland-pegasus", type: "political", place: "Lengyelország", year: "2019–2024", title: "Pegasus az ellenzéki választási kampány vezetőjének telefonján", evidence: "Szenátusi és ügyészi vizsgálat",
    proven: "Krzysztof Brejza, az ellenzéki Polgári Koalíció 2019-es kampányvezetője telefonján ismételten használták a Pegasust. Az Európai Parlament rögzítette a lengyel szenátusi vizsgálat politikai célú megfigyelésre vonatkozó megállapítását; az ügyészség külön nyomozást indított.",
    disputed: "Az egyedi büntetőjogi felelősség és a teljes döntési lánc vizsgálata nem minden ponton zárult le.",
    lesson: "A megfigyelés választási stratégiát, kapcsolati hálót és kampánykommunikációt is feltárhat — így nem csak az egyén magánéletére hat.",
    sources: [["Európai Parlament állásfoglalása · angolul", "https://www.europarl.europa.eu/doceo/document/TA-9-2023-0440_EN.html"], ["Lengyel ügyészség · lengyelül", "https://www.gov.pl/web/prokuratura-krajowa/informacja-o-sledztwie-dotyczacym-oprogramowania-pegasus"]],
  },
  {
    key: "greece-predator", type: "political", place: "Görögország", year: "2022–2023", title: "Ellenzéki pártvezető és újságíró megfigyelése", evidence: "Kormányzati beismerés és parlamenti vizsgálat",
    proven: "A görög kormány elismerte, hogy a hírszerzés megfigyelte Nikos Androulakis ellenzéki pártvezetőt és Thanasis Koukakis pénzügyi újságírót. A miniszterelnök Androulakis megfigyelését jogszerűnek, de politikailag elfogadhatatlannak nevezte.",
    disputed: "A kormány tagadta a Predator megvásárlását vagy használatát; a kémprogramos támadások pontos megrendelője nem tisztázott.",
    lesson: "A jogszerűség, a politikai elfogadhatóság és az elszámoltathatóság külön kérdés. Ellenőrizhetőnek kell lennie, ki, milyen indokkal és meddig jelölt ki célpontot.",
    sources: [["Európai Parlament PEGA-jelentés, 137–142. pont · magyarul", "https://www.europarl.europa.eu/doceo/document/A-9-2023-0189_HU.html"]],
  },
  {
    key: "catalangate", type: "political", place: "Spanyolország", year: "2017–2022", title: "CatalanGate: a célpontok kapcsolatai is bekerültek a körbe", evidence: "Technikai és parlamenti vizsgálat",
    proven: "A Citizen Lab legalább 65, a katalán függetlenségi mozgalomhoz kötődő célpontot azonosított: politikusok mellett ügyvédeket, civileket, családtagokat és munkatársakat is. A spanyol hatóságok 18 személy bírósági engedéllyel történt megfigyelését ismerték el.",
    disputed: "A többi feltárt fertőzés elrendelője nem tisztázott, ezért ezek nem tulajdoníthatók biztosan a spanyol államnak.",
    lesson: "A kapcsolati adatok miatt a megfigyelés túlléphet az elsődleges célponton, és forrásokat, ügyvédeket, családtagokat is érinthet.",
    sources: [["Európai Parlament PEGA-jelentés, 304–306. pont · magyarul", "https://www.europarl.europa.eu/doceo/document/A-9-2023-0189_HU.html"]],
  },
  {
    key: "dutch-algorithm", type: "state", place: "Hollandia", year: "2013–2024", title: "Semlegesnek látszó algoritmus, diszkriminatív otthoni ellenőrzések", evidence: "Adatvédelmi hatósági megállapítás",
    proven: "A holland oktatási végrehajtó szerv életkor, képzéstípus és lakcím-távolság alapján jelölt diákokat csalásellenőrzésre. Az adatvédelmi hatóság szerint a kritériumoknak nem volt megfelelő objektív alapjuk, és közvetetten gyakrabban érintettek nem európai migrációs hátterű diákokat.",
    disputed: "A megállapítás nem azt jelenti, hogy minden egyes ellenőrzés diszkriminatív eredményű volt; a kiválasztási rendszer megalapozottságát és hatását bírálta.",
    lesson: "A névleg semleges jelzők más tulajdonságok helyettesítőivé válhatnak. Csoportonkénti hibamérés és véletlen kontrollminta szükséges.",
    sources: [["Holland adatvédelmi hatóság · angolul", "https://www.autoriteitpersoonsgegevens.nl/en/node/5189"]],
  },
  {
    key: "xinjiang-ijop", type: "state", place: "Kína · Hszincsiang", year: "2017–2022", title: "Hétköznapi viselkedésből „gyanús személy”", evidence: "Technikai vizsgálat és ENSZ-értékelés",
    proven: "A Human Rights Watch visszafejtette az IJOP rendőrségi alkalmazást: kapcsolati, telefon-, jármű- és lakcímadatokat egyesített, majd hétköznapi eltérések alapján jelölt ki embereket vizsgálatra. Az ENSZ a tágabb rendszerhez súlyos, diszkriminatív emberi jogi visszaéléseket kapcsolt.",
    disputed: "Az eset egészen más politikai és jogi környezetben történt, ezért nem közvetlen európai párhuzam, hanem a képességek összekapcsolásának szélsőséges példája.",
    lesson: "Az adatforrások összekapcsolása minőségileg új hatalmat hoz létre. A profilépítést és a kapcsolati következtetést külön is korlátozni kell.",
    sources: [["Human Rights Watch technikai jelentés · angolul", "https://www.hrw.org/report/2019/05/01/chinas-algorithms-repression/reverse-engineering-xinjiang-police-mass"], ["ENSZ emberi jogi értékelés · angolul", "https://www.ohchr.org/sites/default/files/documents/countries/2022-08-31/22-08-31-final-assesment.pdf"]],
  },
  {
    key: "twitter-insider", type: "corporate", place: "Egyesült Államok · Szaúd-Arábia", year: "2014–2022", title: "Egy Twitter-alkalmazott kormánykritikusok adatait adta át", evidence: "Jogerős büntetőítélet",
    proven: "Ahmad Abouammo volt Twitter-alkalmazott kenőpénzért nem nyilvános fiókadatokhoz fért hozzá, majd szaúdi kormánykritikusok azonosítására alkalmas adatokat adott át szaúdi tisztviselőknek. 42 hónap szabadságvesztésre ítélték.",
    disputed: "Az ítélet egy bennfentes konkrét cselekményeiről szólt, nem arról, hogy a teljes vállalat részt vett volna az adatátadásban.",
    lesson: "Jogosan létrehozott adatbázissal is visszaélhet privilegizált bennfentes. Szűk hozzáférés, kettős jóváhagyás és manipulálhatatlan napló kell.",
    sources: [["Amerikai Igazságügyi Minisztérium · angolul", "https://www.justice.gov/usao-ndca/pr/former-twitter-employee-sentenced-42-months-federal-prison-acting-foreign-agent"]],
  },
  {
    key: "rite-aid", type: "corporate", place: "Egyesült Államok", year: "2012–2023", title: "A hamis arcfelismerési találatból rendőri intézkedés lett", evidence: "FTC-panasz és egyezségi végzés",
    proven: "Az FTC szerint a Rite Aid nem mérte megfelelően arcfelismerő rendszere pontosságát, és nem követte a hamis találatokat. Téves egyezések után ártatlan vásárlókat követtek, átkutattak, kiküldtek vagy rendőrt hívtak rájuk; a kár aránytalanul érintett fekete és ázsiai közösségeket.",
    disputed: "A megfogalmazásnál fontos az „FTC szerint” minősítés: az ismertetett tényállás hatósági panasz és egyezség része.",
    lesson: "A téves pozitív nem puszta statisztikai hiba: egy szervezeti folyamatban megalázás, nyomozás vagy kényszerintézkedés lehet belőle.",
    sources: [["Federal Trade Commission · angolul", "https://search.ftc.gov/news-events/news/press-releases/2023/12/rite-aid-banned-using-ai-facial-recognition-after-ftc-says-retailer-deployed-technology-without"]],
  },
];

class AbuseHistory extends HTMLElement {
  connectedCallback() {
    this.filter = this.filter || "all";
    this.render();
  }

  render() {
    const types = { all: "Mind a 9 eset", state: "Állami rendszer", political: "Politikai célpont", corporate: "Vállalati hozzáférés" };
    const cases = abuseHistoryCases.filter((item) => this.filter === "all" || item.type === this.filter);
    this.innerHTML = `
      <div class="history-shell">
        <div class="history-filters" role="group" aria-label="Esetek szűrése">${Object.entries(types).map(([key, label]) => `<button type="button" data-history-filter="${key}" aria-pressed="${this.filter === key}">${label}</button>`).join("")}</div>
        <div class="history-grid">
          ${cases.map((item, index) => `<details class="history-case" ${index === 0 ? "open" : ""}>
            <summary><span><i>${item.place} · ${item.year}</i><b>${item.title}</b></span><em>${item.evidence}</em><strong aria-hidden="true">+</strong></summary>
            <div class="history-case__body">
              <section><h4>Mi bizonyított?</h4><p>${item.proven}</p></section>
              <section><h4>Mi vitatott vagy korlátozott?</h4><p>${item.disputed}</p></section>
              <section class="history-lesson"><h4>Mi a tanulság?</h4><p>${item.lesson}</p></section>
              <div class="history-sources">${item.sources.map(([label, url]) => `<a href="${url}" target="_blank" rel="noreferrer">${label} ↗</a>`).join("")}</div>
            </div>
          </details>`).join("")}
        </div>
      </div>`;
    this.querySelectorAll("[data-history-filter]").forEach((button) => button.addEventListener("click", () => {
      this.filter = button.dataset.historyFilter;
      this.render();
    }));
  }
}

const escapeHTML = (value) => String(value ?? "").replace(/[&<>'"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[character]);

class VoteExplorer extends HTMLElement {
  connectedCallback() {
    this.voteKey = this.voteKey || "2026-july-rejection";
    this.view = this.view || "members";
    this.position = this.position || "ALL";
    this.group = this.group || "ALL";
    this.search = this.search || "";
    this.hungarianOnly = this.hungarianOnly || false;
    this.limit = this.limit || 48;
    this.render();
  }

  render() {
    const votes = window.CHAT_CONTROL_VOTES || [];
    if (!votes.length) {
      this.innerHTML = `<p class="vote-data-error">A név szerinti szavazati adatok nem töltődtek be.</p>`;
      return;
    }
    const vote = votes.find((item) => item.key === this.voteKey) || votes[votes.length - 1];
    this.voteKey = vote.key;
    const numberLocale = document.documentElement.lang || "hu";
    const groups = [...new Set(vote.members.map((member) => member.group))].sort((a, b) => a.localeCompare(b, numberLocale));
    const total = Object.values(vote.totals).reduce((sum, value) => sum + value, 0);
    const positions = ["FOR", "AGAINST", "ABSTENTION", "DID_NOT_VOTE"];
    const filtered = vote.members.filter((member) => {
      const nameMatch = member.name.toLocaleLowerCase(numberLocale).includes(this.search.toLocaleLowerCase(numberLocale));
      return nameMatch && (this.position === "ALL" || member.position === this.position) && (this.group === "ALL" || member.group === this.group) && (!this.hungarianOnly || member.country === "HU");
    });
    this.innerHTML = `
      <section class="vote-explorer-shell" aria-labelledby="vote-explorer-title">
        <div class="vote-explorer-heading"><div><p class="mini-label">Név szerinti szavazatok</p><h3 id="vote-explorer-title">Ki hogyan szavazott?</h3></div><p>Válassz egy döntést. A feliratok minden esetben megmutatják, mit jelentett az igen és a nem.</p></div>
        <div class="vote-picker" role="tablist" aria-label="Szavazás kiválasztása">
          ${votes.map((item) => `<button type="button" role="tab" data-vote-key="${item.key}" aria-selected="${item.key === vote.key}"><span>${item.short_date}</span><b>${item.title}</b><small>${item.totals.FOR} · ${item.totals.AGAINST} · ${item.totals.ABSTENTION}</small></button>`).join("")}
        </div>
        <div class="vote-detail-card">
          <div class="vote-detail-head"><div><span>${vote.body}</span><h4>${vote.question}</h4><p>${vote.meaning}</p></div><strong>${vote.result_label}</strong></div>
          <div class="vote-stack" aria-label="Szavazatok megoszlása">
            ${positions.map((position) => `<span class="position-${position.toLowerCase().replaceAll("_", "-")}" style="width:${(vote.totals[position] / total) * 100}%"><i>${vote.totals[position]}</i></span>`).join("")}
          </div>
          <div class="vote-total-cards">
            ${positions.map((position) => `<div class="position-${position.toLowerCase().replaceAll("_", "-")}"><b>${vote.totals[position]}</b><span>${vote.position_labels[position]}</span></div>`).join("")}
          </div>
        </div>
        <div class="vote-view-switch" role="group" aria-label="Adatok nézete"><button type="button" data-vote-view="members" aria-pressed="${this.view === "members"}">Képviselők</button><button type="button" data-vote-view="groups" aria-pressed="${this.view === "groups"}">Frakciók</button></div>
        ${this.view === "members" ? `
          <div class="vote-filters">
            <label><span>Keresés név szerint</span><input type="search" data-member-search value="${escapeHTML(this.search)}" placeholder="Például: Cseh Katalin" /></label>
            <label><span>Álláspont</span><select data-position-filter><option value="ALL">Mindegyik</option>${positions.map((position) => `<option value="${position}" ${this.position === position ? "selected" : ""}>${vote.position_labels[position]}</option>`).join("")}</select></label>
            <label><span>Frakció</span><select data-group-filter><option value="ALL">Mindegyik</option>${groups.map((group) => `<option value="${escapeHTML(group)}" ${this.group === group ? "selected" : ""}>${escapeHTML(group)}</option>`).join("")}</select></label>
            <button type="button" class="hungarian-filter" data-hungarian-filter aria-pressed="${this.hungarianOnly}">HU · magyar képviselők</button>
          </div>
          <p class="filter-count" role="status">${filtered.length.toLocaleString(numberLocale)} képviselő felel meg a szűrésnek.</p>
          <div class="member-grid">
            ${filtered.slice(0, this.limit).map((member) => `<article><span class="member-position position-${member.position.toLowerCase().replaceAll("_", "-")}">${vote.position_labels[member.position]}</span><h5>${escapeHTML(member.name)}</h5><p>${member.country ? `<b>${member.country}</b> · ` : ""}${escapeHTML(member.group)}</p></article>`).join("") || `<p class="empty-members">Nincs ilyen találat. Próbálj másik szűrést.</p>`}
          </div>
          ${filtered.length > this.limit ? `<button class="small-button vote-more" type="button" data-vote-more>További ${Math.min(48, filtered.length - this.limit)} képviselő</button>` : ""}
        ` : `
          <div class="group-grid">
            ${vote.group_stats.map((item) => `<article><h5>${escapeHTML(item.group)}</h5><p>${escapeHTML(item.label)}</p><div>${positions.map((position) => `<span class="position-${position.toLowerCase().replaceAll("_", "-")}"><b>${item.stats[position] || 0}</b><small>${position === "FOR" ? "igen" : position === "AGAINST" ? "nem" : position === "ABSTENTION" ? "tart." : "nem szav."}</small></span>`).join("")}</div></article>`).join("")}
          </div>
        `}
        <div class="vote-sources"><span>Adatforrás:</span><a href="${vote.official_source}" target="_blank" rel="noreferrer">hivatalos név szerinti jegyzőkönyv ↗</a><a href="${vote.explore_source}" target="_blank" rel="noreferrer">HowTheyVote-adatnézet ↗</a><small>A HowTheyVote az Európai Parlament nyílt adatait dolgozza fel (ODbL). A 2023-as LIBE-szavazatokat a bizottsági jegyzőkönyvből vettük át.</small></div>
      </section>`;
    this.bindEvents();
  }

  bindEvents() {
    this.querySelectorAll("[data-vote-key]").forEach((button) => button.addEventListener("click", () => {
      this.voteKey = button.dataset.voteKey;
      this.position = "ALL";
      this.group = "ALL";
      this.search = "";
      this.hungarianOnly = false;
      this.limit = 48;
      this.render();
    }));
    this.querySelectorAll("[data-vote-view]").forEach((button) => button.addEventListener("click", () => {
      this.view = button.dataset.voteView;
      this.render();
    }));
    this.querySelector("[data-member-search]")?.addEventListener("input", (event) => {
      this.search = event.target.value;
      this.limit = 48;
      this.render();
      const input = this.querySelector("[data-member-search]");
      input?.focus();
      input?.setSelectionRange(this.search.length, this.search.length);
    });
    this.querySelector("[data-position-filter]")?.addEventListener("change", (event) => { this.position = event.target.value; this.limit = 48; this.render(); });
    this.querySelector("[data-group-filter]")?.addEventListener("change", (event) => { this.group = event.target.value; this.limit = 48; this.render(); });
    this.querySelector("[data-hungarian-filter]")?.addEventListener("click", () => { this.hungarianOnly = !this.hungarianOnly; this.limit = 48; this.render(); });
    this.querySelector("[data-vote-more]")?.addEventListener("click", () => { this.limit += 48; this.render(); });
  }
}

class VoteSimulator extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `
      <div class="vote-board">
        <div class="vote-head">
          <h3>Vajon 314 szavazat elég a Tanács szövegének elutasításához?</h3>
          <span class="vote-date">2026. július 9.</span>
        </div>
        <div class="vote-track-wrap">
          <div class="vote-labels"><span>0 elutasító szavazat</span><span>küszöb: 360</span></div>
          <div class="vote-track" aria-label="314 elutasító szavazat a szükséges 360-ból">
            <span class="vote-fill" data-vote-fill>0</span>
            <span class="vote-threshold" data-vote-threshold aria-hidden="true"></span>
          </div>
          <div class="vote-goal-marker">360 kellett volna ↑</div>
        </div>
        <div class="vote-equation" aria-label="314 plusz 46 egyenlő 360">
          <div class="vote-number"><b>314</b><span>az elutasításért</span></div>
          <span class="vote-symbol">+</span>
          <div class="vote-number missing"><b>46</b><span>még hiányzott</span></div>
          <span class="vote-symbol">=</span>
          <div class="vote-number"><b>360</b><span>abszolút többség</span></div>
        </div>
        <div class="vote-explainer" data-vote-explainer>
          <b>Ezért az elutasítási indítvány nem kapta meg a szükséges többséget.</b> Nem az számított, hogy a 314 több-e, mint a 276. A Parlament 719 hivatalban lévő képviselőjének több mint fele kellett: legalább 360. A Parlament ezután módosította a szöveget; a Tanácsnak még döntenie kell róla.
        </div>
        <div class="vote-action"><button class="small-button primary" type="button" data-run-vote>Számoljuk meg a 314-et</button></div>
      </div>`;

    const button = this.querySelector("[data-run-vote]");
    button.addEventListener("click", () => {
      const fill = this.querySelector("[data-vote-fill]");
      fill.classList.add("is-run");
      this.querySelector("[data-vote-threshold]").classList.add("is-run");
      this.querySelector("[data-vote-explainer]").classList.add("is-visible");
      button.textContent = "314 / 360 — 46 hiányzott";
      button.disabled = true;
      let display = 0;
      const reduced = document.documentElement.dataset.reduceMotion === "true" || matchMedia("(prefers-reduced-motion: reduce)").matches;
      if (reduced) {
        fill.textContent = "314";
        return;
      }
      const started = performance.now();
      const count = (now) => {
        const progress = Math.min(1, (now - started) / 1200);
        display = Math.round(314 * (1 - Math.pow(1 - progress, 3)));
        fill.textContent = display;
        if (progress < 1) requestAnimationFrame(count);
      };
      requestAnimationFrame(count);
    });
  }
}

const safeguards = [
  {
    id: "warrant",
    short: "Célzott végzés",
    title: "Egyedi, bíró által ellenőrzött célzás",
    body: "A vizsgálat csak konkrét személyre, fiókra, időre és súlyos bűncselekményre szólhat; nem indulhat minden felhasználón automatikusan.",
    icon: "§",
  },
  {
    id: "purpose",
    short: "Célhoz kötés",
    title: "Szűk, ellenőrizhető keresési cél",
    body: "A keresőlistát, a jogalapot és minden későbbi bővítést naplózni, indokolni és függetlenül ellenőrizni kell.",
    icon: "◎",
  },
  {
    id: "e2ee",
    short: "E2EE-védelem",
    title: "A végpontok közötti titkosítás tényleges védelme",
    body: "A szolgáltató nem kaphat tartalomkulcsot, és nem kötelezhető a lezárás előtti általános készülékoldali vizsgálatra sem.",
    icon: "⌾",
  },
  {
    id: "audit",
    short: "Független audit",
    title: "Nyilvános mérés és külső technikai ellenőrzés",
    body: "A téves pozitív és téves negatív arányokat valós környezetben, csoportonként is mérni kell; az auditáló nem függhet a rendszer szállítójától.",
    icon: "⌕",
  },
  {
    id: "human",
    short: "Emberi kontroll",
    title: "Nincs automatikus szankció egy gépi jelzésből",
    body: "Képzett felülvizsgáló, dokumentált döntési szabály és arányos eljárás kell; egy modell pontszáma önmagában nem lehet letiltás vagy feljelentés alapja.",
    icon: "◉",
  },
  {
    id: "remedy",
    short: "Jogorvoslat",
    title: "Értesítés, törlés és megtámadható döntés",
    body: "Az érintettnek — ha a nyomozás ezt már nem veszélyezteti — tudnia kell a vizsgálatról, kijavíttathatja a hibát, és független fórumhoz fordulhat.",
    icon: "↺",
  },
];

class SafeguardBuilder extends HTMLElement {
  connectedCallback() {
    this.selected = this.selected || new Set();
    this.render();
  }

  getStatus() {
    const count = this.selected.size;
    if (count === 0) return {
      label: "Nincs bekapcsolt korlát",
      body: "A széles ellenőrzési képesség érdemi jogi és technikai ellensúly nélkül maradna.",
    };
    if (count <= 2) return {
      label: "Egy-egy garancia önmagában kevés",
      body: "Egy jó szabály nem pótolja a hiányzó technikai védelmet, auditot vagy jogorvoslatot.",
    };
    if (count < safeguards.length) return {
      label: "Erősebb csomag, nyitott résekkel",
      body: "A kiválasztott korlátok csökkentik a kockázatot, de a kihagyott pont továbbra is valódi visszaélési vagy tévedési út lehet.",
    };
    return {
      label: "Teljesebb ellenőrzési lánc — nem automatikus jóváhagyás",
      body: "A hat garanciát a pontos jogszövegben, a műszaki megvalósításban és a gyakorlatban is bizonyítani és folyamatosan érvényesíteni kell.",
    };
  }

  render() {
    const status = this.getStatus();
    this.innerHTML = `
      <section class="safeguard-shell" aria-labelledby="safeguard-title">
        <div class="safeguard-heading">
          <p class="chapter-number">Interaktív garanciateszt</p>
          <h3 id="safeguard-title">Építs korlátokat a megfigyelési képesség köré</h3>
          <p>Kapcsold be a garanciákat. Az ábra nem azt állítja, hogy egy darabszám „biztonságossá” tesz egy rendszert: azt mutatja, hogy a védelem egymásra épülő jogi, műszaki és eljárási rétegekből áll.</p>
        </div>
        <div class="safeguard-workbench">
          <div class="safeguard-visual">
            <div class="safeguard-radar ${this.selected.size === safeguards.length ? "is-complete" : ""}" aria-hidden="true">
              <span class="radar-ring radar-ring--one"></span><span class="radar-ring radar-ring--two"></span>
              <span class="safeguard-core"><i>✉</i><b>${this.selected.size}/${safeguards.length}</b></span>
              ${safeguards.map((item, index) => `<span class="safeguard-orbit safeguard-orbit--${index + 1} ${this.selected.has(item.id) ? "is-on" : ""}"><i>${item.icon}</i></span>`).join("")}
            </div>
            <div class="safeguard-status" role="status" aria-live="polite"><b>${status.label}</b><span>${status.body}</span></div>
          </div>
          <div class="safeguard-options">
            ${safeguards.map((item) => `
              <button type="button" class="safeguard-option ${this.selected.has(item.id) ? "is-on" : ""}" data-safeguard="${item.id}" aria-pressed="${this.selected.has(item.id)}">
                <span class="safeguard-check" aria-hidden="true">${this.selected.has(item.id) ? "✓" : "+"}</span>
                <span><b>${item.short}</b><strong>${item.title}</strong><small>${item.body}</small></span>
              </button>`).join("")}
          </div>
        </div>
      </section>`;
    this.querySelectorAll("[data-safeguard]").forEach((button) => button.addEventListener("click", () => {
      const id = button.dataset.safeguard;
      if (this.selected.has(id)) this.selected.delete(id);
      else this.selected.add(id);
      this.render();
      requestAnimationFrame(() => this.querySelector(`[data-safeguard="${id}"]`)?.focus());
    }));
  }
}

class MythQuiz extends HTMLElement {
  connectedCallback() {
    this.startNewSet();
  }

  randomInt(max) {
    if (max <= 1) return 0;
    if (globalThis.crypto?.getRandomValues) {
      const values = new Uint32Array(1);
      crypto.getRandomValues(values);
      return values[0] % max;
    }
    return Math.floor(Math.random() * max);
  }

  shuffle(values) {
    const result = [...values];
    for (let index = result.length - 1; index > 0; index -= 1) {
      const other = this.randomInt(index + 1);
      [result[index], result[other]] = [result[other], result[index]];
    }
    return result;
  }

  storageGet(key, fallback) {
    try {
      const value = JSON.parse(sessionStorage.getItem(key));
      return value ?? fallback;
    } catch {
      return fallback;
    }
  }

  storageSet(key, value) {
    try { sessionStorage.setItem(key, JSON.stringify(value)); } catch { /* Private storage can be unavailable. */ }
  }

  pickFromBag(category, answer, questions) {
    const key = `chat-control-quiz-bag:${category}:${answer}`;
    let bag = this.storageGet(key, []);
    if (!bag.length) bag = this.shuffle(questions.filter((question) => question.category === category && question.answer === answer).map((question) => question.id));
    const id = bag.pop();
    this.storageSet(key, bag);
    return questions.find((question) => question.id === id);
  }

  hasLongStreak(questions) {
    return questions.some((question, index) => index >= 2 && question.answer === questions[index - 1].answer && question.answer === questions[index - 2].answer);
  }

  makeQuestionSet() {
    const questions = window.CHAT_CONTROL_QUIZ || [];
    const categories = [...new Set(questions.map((question) => question.category))];
    if (questions.length < 100 || categories.length !== 10) return [];
    const masks = this.storageGet("chat-control-quiz-truth-masks", []);
    let trueCategories;
    let mask;
    for (let attempt = 0; attempt < 30; attempt += 1) {
      trueCategories = new Set(this.shuffle(categories).slice(0, 5));
      mask = categories.map((category) => trueCategories.has(category) ? "1" : "0").join("");
      if (!masks.includes(mask)) break;
    }
    const nextMasks = [...masks, mask].slice(-40);
    this.storageSet("chat-control-quiz-truth-masks", nextMasks);
    const selected = categories.map((category) => this.pickFromBag(category, trueCategories.has(category), questions));
    let ordered = selected;
    for (let attempt = 0; attempt < 50; attempt += 1) {
      ordered = this.shuffle(selected);
      if (!this.hasLongStreak(ordered)) break;
    }
    return ordered;
  }

  startNewSet() {
    this.questions = this.makeQuestionSet();
    this.index = 0;
    this.score = 0;
    this.answered = false;
    this.render();
  }

  markSeen(question) {
    const seen = new Set(this.storageGet("chat-control-quiz-seen", []));
    seen.add(question.id);
    this.storageSet("chat-control-quiz-seen", [...seen]);
    return seen.size;
  }

  seenCount() {
    return this.storageGet("chat-control-quiz-seen", []).length;
  }

  render() {
    if (!this.questions?.length) {
      this.innerHTML = `<div class="quiz-shell"><div class="quiz-card"><h3>A kvízadatok nem töltődtek be.</h3><p>Frissítsd az oldalt, vagy olvasd tovább a forrásokat.</p></div></div>`;
      return;
    }
    if (this.index >= this.questions.length) {
      this.innerHTML = `
        <div class="quiz-shell">
          <div class="quiz-heading"><span>A minikvíz véget ért</span><h3>A pontos érv a meggyőző érv</h3></div>
          <div class="quiz-card quiz-score" role="status" tabindex="-1">
            <strong>${this.score}/${this.questions.length}</strong>
            <h3>${this.score === this.questions.length ? "Minden válaszod helyes." : "Most már látod, mely részletekre érdemes figyelni."}</h3>
            <p>A legerősebb állampolgári érv egyszerre védi a gyermekeket, a bizonyítékokat és a magánkommunikáció biztonságát.</p>
            <p class="quiz-seen">Ebben a böngészési munkamenetben a 100 kérdésből <b>${this.seenCount()}</b> különbözőt láttál.</p>
            <button class="small-button primary quiz-next" type="button" data-new-quiz>Új 10 kérdés</button>
          </div>
        </div>`;
      this.querySelector("[data-new-quiz]").addEventListener("click", () => this.startNewSet());
      return;
    }

    const question = this.questions[this.index];
    this.innerHTML = `
      <div class="quiz-shell">
        <div class="quiz-heading"><span>${question.categoryLabel} · ${this.index + 1}/${this.questions.length}</span><h3>Tény vagy tévhit?</h3><p>100 ellenőrzött állításból minden körben 10 kiegyensúlyozott kérdés.</p></div>
        <div class="quiz-progress" aria-hidden="true"><span style="width:${((this.index + 1) / this.questions.length) * 100}%"></span></div>
        <div class="quiz-card" tabindex="-1">
          <h3>${question.statement}</h3>
          <div class="quiz-actions">
            <button class="quiz-choice" type="button" data-answer="true">Igaz</button>
            <button class="quiz-choice" type="button" data-answer="false">Nem igaz</button>
          </div>
          <div class="quiz-feedback" data-quiz-feedback role="status" aria-live="polite"></div>
          <button class="small-button primary quiz-next" type="button" data-next-question hidden>${this.index === this.questions.length - 1 ? "Eredmény" : "Következő állítás"} →</button>
        </div>
      </div>`;

    this.querySelectorAll("[data-answer]").forEach((button) => {
      button.addEventListener("click", () => {
        if (this.answered) return;
        this.answered = true;
        const chosen = button.dataset.answer === "true";
        const correct = chosen === question.answer;
        if (correct) this.score += 1;
        const feedback = this.querySelector("[data-quiz-feedback]");
        feedback.className = `quiz-feedback is-visible ${correct ? "is-right" : "is-wrong"}`;
        feedback.innerHTML = `<b>${correct ? "Pontosan." : "Nem egészen."}</b> ${question.detail}`;
        this.querySelectorAll("[data-answer]").forEach((choice) => {
          choice.disabled = true;
          if ((choice.dataset.answer === "true") === question.answer) choice.setAttribute("aria-label", `${choice.textContent}, ez a helyes válasz`);
        });
        this.markSeen(question);
        this.querySelector("[data-next-question]").hidden = false;
      });
    });

    this.querySelector("[data-next-question]").addEventListener("click", () => {
      this.index += 1;
      this.answered = false;
      this.render();
      this.querySelector(".quiz-card")?.focus({ preventScroll: true });
    });
  }
}

customElements.define("mail-story", MailStory);
customElements.define("encryption-layers", EncryptionLayers);
customElements.define("version-switcher", VersionSwitcher);
customElements.define("detection-lab", DetectionLab);
customElements.define("privacy-room", PrivacyRoom);
customElements.define("surveillance-contrast", SurveillanceContrast);
customElements.define("abuse-simulator", AbuseSimulator);
customElements.define("abuse-history", AbuseHistory);
customElements.define("vote-simulator", VoteSimulator);
customElements.define("vote-explorer", VoteExplorer);
customElements.define("safeguard-builder", SafeguardBuilder);
customElements.define("myth-quiz", MythQuiz);

const connectionCards = [...document.querySelectorAll("[data-connection-card]")];
const connectionCount = document.querySelector("[data-connection-count]");
document.querySelectorAll("[data-connection-filter]").forEach((button) => {
  button.addEventListener("click", () => {
    const active = button.dataset.connectionFilter;
    document.querySelectorAll("[data-connection-filter]").forEach((filter) => {
      filter.setAttribute("aria-pressed", String(filter === button));
    });
    let visible = 0;
    connectionCards.forEach((card) => {
      const matches = active === "all" || card.dataset.tags.split(" ").includes(active);
      card.hidden = !matches;
      if (matches) visible += 1;
    });
    if (connectionCount) connectionCount.textContent = String(visible);
  });
});

document.querySelectorAll("[data-flip-card]").forEach((card) => {
  card.querySelectorAll("[data-flip]").forEach((button) => button.addEventListener("click", () => {
    const flipped = !card.classList.contains("is-flipped");
    card.classList.toggle("is-flipped", flipped);
    const front = card.querySelector(".institution-card__front");
    const back = card.querySelector(".institution-card__back");
    front.toggleAttribute("inert", flipped);
    back.toggleAttribute("inert", !flipped);
    front.setAttribute("aria-hidden", String(flipped));
    back.setAttribute("aria-hidden", String(!flipped));
    card.querySelector(".institution-card__front [data-flip]")?.setAttribute("aria-expanded", String(flipped));
    requestAnimationFrame(() => (flipped ? back : front).querySelector("[data-flip]")?.focus());
  }));
});

const mobileMenu = document.querySelector("#mobileNav");
const menuButton = document.querySelector("#menuButton");
menuButton?.addEventListener("click", () => {
  const open = menuButton.getAttribute("aria-expanded") === "true";
  menuButton.setAttribute("aria-expanded", String(!open));
  mobileMenu.hidden = open;
  document.body.classList.toggle("menu-open", !open);
  menuButton.querySelector(".sr-only").textContent = open ? "Menü megnyitása" : "Menü bezárása";
});
mobileMenu?.querySelectorAll("a").forEach((link) =>
  link.addEventListener("click", () => {
    menuButton.setAttribute("aria-expanded", "false");
    mobileMenu.hidden = true;
    document.body.classList.remove("menu-open");
  }),
);

const motionToggle = document.querySelector("#motionToggle");
const updateMotionToggle = (reduced) => {
  if (!motionToggle) return;
  motionToggle.setAttribute("aria-pressed", String(reduced));
  motionToggle.querySelector(".motion-icon").textContent = reduced ? "▶" : "Ⅱ";
  motionToggle.querySelector(".button-label").textContent = reduced ? "Animáció indítása" : "Animáció leállítása";
  motionToggle.title = reduced ? "A mozgó ábrák újraindítása" : "A mozgó ábrák leállítása";
};
motionToggle?.addEventListener("click", () => {
  const reduced = document.documentElement.dataset.reduceMotion === "true";
  const nextReduced = !reduced;
  document.documentElement.dataset.reduceMotion = String(nextReduced);
  updateMotionToggle(nextReduced);
  localStorage.setItem("reduce-motion", String(nextReduced));
});

if (localStorage.getItem("reduce-motion") === "true") {
  document.documentElement.dataset.reduceMotion = "true";
  updateMotionToggle(true);
} else {
  updateMotionToggle(false);
}

const revealObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("is-visible");
      revealObserver.unobserve(entry.target);
    });
  },
  { threshold: 0.08, rootMargin: "0px 0px -5%" },
);
document.querySelectorAll(".reveal").forEach((element) => revealObserver.observe(element));

const progress = document.querySelector("#readingProgress");
const updateProgress = () => {
  const scrollable = document.documentElement.scrollHeight - window.innerHeight;
  const value = scrollable > 0 ? Math.min(100, Math.max(0, (window.scrollY / scrollable) * 100)) : 0;
  progress.style.width = `${value}%`;
};
updateProgress();
window.addEventListener("scroll", updateProgress, { passive: true });
window.addEventListener("resize", updateProgress);

const statusDialog = document.querySelector("#statusDialog");
const letterDialog = document.querySelector("#letterDialog");
const openDialog = (dialog) => {
  if (typeof dialog.showModal === "function") dialog.showModal();
  else dialog.setAttribute("open", "");
};
document.querySelectorAll("[data-open-status]").forEach((button) => button.addEventListener("click", () => openDialog(statusDialog)));
document.querySelectorAll("[data-open-letter]").forEach((button) => button.addEventListener("click", () => openDialog(letterDialog)));

[statusDialog, letterDialog].forEach((dialog) => {
  dialog?.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });
});

const toast = document.querySelector("#toast");
const t = (value) => window.ChatControlI18n?.t(value) || value;
let toastTimer;
const showToast = (message) => {
  clearTimeout(toastTimer);
  toast.textContent = message;
  toast.classList.add("is-visible");
  toastTimer = setTimeout(() => toast.classList.remove("is-visible"), 2800);
};

const copyText = async (text, success) => {
  try {
    await navigator.clipboard.writeText(text);
    showToast(success);
  } catch {
    const helper = document.createElement("textarea");
    helper.value = text;
    helper.setAttribute("readonly", "");
    helper.style.position = "fixed";
    helper.style.opacity = "0";
    document.body.append(helper);
    helper.select();
    const copied = document.execCommand("copy");
    helper.remove();
    showToast(copied ? success : t("A másolás nem sikerült — jelöld ki kézzel a szöveget."));
  }
};

const shortSummary = t(
  "A Chat Control mögött valós gyermekvédelmi cél áll, de a készülékeken vagy szolgáltatóknál végzett általános üzenetvizsgálat téves riasztásokkal, a titkosítás gyengítésével és a cél későbbi kiterjesztésének kockázatával járhat. 2026. július 14-én az 1.0 lejárt, visszaállítása még függőben van; a 2.0 továbbra is tárgyalás alatt áll. Célzott, bírói engedélyhez kötött és függetlenül auditált megoldást kérek, a végpontok közötti titkosítás egyértelmű védelmével.",
);

document.querySelector("[data-copy-summary]")?.addEventListener("click", () =>
  copyText(shortSummary, t("A rövid összefoglaló a vágólapra került.")),
);
document.querySelector("[data-copy-letter]")?.addEventListener("click", () =>
  copyText(document.querySelector("#letterTemplate").value, t("A levélminta a vágólapra került.")),
);
document.querySelector("[data-share]")?.addEventListener("click", async () => {
  const shareData = {
    title: document.title,
    text: t("Mit jelent valójában a Chat Control? Közérthető, interaktív útmutató."),
    url: location.href,
  };
  if (navigator.share) {
    try {
      await navigator.share(shareData);
    } catch (error) {
      if (error.name !== "AbortError") showToast(t("A megosztás most nem sikerült."));
    }
  } else {
    copyText(location.href, t("Az oldal címe a vágólapra került."));
  }
});
