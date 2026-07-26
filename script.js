const CATEGORY_META = {
  "Gastronomia & Delivery": {
    label: "Gastronomia",
    kicker: "Restaurantes, pizzarias, delivery",
    tone: "gold",
    img: "photo-1517248135467-4c7edcad34c4"
  },
  "Cafes, Padarias & Doces": {
    label: "Cafés & Doces",
    kicker: "Padarias, bolos, açaí, chocolates",
    tone: "cream",
    img: "photo-1442512595331-e89e73853f31"
  },
  "Mercados, Emporios & Conveniencia": {
    label: "Mercados & Conveniência",
    kicker: "Empórios, hortifruti, suplementos",
    tone: "green",
    img: "photo-1542838132-92c53300491e"
  },
  "Saude & Clinicas": {
    label: "Saúde & Clínicas",
    kicker: "Clínicas, óticas, nutrição, terapias",
    tone: "blue",
    img: "photo-1576091160550-2173dba999ef"
  },
  "Beleza & Estetica": {
    label: "Beleza & Estética",
    kicker: "Salões, estética, spa, barbearias",
    tone: "rose",
    img: "photo-1522337360788-8b13dee7a37e"
  },
  "Academias, Esportes & Bem-Estar": {
    label: "Esportes & Bem-Estar",
    kicker: "Academias, pilates, yoga, artes marciais",
    tone: "lime",
    img: "photo-1534438327276-14e5300c3a48"
  },
  "Moda, Calcados & Acessorios": {
    label: "Moda & Acessórios",
    kicker: "Roupas, calçados, bolsas, semijoias",
    tone: "violet",
    img: "photo-1483985988355-763728e1935b"
  },
  "Casa, Decoracao & Organizacao": {
    label: "Casa & Decoração",
    kicker: "Decoração, móveis, organização",
    tone: "clay",
    img: "photo-1616486338812-3dadae4b4ace"
  },
  "Servicos para Casa": {
    label: "Serviços para Casa",
    kicker: "Reformas, lavanderia, limpeza",
    tone: "steel",
    img: "photo-1527515637462-cff94eecc1ac"
  },
  "Imoveis & Construcao": {
    label: "Imóveis & Construção",
    kicker: "Corretores, construtoras, lançamentos",
    tone: "navy",
    img: "photo-1486406146926-c627a92ad1ab"
  },
  "Pets": {
    label: "Pets",
    kicker: "Veterinário, pet shop, hotel pet",
    tone: "mint",
    img: "photo-1601758228041-f3b2795255f1"
  },
  "Educacao & Cursos": {
    label: "Educação & Cursos",
    kicker: "Escolas, idiomas, cursos",
    tone: "sky",
    img: "photo-1509062522246-3755977927d7"
  },
  "Infantil & Familia": {
    label: "Infantil & Família",
    kicker: "Crianças, família, brinquedos",
    tone: "yellow",
    img: "photo-1503454537195-1dcabb73ffb9"
  },
  "Festas & Eventos": {
    label: "Festas & Eventos",
    kicker: "Buffets, recreação, celebrações",
    tone: "coral",
    img: "photo-1511795409834-ef04bbd61622"
  },
  "Lojas & Presentes": {
    label: "Lojas & Presentes",
    kicker: "Bazares, música, presentes",
    tone: "plum",
    img: "photo-1513201099705-a9746e1e201f"
  },
  "Instituicoes & Comunidade": {
    label: "Comunidade",
    kicker: "Instituições, ações sociais",
    tone: "ink",
    img: "photo-1518005020951-eccb494ad742"
  }
};

const state = {
  category: null,
  subcategory: "Todos",
  query: "",
  sort: "az"
};

const categoryGrid = document.getElementById("categoryGrid");
const cardsList = document.getElementById("cardsList");
const subnav = document.getElementById("subnav");
const searchForm = document.getElementById("searchForm");
const searchInput = document.getElementById("searchInput");
const clearSearch = document.getElementById("clearSearch");
const categorySelect = document.getElementById("categorySelect");
const sortSelect = document.getElementById("sortSelect");
const activeCategoryLabel = document.getElementById("activeCategoryLabel");
const resultsHeading = document.getElementById("resultsHeading");
const resultsMeta = document.getElementById("resultsMeta");
const mapCount = document.getElementById("mapCount");
const mapList = document.getElementById("mapList");
const weatherWidget = document.getElementById("weatherWidget");
const weatherIcon = document.getElementById("weatherIcon");
const weatherTemp = document.getElementById("weatherTemp");
const weatherDesc = document.getElementById("weatherDesc");
const resultsSection = document.querySelector(".results-section");
const mapLayout = document.querySelector(".map-layout");

const MAP_CENTER = [-23.645684, -46.668131];
const MAP_INITIAL_ZOOM = 15;
const MAP_NEIGHBORHOOD_BOUNDS = [
  [-23.666, -46.678],
  [-23.63, -46.652]
];
const mapState = {
  map: null,
  markers: new Map()
};

const unsplash = (id) => `https://images.unsplash.com/${id}?w=720&h=520&fit=crop&q=78&auto=format`;

function normalizeText(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

function formatCategory(category) {
  return CATEGORY_META[category]?.label || category;
}

function initials(value) {
  return String(value || "")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

function getCategoryEntries() {
  return Object.keys(CATEGORY_META)
    .map((category) => ({
      key: category,
      ...CATEGORY_META[category],
      count: dados.filter((item) => item.categorias.includes(category)).length
    }))
    .filter((category) => category.count > 0);
}

function getAllCategoryEntries() {
  return [
    ...getCategoryEntries(),
    {
      key: "Todos",
      label: "Todos os locais",
      kicker: "Ver guia completo",
      tone: "navy",
      img: "photo-1642188537432-41c8a331ebdb",
      count: dados.length
    }
  ];
}

function hasActiveIntent() {
  return Boolean(state.category || state.query);
}

function getSearchHaystack(item) {
  return normalizeText([
    item.nome,
    item.subcategoria,
    item.endereco,
    item.descricao,
    item.promocao,
    item.instagram,
    item.categoriaPrincipal,
    ...(item.categorias || []),
    ...(item.termosBusca || [])
  ].join(" "));
}

function getFilteredData() {
  if (!hasActiveIntent()) {
    return [];
  }

  const query = normalizeText(state.query);

  let filtered = dados.filter((item) => {
    const inCategory = !state.category || state.category === "Todos" || item.categorias.includes(state.category);
    const inSubcategory = state.subcategory === "Todos" || item.subcategoria === state.subcategory;
    const inSearch = !query || getSearchHaystack(item).includes(query);
    return inCategory && inSubcategory && inSearch;
  });

  filtered = [...filtered].sort((a, b) => {
    if (state.sort === "az") {
      return a.nome.localeCompare(b.nome, "pt-BR");
    }
    if (state.sort === "citados") {
      return b.postsAno - a.postsAno || a.nome.localeCompare(b.nome, "pt-BR");
    }
    return new Date(b.ultimoPost) - new Date(a.ultimoPost) || a.nome.localeCompare(b.nome, "pt-BR");
  });

  return filtered;
}

function renderCategorySelect() {
  if (!categorySelect) return;
  categorySelect.innerHTML = "";
  getAllCategoryEntries().forEach((category) => {
    const option = document.createElement("option");
    option.value = category.key;
    option.textContent = category.key === "Todos" ? "Todas" : category.label;
    categorySelect.appendChild(option);
  });
  categorySelect.value = state.category || "Todos";
}

function renderCategoryGrid() {
  categoryGrid.innerHTML = "";

  const categories = getAllCategoryEntries();

  categories.forEach((category) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `category-card tone-${category.tone}`;
    button.style.setProperty("--category-image", `url("${unsplash(category.img)}")`);
    button.setAttribute("aria-pressed", state.category === category.key ? "true" : "false");
    button.innerHTML = `
      <span class="category-overlay" aria-hidden="true"></span>
      <span class="category-content">
        <span class="category-label">${category.label}</span>
      </span>
    `;
    button.addEventListener("click", () => {
      state.category = category.key;
      state.subcategory = "Todos";
      if (categorySelect) categorySelect.value = category.key;
      render();
      document.querySelector(".results-section").scrollIntoView({ behavior: "smooth", block: "start" });
    });
    categoryGrid.appendChild(button);
  });
}

function renderSubnav() {
  if (!state.category) {
    subnav.innerHTML = "";
    return;
  }

  const source = state.category === "Todos"
    ? dados
    : dados.filter((item) => item.categorias.includes(state.category));
  const subcategories = [
    ...new Set(source.map((item) => item.subcategoria).filter(Boolean))
  ].sort((a, b) => a.localeCompare(b, "pt-BR"));
  subcategories.push("Todos");

  subnav.innerHTML = "";
  subcategories.forEach((subcategory) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `subpill ${state.subcategory === subcategory ? "active" : ""}`;
    button.textContent = subcategory;
    button.addEventListener("click", () => {
      state.subcategory = subcategory;
      renderResults();
      renderSubnav();
    });
    subnav.appendChild(button);
  });
}

function renderResultsHeader(filtered) {
  const categoryName = state.category
    ? state.category === "Todos" ? "Todos os locais" : formatCategory(state.category)
    : "Busca";
  activeCategoryLabel.textContent = categoryName;
  resultsHeading.textContent = !state.category
    ? "Resultados"
    : state.subcategory === "Todos" ? "Estabelecimentos" : state.subcategory;

  const searchLabel = state.query ? ` para "${state.query}"` : "";
  resultsMeta.textContent = `${filtered.length} resultado${filtered.length === 1 ? "" : "s"}${searchLabel}`;
}

function renderCards() {
  if (!hasActiveIntent()) {
    cardsList.innerHTML = "";
    resultsMeta.textContent = "";
    return;
  }

  const filtered = getFilteredData();
  renderResultsHeader(filtered);
  renderMap(filtered);
  cardsList.innerHTML = "";

  if (!filtered.length) {
    cardsList.innerHTML = `
      <div class="empty-state">
        <strong>Nenhum local encontrado.</strong>
        <span>Tente outra busca ou volte para todos os locais.</span>
      </div>
    `;
    return;
  }

  filtered.forEach((item) => {
    const card = document.createElement("article");
    card.className = "business-card";
    const phone = item.telefones?.[0] || "";
    const mapsQuery = encodeURIComponent(`${item.nome} ${item.endereco || "Vila Mascote São Paulo"}`);
    const postUrl = item.linksPosts?.[0] || "";

    card.innerHTML = `
      <div class="card-main">
        <div class="card-heading">
          <span class="card-category">${formatCategory(item.categoriaPrincipal)}</span>
          <h3>${item.nome}</h3>
          <p>${item.descricao || "Estabelecimento da Vila Mascote."}</p>
          ${item.promocao ? `<div class="promo-callout">${item.promocao}</div>` : ""}
        </div>

        <div class="card-tags">
          <span>${item.subcategoria}</span>
          ${item.categorias.filter((category) => category !== item.categoriaPrincipal).slice(0, 2).map((category) => `<span>${formatCategory(category)}</span>`).join("")}
        </div>
      </div>

      <div class="card-side">
        ${item.endereco ? `<p class="address">${item.endereco}</p>` : `<p class="address muted">Endereço a validar</p>`}
        <div class="card-actions">
          ${phone ? `<a href="https://wa.me/55${phone}" target="_blank" rel="noopener">WhatsApp</a>` : ""}
          ${item.instagram ? `<a href="https://instagram.com/${item.instagram}" target="_blank" rel="noopener">Instagram</a>` : ""}
          ${item.endereco ? `<a href="https://maps.google.com/?q=${mapsQuery}" target="_blank" rel="noopener">Mapa</a>` : ""}
          ${postUrl ? `<a href="${postUrl}" target="_blank" rel="noopener">Veja Post</a>` : ""}
        </div>
      </div>
    `;

    cardsList.appendChild(card);
  });
}

function renderResults() {
  renderCards();
}

function getMapData() {
  return hasActiveIntent() ? getFilteredData() : dados;
}

function isInsideMapBounds(item) {
  if (!Number.isFinite(item.lat) || !Number.isFinite(item.lng)) return false;
  const [[south, west], [north, east]] = MAP_NEIGHBORHOOD_BOUNDS;
  return item.lat >= south && item.lat <= north && item.lng >= west && item.lng <= east;
}

function getMapItems(filtered = getMapData()) {
  return filtered.filter(isInsideMapBounds);
}

function mapIconName(item) {
  const text = normalizeText([
    item.categoriaPrincipal,
    item.subcategoria,
    ...(item.categorias || [])
  ].join(" "));

  if (text.includes("gastronomia") || text.includes("delivery") || text.includes("restaurante")) return "food";
  if (text.includes("cafe") || text.includes("padaria") || text.includes("doce")) return "coffee";
  if (text.includes("mercado") || text.includes("emporio") || text.includes("conveniencia")) return "market";
  if (text.includes("saude") || text.includes("clinica")) return "health";
  if (text.includes("beleza") || text.includes("estetica")) return "spark";
  if (text.includes("academia") || text.includes("esporte") || text.includes("bem-estar")) return "wellness";
  if (text.includes("moda") || text.includes("calcado") || text.includes("acessorio")) return "bag";
  if (text.includes("casa") || text.includes("decoracao") || text.includes("servicos para casa")) return "home";
  if (text.includes("imoveis") || text.includes("construcao")) return "building";
  if (text.includes("pet")) return "pet";
  if (text.includes("educacao") || text.includes("curso")) return "book";
  if (text.includes("infantil") || text.includes("familia")) return "family";
  if (text.includes("festa") || text.includes("evento")) return "party";
  if (text.includes("presente") || text.includes("loja")) return "gift";
  if (text.includes("instituicao") || text.includes("comunidade")) return "community";
  return "place";
}

function mapIconSvg(name) {
  const icons = {
    food: '<path d="M8 3v18"/><path d="M5 3v5a3 3 0 0 0 6 0V3"/><path d="M16 3v18"/><path d="M16 3c2 2 3 4 3 7 0 2-1 3-3 3"/>',
    coffee: '<path d="M5 7h10v5a4 4 0 0 1-4 4H9a4 4 0 0 1-4-4Z"/><path d="M15 8h2a2 2 0 0 1 0 4h-2"/><path d="M6 20h11"/><path d="M8 3v2"/><path d="M12 3v2"/>',
    market: '<path d="M6 8h13l-2 8H8Z"/><path d="M6 8 5 5H3"/><circle cx="9" cy="19" r="1"/><circle cx="16" cy="19" r="1"/>',
    health: '<path d="M12 5v14"/><path d="M5 12h14"/>',
    spark: '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8Z"/><path d="M18 15l.7 2 2 .7-2 .7-.7 2-.7-2-2-.7 2-.7Z"/>',
    wellness: '<path d="M6 16c3-5 9-5 12 0"/><path d="M9 12a3 3 0 1 1 6 0"/><path d="M4 19h16"/>',
    bag: '<path d="M6 8h12l-1 12H7Z"/><path d="M9 8a3 3 0 0 1 6 0"/>',
    home: '<path d="M4 11 12 4l8 7"/><path d="M6 10v10h12V10"/><path d="M10 20v-6h4v6"/>',
    building: '<path d="M6 20V5h9v15"/><path d="M15 9h3v11"/><path d="M9 8h3"/><path d="M9 12h3"/><path d="M9 16h3"/>',
    pet: '<circle cx="7" cy="9" r="1.5"/><circle cx="12" cy="6" r="1.5"/><circle cx="17" cy="9" r="1.5"/><path d="M7.5 16a4.5 4.5 0 0 1 9 0c0 2-2 3-4.5 3s-4.5-1-4.5-3Z"/>',
    book: '<path d="M5 5h6a3 3 0 0 1 3 3v11a3 3 0 0 0-3-3H5Z"/><path d="M19 5h-5a3 3 0 0 0-3 3"/>',
    family: '<circle cx="9" cy="8" r="2"/><circle cx="15" cy="8" r="2"/><path d="M5 18a4 4 0 0 1 8 0"/><path d="M11 18a4 4 0 0 1 8 0"/>',
    party: '<path d="m5 20 4-14 10 10Z"/><path d="M14 5h.01"/><path d="M18 3h.01"/><path d="M20 8h.01"/>',
    gift: '<path d="M4 10h16v10H4Z"/><path d="M12 10v10"/><path d="M4 14h16"/><path d="M8 10c-2 0-3-1-3-2s1-2 2-2c2 0 3 4 5 4"/><path d="M16 10c2 0 3-1 3-2s-1-2-2-2c-2 0-3 4-5 4"/>',
    community: '<path d="M5 20V9l7-5 7 5v11"/><path d="M9 20v-6h6v6"/><path d="M9 10h6"/>',
    place: '<path d="M12 21s6-5.5 6-11a6 6 0 0 0-12 0c0 5.5 6 11 6 11Z"/><circle cx="12" cy="10" r="2"/>'
  };
  return `<svg viewBox="0 0 24 24" aria-hidden="true">${icons[name] || icons.place}</svg>`;
}

function mapSymbol(item, selected = false) {
  return `<span class="map-pin${selected ? " selected" : ""}">${mapIconSvg(mapIconName(item))}</span>`;
}

function markerIcon(item, selected = false) {
  return L.divIcon({
    className: "",
    html: mapSymbol(item, selected),
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -13]
  });
}

function focusMapItem(item) {
  if (!mapState.map || !item) return;
  const marker = mapState.markers.get(item.id);
  mapState.markers.forEach((entry, id) => {
    const target = dados.find((local) => local.id === id);
    if (target) entry.setIcon(markerIcon(target, target.id === item.id));
  });
  document.querySelectorAll(".map-list-item").forEach((button) => {
    button.classList.toggle("active", Number(button.dataset.id) === item.id);
  });
  mapState.map.flyTo([item.lat, item.lng], 16, { duration: 0.7 });
  marker?.openPopup();
}

function renderMapList(items) {
  if (!mapList) return;
  mapList.hidden = false;
  mapLayout?.classList.remove("map-only");
  if (!items.length) {
    mapList.innerHTML = `<p class="map-empty">Nenhum local com mapa para este filtro.</p>`;
    return;
  }

  mapList.innerHTML = items.map((item) => `
    <button class="map-list-item" type="button" data-id="${item.id}">
      ${mapSymbol(item)}
      <strong>${item.nome}</strong>
      <small>${item.endereco || "Vila Mascote"}</small>
    </button>
  `).join("");

  mapList.querySelectorAll(".map-list-item").forEach((button) => {
    button.addEventListener("click", () => {
      const item = items.find((local) => local.id === Number(button.dataset.id));
      focusMapItem(item);
    });
  });
}

function renderMap(filtered = getMapData()) {
  const items = getMapItems(filtered);
  if (mapCount) {
    mapCount.textContent = `${items.length} ${items.length === 1 ? "local" : "locais"}`;
  }
  renderMapList(items);

  if (!mapState.map || !window.L) return;

  mapState.markers.forEach((marker) => marker.remove());
  mapState.markers.clear();

  const bounds = L.latLngBounds([]);
  items.forEach((item) => {
    const marker = L.marker([item.lat, item.lng], { icon: markerIcon(item) })
      .addTo(mapState.map)
      .bindPopup(`
        <strong>${item.nome}</strong>
        <small>${formatCategory(item.categoriaPrincipal)}</small>
        <span>${item.endereco || "Vila Mascote"}</span>
      `);
    marker.on("click", () => focusMapItem(item));
    mapState.markers.set(item.id, marker);
    bounds.extend([item.lat, item.lng]);
  });

  if (!hasActiveIntent()) {
    mapState.map.setView(MAP_CENTER, MAP_INITIAL_ZOOM);
  } else if (items.length > 1 && bounds.isValid()) {
    mapState.map.fitBounds(bounds, { padding: [26, 26], maxZoom: 15 });
  } else if (items.length === 1) {
    mapState.map.setView([items[0].lat, items[0].lng], 16);
  } else {
    mapState.map.setView(MAP_CENTER, MAP_INITIAL_ZOOM);
  }
}

function initMap() {
  if (!window.L || !document.getElementById("map")) return;
  const neighborhoodBounds = L.latLngBounds(MAP_NEIGHBORHOOD_BOUNDS);
  mapState.map = L.map("map", {
    scrollWheelZoom: false,
    zoomControl: true,
    maxBounds: neighborhoodBounds.pad(0.35),
    maxBoundsViscosity: 0.65
  }).setView(MAP_CENTER, MAP_INITIAL_ZOOM);

  const streetLayer = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors"
  });

  const satelliteLayer = L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    {
      maxZoom: 19,
      attribution: "Tiles &copy; Esri, Maxar, Earthstar Geographics, and the GIS User Community"
    }
  );

  streetLayer.addTo(mapState.map);
  L.control.layers(
    {
      "Mapa": streetLayer,
      "Satélite": satelliteLayer
    },
    null,
    { collapsed: false }
  ).addTo(mapState.map);

  renderMap();
}

async function loadWeather() {
  if (!weatherWidget || !weatherIcon || !weatherTemp || !weatherDesc) return;

  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 6000);

  try {
    const res = await fetch("https://wttr.in/Vila+Mascote,Sao+Paulo?format=j1", { signal: ctrl.signal });
    clearTimeout(timer);
    if (!res.ok) return;

    const data = await res.json();
    const current = data.current_condition[0];
    const today = data.weather[0];
    const code = Number.parseInt(current.weatherCode, 10);
    const rainChance = Math.max(...today.hourly.map((hour) => Number.parseInt(hour.chanceofrain, 10)));
    const willRain = rainChance > 40;

    const icon =
      code === 113 ? "☀️" :
      code === 116 ? "⛅" :
      code === 119 || code === 122 ? "☁️" :
      code === 143 || code === 248 || code === 260 ? "🌫️" :
      code === 200 || code >= 386 ? "⛈️" :
      code >= 263 && code <= 308 ? "🌧️" :
      code >= 311 && code <= 338 ? "🌨️" :
      code >= 353 && code <= 381 ? "🌦️" : "🌤️";

    weatherIcon.textContent = icon;
    weatherTemp.textContent = `${current.temp_C}°`;
    weatherDesc.textContent = `${willRain ? "🌧 " : ""}↑${today.maxtempC}° ↓${today.mintempC}°`;
    weatherWidget.classList.add("loaded");
  } catch {
    clearTimeout(timer);
    try {
      const res = await fetch("https://wttr.in/Vila+Mascote,Sao+Paulo?format=%c+%t");
      if (!res.ok) return;
      const text = (await res.text()).trim();
      const splitAt = text.indexOf(" ");
      if (splitAt === -1) return;
      weatherIcon.textContent = text.slice(0, splitAt);
      weatherTemp.textContent = text.slice(splitAt + 1).replace(/^\+/, "");
      weatherDesc.textContent = "";
      weatherWidget.classList.add("loaded");
    } catch {
      weatherDesc.textContent = "";
    }
  }
}

function render() {
  resultsSection.hidden = !hasActiveIntent();
  if (sortSelect) sortSelect.value = state.sort;
  renderCategorySelect();
  renderCategoryGrid();
  renderSubnav();
  renderResults();
  renderMap();
}

function init() {
  searchInput.addEventListener("input", (event) => {
    state.query = event.target.value.trim();
    if (!resultsSection.hidden || state.category) {
      render();
    }
  });

  clearSearch?.addEventListener("click", () => {
    state.query = "";
    searchInput.value = "";
    render();
    searchInput.focus();
  });

  categorySelect?.addEventListener("change", (event) => {
    state.category = event.target.value;
    state.subcategory = "Todos";
    render();
    if (hasActiveIntent()) {
      resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });

  searchForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    state.query = searchInput.value.trim();
    state.subcategory = "Todos";
    render();
    if (hasActiveIntent()) {
      resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });

  sortSelect.addEventListener("change", (event) => {
    state.sort = event.target.value;
    renderResults();
  });

  render();
  initMap();
  loadWeather();
}

document.addEventListener("DOMContentLoaded", init);
