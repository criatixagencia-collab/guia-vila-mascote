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
  sort: "recentes"
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
const totalCount = document.getElementById("totalCount");
const categoryCount = document.getElementById("categoryCount");
const mapCount = document.getElementById("mapCount");
const mapList = document.getElementById("mapList");
const resultsSection = document.querySelector(".results-section");
const mapLayout = document.querySelector(".map-layout");

const MAP_CENTER = [-23.6489, -46.6656];
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
      img: "photo-1500530855697-b586d89ba3ee",
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
    item.instagram,
    item.categoriaPrincipal,
    ...(item.categorias || [])
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
  categorySelect.innerHTML = `<option value="">Selecione</option>`;
  getAllCategoryEntries().forEach((category) => {
    const option = document.createElement("option");
    option.value = category.key;
    option.textContent = category.label;
    categorySelect.appendChild(option);
  });
  categorySelect.value = state.category || "";
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
        <span class="category-kicker">${category.kicker}</span>
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
          ${postUrl ? `<a href="${postUrl}" target="_blank" rel="noopener">Post</a>` : ""}
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

function getMapItems(filtered = getFilteredData()) {
  return filtered.filter((item) => Number.isFinite(item.lat) && Number.isFinite(item.lng));
}

function markerIcon(item, selected = false) {
  return L.divIcon({
    className: "",
    html: `<span class="map-pin${selected ? " selected" : ""}">${initials(item.nome)}</span>`,
    iconSize: [40, 40],
    iconAnchor: [20, 20],
    popupAnchor: [0, -18]
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
  if (!hasActiveIntent()) {
    mapList.innerHTML = "";
    mapList.hidden = true;
    mapLayout?.classList.add("map-only");
    return;
  }

  mapList.hidden = false;
  mapLayout?.classList.remove("map-only");
  if (!items.length) {
    mapList.innerHTML = `<p class="map-empty">Nenhum local com mapa para este filtro.</p>`;
    return;
  }

  mapList.innerHTML = items.slice(0, 36).map((item) => `
    <button class="map-list-item" type="button" data-id="${item.id}">
      <span>${initials(item.nome)}</span>
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
    mapCount.textContent = `${items.length} local${items.length === 1 ? "" : "is"}`;
  }
  renderMapList(items);

  if (!mapState.map || !window.L) return;

  mapState.markers.forEach((marker) => marker.remove());
  mapState.markers.clear();

  const bounds = [];
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
    bounds.push([item.lat, item.lng]);
  });

  if (bounds.length > 1) {
    mapState.map.fitBounds(bounds, { padding: [26, 26], maxZoom: 15 });
  } else if (bounds.length === 1) {
    mapState.map.setView(bounds[0], 16);
  } else {
    mapState.map.setView(MAP_CENTER, 14);
  }
}

function initMap() {
  if (!window.L || !document.getElementById("map")) return;
  mapState.map = L.map("map", {
    scrollWheelZoom: false,
    zoomControl: true
  }).setView(MAP_CENTER, 14);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors"
  }).addTo(mapState.map);

  renderMap();
}

function render() {
  resultsSection.hidden = !hasActiveIntent();
  renderCategorySelect();
  renderCategoryGrid();
  renderSubnav();
  renderResults();
  renderMap();
}

function init() {
  totalCount.textContent = `${dados.length} locais`;
  categoryCount.textContent = `${getCategoryEntries().length} categorias`;

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
    state.category = event.target.value || null;
    state.subcategory = "Todos";
    render();
    if (hasActiveIntent()) {
      resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });

  searchForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    state.query = searchInput.value.trim();
    state.category = categorySelect?.value || state.category;
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
}

document.addEventListener("DOMContentLoaded", init);
