const COPY = {
  en: {
    title: "CJK font catalog",
    intro: "Preview the actual 2-bit device bitmaps, then download verified physical font files from GitHub Release.",
    searchLabel: "Search fonts", searchPlaceholder: "Name or description", languageLabel: "Language", categoryLabel: "Category", previewLabel: "Preview size", all: "All",
    downloads: "Download physical sizes", source: "Source", license: "License", manifest: "Release manifest", maker: "Make a custom font",
    footer: "Pages hosts only this catalog and compact PNG previews. Font binaries remain on GitHub Release.",
    verified: "Verified", loading: "Loading catalog…", empty: "No matching fonts.", error: "Catalog unavailable. Try again later.", families: count => `${count} font ${count === 1 ? "family" : "families"}`,
  },
  zh: {
    title: "CJK 字体目录",
    intro: "预览设备实际使用的 2-bit 点阵，并从 GitHub Release 下载已校验的物理字号字体。",
    searchLabel: "搜索字体", searchPlaceholder: "名称或简介", languageLabel: "语言", categoryLabel: "类型", previewLabel: "预览字号", all: "全部",
    downloads: "下载物理字号", source: "字体来源", license: "授权", manifest: "Release 清单", maker: "制作自制字体",
    footer: "Pages 只托管目录和轻量 PNG 预览；字体二进制仍由 GitHub Release 分发。",
    verified: "已核验", loading: "正在加载字体目录…", empty: "没有匹配的字体。", error: "字体目录暂时不可用，请稍后重试。", families: count => `${count} 个字体家族`,
  },
  ja: {
    title: "CJK フォントカタログ",
    intro: "端末で使われる実際の 2-bit ビットマップを確認し、検証済みの物理サイズを GitHub Release から取得できます。",
    searchLabel: "フォント検索", searchPlaceholder: "名前または説明", languageLabel: "言語", categoryLabel: "分類", previewLabel: "プレビューサイズ", all: "すべて",
    downloads: "物理サイズをダウンロード", source: "出典", license: "ライセンス", manifest: "Release マニフェスト", maker: "個人用フォントを作成",
    footer: "Pages はカタログと軽量 PNG のみを配信し、フォント本体は GitHub Release に置かれます。",
    verified: "確認済み", loading: "カタログを読み込み中…", empty: "該当するフォントはありません。", error: "カタログを読み込めませんでした。", families: count => `${count} ファミリー`,
  },
};

const state = { catalog: null, locale: "en", query: "", language: "", category: "", previewSize: "14" };
const nodes = {
  catalog: document.querySelector("#catalog"), status: document.querySelector("#status"), search: document.querySelector("#search"),
  language: document.querySelector("#language-filter"), category: document.querySelector("#category-filter"), previewSize: document.querySelector("#preview-size"),
  template: document.querySelector("#font-card-template"), manifest: document.querySelector("#manifest-link"),
};

function preferredLocale() {
  const stored = localStorage.getItem("crosspoint-font-catalog-locale");
  if (COPY[stored]) return stored;
  const language = navigator.language.toLowerCase();
  if (language.startsWith("zh")) return "zh";
  if (language.startsWith("ja")) return "ja";
  return "en";
}

function applyCopy() {
  const copy = COPY[state.locale];
  document.documentElement.lang = state.locale;
  document.querySelectorAll("[data-copy]").forEach(node => { const value = copy[node.dataset.copy]; if (typeof value === "string") node.textContent = value; });
  document.querySelectorAll("[data-copy-placeholder]").forEach(node => { node.placeholder = copy[node.dataset.copyPlaceholder]; });
  document.querySelectorAll("[data-locale]").forEach(button => button.setAttribute("aria-pressed", String(button.dataset.locale === state.locale)));
  render();
}

function optionValues(key) {
  if (!state.catalog) return [];
  const values = new Set();
  state.catalog.families.forEach(family => {
    if (key === "languages") family.languages.forEach(value => values.add(value));
    else if (family[key]) values.add(family[key]);
  });
  return [...values].sort((a, b) => a.localeCompare(b));
}

function populateFilters() {
  const allText = COPY[state.locale].all;
  for (const [node, values] of [[nodes.language, optionValues("languages")], [nodes.category, optionValues("category")]]) {
    const selected = node.value;
    node.replaceChildren(new Option(allText, ""), ...values.map(value => new Option(value, value)));
    node.value = values.includes(selected) ? selected : "";
  }
  const selectedSize = state.previewSize;
  nodes.previewSize.replaceChildren(...state.catalog.previewSizes.map(size => {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.previewSize = String(size);
    button.textContent = `${size} pt`;
    button.setAttribute("aria-pressed", String(String(size) === selectedSize));
    button.addEventListener("click", () => {
      state.previewSize = String(size);
      render();
    });
    return button;
  }));
  if (!state.catalog.previewSizes.map(String).includes(selectedSize)) state.previewSize = String(state.catalog.previewSizes[0]);
  nodes.previewSize.querySelectorAll("button").forEach(button => {
    button.setAttribute("aria-pressed", String(button.dataset.previewSize === state.previewSize));
  });
}

function humanBytes(value) {
  const units = ["B", "KiB", "MiB"];
  let size = value; let unit = 0;
  while (size >= 1024 && unit < units.length - 1) { size /= 1024; unit += 1; }
  return `${size.toFixed(unit === 0 ? 0 : 1)} ${units[unit]}`;
}

function familyDisplayName(family) {
  return family.displayNames[state.locale] || family.displayNames.en || family.name;
}

function render() {
  if (!state.catalog) return;
  const copy = COPY[state.locale];
  populateFilters();
  const query = state.query.trim().toLocaleLowerCase();
  const families = state.catalog.families.filter(family => {
    const searchableNames = Object.values(family.displayNames).join(" ");
    const matchesText = !query || `${family.name} ${searchableNames} ${family.description}`.toLocaleLowerCase().includes(query);
    const matchesLanguage = !state.language || family.languages.includes(state.language);
    const matchesCategory = !state.category || family.category === state.category;
    return matchesText && matchesLanguage && matchesCategory;
  });
  nodes.catalog.replaceChildren();
  families.forEach(family => {
    const fragment = nodes.template.content.cloneNode(true);
    const displayName = familyDisplayName(family);
    fragment.querySelector("h2").textContent = displayName;
    fragment.querySelector(".family-id").textContent = family.name;
    fragment.querySelector(".description").textContent = family.description;
    fragment.querySelector(".license-status").textContent = family.licenseStatus === "verified" ? copy.verified : family.licenseStatus;
    const preview = fragment.querySelector(".preview");
    preview.src = family.previews[state.previewSize];
    preview.alt = `${displayName}, ${state.previewSize} pt`;
    preview.addEventListener("error", () => preview.classList.add("is-broken"), { once: true });
    fragment.querySelector(".tags").textContent = [...family.languages, family.category].filter(Boolean).join(" · ");
    fragment.querySelector(".license").textContent = family.license;
    const downloads = fragment.querySelector(".downloads");
    downloads.setAttribute("aria-label", `${family.name}: ${copy.downloads}`);
    family.files.forEach(file => {
      const link = document.createElement("a");
      link.href = file.downloadUrl;
      link.textContent = `${file.physicalSize} pt`;
      link.setAttribute("aria-label", `${file.physicalSize} pt, ${humanBytes(file.byteSize)}`);
      link.title = `${file.physicalSize} pt · ${humanBytes(file.byteSize)}`;
      link.rel = "noopener noreferrer";
      downloads.append(link);
    });
    const source = fragment.querySelector(".source-link"); source.href = family.sourceUrl; source.textContent = copy.source;
    const license = fragment.querySelector(".license-link"); license.href = family.licenseUrl; license.textContent = copy.license;
    nodes.catalog.append(fragment);
  });
  nodes.status.textContent = families.length ? copy.families(families.length) : copy.empty;
}

function validateCatalog(catalog) {
  if (catalog?.schemaVersion !== 1 || catalog.cpfontVersion !== 4 || catalog.manifestVersion !== 2 || !Array.isArray(catalog.families)) throw new Error("Unsupported catalog schema");
  return catalog;
}

async function loadCatalog() {
  nodes.status.textContent = COPY[state.locale].loading;
  try {
    const response = await fetch("catalog.json", { cache: "no-cache" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.catalog = validateCatalog(await response.json());
    state.previewSize = String(state.catalog.previewSizes[0]);
    nodes.manifest.href = state.catalog.manifestUrl;
    render();
  } catch (error) {
    console.error(error);
    nodes.status.textContent = COPY[state.locale].error;
  }
}

document.querySelectorAll("[data-locale]").forEach(button => button.addEventListener("click", () => { state.locale = button.dataset.locale; localStorage.setItem("crosspoint-font-catalog-locale", state.locale); applyCopy(); }));
nodes.search.addEventListener("input", event => { state.query = event.target.value; render(); });
nodes.language.addEventListener("change", event => { state.language = event.target.value; render(); });
nodes.category.addEventListener("change", event => { state.category = event.target.value; render(); });

state.locale = preferredLocale();
applyCopy();
loadCatalog();
