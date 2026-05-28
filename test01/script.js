const CATEGORY_META = {
  "Gastronomia & Delivery": {
    label: "Gastronomia",
    kicker: "Restaurantes, pizzarias, delivery",
    img: "photo-1517248135467-4c7edcad34c4"
  },
  "Cafes, Padarias & Doces": {
    label: "Cafés & Doces",
    kicker: "Padarias, bolos, açaí, chocolates",
    img: "photo-1442512595331-e89e73853f31"
  },
  "Mercados, Emporios & Conveniencia": {
    label: "Mercados & Conveniência",
    kicker: "Empórios, hortifruti, suplementos",
    img: "photo-1542838132-92c53300491e"
  },
  "Saude & Clinicas": {
    label: "Saúde & Clínicas",
    kicker: "Clínicas, óticas, nutrição, terapias",
    img: "photo-1576091160550-2173dba999ef"
  },
  "Beleza & Estetica": {
    label: "Beleza & Estética",
    kicker: "Salões, estética, spa, barbearias",
    img: "photo-1522337360788-8b13dee7a37e"
  },
  "Academias, Esportes & Bem-Estar": {
    label: "Esportes & Bem-Estar",
    kicker: "Academias, pilates, yoga, artes marciais",
    img: "photo-1534438327276-14e5300c3a48"
  },
  "Moda, Calcados & Acessorios": {
    label: "Moda & Acessórios",
    kicker: "Roupas, calçados, bolsas, semijoias",
    img: "photo-1483985988355-763728e1935b"
  },
  "Casa, Decoracao & Organizacao": {
    label: "Casa & Decoração",
    kicker: "Decoração, móveis, organização",
    img: "photo-1616486338812-3dadae4b4ace"
  },
  "Servicos para Casa": {
    label: "Serviços para Casa",
    kicker: "Reformas, lavanderia, limpeza",
    img: "photo-1527515637462-cff94eecc1ac"
  },
  "Imoveis & Construcao": {
    label: "Imóveis & Construção",
    kicker: "Corretores, construtoras, lançamentos",
    img: "photo-1486406146926-c627a92ad1ab"
  },
  "Pets": {
    label: "Pets",
    kicker: "Veterinário, pet shop, hotel pet",
    img: "photo-1601758228041-f3b2795255f1"
  },
  "Educacao & Cursos": {
    label: "Educação & Cursos",
    kicker: "Escolas, idiomas, cursos",
    img: "photo-1509062522246-3755977927d7"
  },
  "Infantil & Familia": {
    label: "Infantil & Família",
    kicker: "Crianças, família, brinquedos",
    img: "photo-1503454537195-1dcabb73ffb9"
  },
  "Festas & Eventos": {
    label: "Festas & Eventos",
    kicker: "Buffets, recreação, celebrações",
    img: "photo-1511795409834-ef04bbd61622"
  },
  "Lojas & Presentes": {
    label: "Lojas & Presentes",
    kicker: "Bazares, música, presentes",
    img: "photo-1513201099705-a9746e1e201f"
  },
  "Instituicoes & Comunidade": {
    label: "Comunidade",
    kicker: "Instituições, ações sociais",
    img: "photo-1518005020951-eccb494ad742"
  }
};

const unsplash = (id) => `https://images.unsplash.com/${id}?w=720&h=520&fit=crop&q=78&auto=format`;

const state = {
  query: "",
  category: ""
};

const searchForm = document.getElementById("searchForm");
const searchInput = document.getElementById("searchInput");
const categorySelect = document.getElementById("categorySelect");
const categoryGrid = document.getElementById("categoryGrid");
const resultsSection = document.getElementById("resultsSection");
const resultsKicker = document.getElementById("resultsKicker");
const resultsTitle = document.getElementById("resultsTitle");
const resultsMeta = document.getElementById("resultsMeta");
const cardsList = document.getElementById("cardsList");

function normalizeText(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

function formatCategory(category) {
  return CATEGORY_META[category]?.label || category;
}

function categoryEntries() {
  const entries = Object.entries(CATEGORY_META)
    .map(([key, meta]) => ({
      key,
      ...meta,
      count: dados.filter((item) => item.categorias.includes(key)).length
    }))
    .filter((entry) => entry.count > 0);

  entries.push({
    key: "Todos",
    label: "Todos os locais",
    kicker: "Ver guia completo",
    img: "photo-1500530855697-b586d89ba3ee",
    count: dados.length
  });

  return entries;
}

function itemMatches(item) {
  const inCategory = !state.category || state.category === "Todos" || item.categorias.includes(state.category);
  const query = normalizeText(state.query);
  const haystack = normalizeText([
    item.nome,
    item.subcategoria,
    item.endereco,
    item.descricao,
    item.instagram,
    item.categoriaPrincipal,
    ...(item.categorias || [])
  ].join(" "));

  return inCategory && (!query || haystack.includes(query));
}

function renderCategorySelect() {
  categorySelect.innerHTML = `<option value="">Selecione</option>`;
  categoryEntries().forEach((entry) => {
    const option = document.createElement("option");
    option.value = entry.key;
    option.textContent = entry.label;
    categorySelect.appendChild(option);
  });
}

function renderCategoryGrid() {
  categoryGrid.innerHTML = "";
  categoryEntries().forEach((entry) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "category-card";
    button.style.setProperty("--category-image", `url("${unsplash(entry.img)}")`);
    button.innerHTML = `
      <strong>${entry.label}</strong>
      <span>${entry.kicker}</span>
    `;
    button.addEventListener("click", () => {
      state.category = entry.key;
      categorySelect.value = entry.key;
      renderResults(true);
    });
    categoryGrid.appendChild(button);
  });
}

function renderResults(shouldScroll = false) {
  const hasIntent = state.query || state.category;
  resultsSection.hidden = !hasIntent;
  if (!hasIntent) return;

  const filtered = dados.filter(itemMatches).sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"));
  const categoryLabel = state.category ? formatCategory(state.category) : "Busca";
  resultsKicker.textContent = categoryLabel;
  resultsTitle.textContent = state.category === "Todos" ? "Todos os locais" : "Estabelecimentos";
  resultsMeta.textContent = `${filtered.length} resultado${filtered.length === 1 ? "" : "s"}`;
  cardsList.innerHTML = "";

  if (!filtered.length) {
    cardsList.innerHTML = `<article class="business-card"><strong>Nenhum local encontrado.</strong><p>Tente buscar por outro termo ou categoria.</p></article>`;
  } else {
    filtered.slice(0, 36).forEach((item) => {
      const phone = item.telefones?.[0] || "";
      const mapsQuery = encodeURIComponent(`${item.nome} ${item.endereco || "Vila Mascote São Paulo"}`);
      const card = document.createElement("article");
      card.className = "business-card";
      card.innerHTML = `
        <strong>${item.nome}</strong>
        <p>${formatCategory(item.categoriaPrincipal)} · ${item.subcategoria}</p>
        <p>${item.endereco || "Endereço a validar"}</p>
        <div class="card-actions">
          ${phone ? `<a href="https://wa.me/55${phone}" target="_blank" rel="noopener">WhatsApp</a>` : ""}
          ${item.instagram ? `<a href="https://instagram.com/${item.instagram}" target="_blank" rel="noopener">Instagram</a>` : ""}
          ${item.endereco ? `<a href="https://maps.google.com/?q=${mapsQuery}" target="_blank" rel="noopener">Mapa</a>` : ""}
        </div>
      `;
      cardsList.appendChild(card);
    });
  }

  if (shouldScroll) {
    resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function init() {
  renderCategorySelect();
  renderCategoryGrid();

  searchInput.addEventListener("input", (event) => {
    state.query = event.target.value.trim();
  });

  categorySelect.addEventListener("change", (event) => {
    state.category = event.target.value;
    renderResults(true);
  });

  searchForm.addEventListener("submit", (event) => {
    event.preventDefault();
    state.query = searchInput.value.trim();
    state.category = categorySelect.value;
    renderResults(true);
  });
}

document.addEventListener("DOMContentLoaded", init);
