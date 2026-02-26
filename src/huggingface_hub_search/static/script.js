(function () {
    "use strict";

    var root = element.querySelector(".hf-search");
    var dataScript = element.querySelector("script.hf-search-data");
    var inputEl = root.querySelector(".hf-search-input");
    var clearEl = root.querySelector(".hf-search-clear");
    var dropdown = root.querySelector(".hf-search-dropdown");
    var filtersEl = root.querySelector(".hf-search-filters");

    var searchType = String(props.search_type || "all");
    var submitOnSelect = props.submit_on_select !== false;

    var API_URL = "https://huggingface.co/api/quicksearch";
    var DEBOUNCE_MS = 300;
    var RESULT_LIMIT = props.result_limit || 5;

    var state = {
        query: "",
        results: [],
        activeIndex: -1,
        isOpen: false,
        abortController: null,
        debounceTimer: null,
        lastApiData: null,
        userFilters: null,
        // When submit_on_select=false, a dropdown click fills the input but does
        // not immediately set props.value.  The selected result object (with full
        // type/url info) is cached here so that a subsequent Enter press can
        // submit the complete structured value rather than a bare string.
        pendingResult: null
    };

    // Category configuration
    // API returns different id fields per category:
    //   models/datasets/spaces → "id", users → "user", orgs → "name"
    var CATEGORIES = {
        models: { label: "Models", type: "model", idKey: "id" },
        datasets: { label: "Datasets", type: "dataset", idKey: "id" },
        spaces: { label: "Spaces", type: "space", idKey: "id" },
        users: { label: "Users", type: "user", idKey: "user" },
        orgs: { label: "Organizations", type: "org", idKey: "name" }
    };

    // Determine which categories to show
    var allowedTypes = searchType === "all"
        ? null
        : searchType.split(",").map(function (s) { return s.trim(); });

    function isTypeAllowed(type) {
        if (allowedTypes && allowedTypes.indexOf(type) === -1) return false;
        if (state.userFilters && state.userFilters.indexOf(type) === -1) return false;
        return true;
    }

    // --- Debounce ---
    function debounce(fn, ms) {
        return function () {
            var args = arguments;
            var ctx = this;
            if (state.debounceTimer) clearTimeout(state.debounceTimer);
            state.debounceTimer = setTimeout(function () {
                state.debounceTimer = null;
                fn.apply(ctx, args);
            }, ms);
        };
    }

    // --- API search ---
    function doSearch(query) {
        if (!query) {
            state.results = [];
            closeDropdown();
            return;
        }

        // Cancel any in-flight request
        if (state.abortController) {
            state.abortController.abort();
        }
        state.abortController = new AbortController();

        var params = new URLSearchParams();
        params.set("q", query);
        params.set("limit", String(RESULT_LIMIT));

        // Filter by type if narrowed to exactly one type
        var activeFilters = state.userFilters || allowedTypes;
        if (activeFilters && activeFilters.length === 1) {
            params.set("type", activeFilters[0]);
        }

        var url = API_URL + "?" + params.toString();

        fetch(url, { signal: state.abortController.signal })
            .then(function (res) {
                if (!res.ok) throw new Error("Search failed: " + res.status + " " + res.statusText);
                return res.json();
            })
            .then(function (data) {
                state.abortController = null;
                state.lastApiData = data;
                parseResults(data);
                if (state.results.length > 0) {
                    renderDropdown();
                    openDropdown();
                } else {
                    renderEmpty();
                    openDropdown();
                }
            })
            .catch(function (err) {
                if (err.name === "AbortError") return;
                state.abortController = null;
                state.results = [];
                renderError();
                openDropdown();
            });
    }

    var debouncedSearch = debounce(doSearch, DEBOUNCE_MS);

    // --- Parse API response into flat result list with category grouping ---
    function parseResults(data) {
        var results = [];
        var categoryOrder = ["models", "datasets", "spaces", "users", "orgs"];

        for (var c = 0; c < categoryOrder.length; c++) {
            var catKey = categoryOrder[c];
            var catConfig = CATEGORIES[catKey];
            if (!isTypeAllowed(catConfig.type)) continue;

            // The quicksearch API may return "users" results under "users"
            // and "orgs" under "orgs", or combine them. Handle both structures.
            var items = data[catKey];
            if (!items || !items.length) continue;

            for (var i = 0; i < items.length; i++) {
                var item = items[i];
                var id = item[catConfig.idKey] || item._id || "";
                if (!id) continue;
                // Avatar URLs may be relative (e.g. "/avatars/...")
                var avatar = item.avatarUrl || null;
                if (avatar && avatar.charAt(0) === "/") {
                    avatar = "https://huggingface.co" + avatar;
                }

                results.push({
                    id: id,
                    category: catKey,
                    type: catConfig.type,
                    label: catConfig.label,
                    avatarUrl: avatar
                });
            }
        }

        state.results = results;
        state.activeIndex = -1;
    }

    // --- Render dropdown ---
    function renderDropdown() {
        dropdown.innerHTML = "";
        var currentCategory = null;

        for (var i = 0; i < state.results.length; i++) {
            var result = state.results[i];

            // Insert category header when category changes
            if (result.category !== currentCategory) {
                currentCategory = result.category;
                var header = document.createElement("div");
                header.className = "hf-search-category";
                var dot = document.createElement("span");
                dot.className = "hf-search-category-dot hf-type-" + result.type;
                header.appendChild(dot);
                header.appendChild(document.createTextNode(result.label));
                dropdown.appendChild(header);
            }

            var item = document.createElement("div");
            item.className = "hf-search-item";
            item.setAttribute("data-index", String(i));
            item.setAttribute("data-id", result.id);

            if (result.avatarUrl) {
                var avatar = document.createElement("img");
                avatar.className = "hf-search-item-avatar";
                avatar.src = result.avatarUrl;
                avatar.alt = "";
                avatar.loading = "lazy";
                item.appendChild(avatar);
            }

            var idSpan = document.createElement("span");
            idSpan.className = "hf-search-item-id";
            idSpan.textContent = result.id;
            item.appendChild(idSpan);

            dropdown.appendChild(item);
        }
    }

    function renderEmpty() {
        dropdown.innerHTML = "";
        var msg = document.createElement("div");
        msg.className = "hf-search-status";
        msg.textContent = "No results found";
        dropdown.appendChild(msg);
    }

    function renderError() {
        dropdown.innerHTML = "";
        var msg = document.createElement("div");
        msg.className = "hf-search-status";
        msg.textContent = "Search failed — please try again";
        dropdown.appendChild(msg);
    }

    // --- Dropdown visibility ---
    function openDropdown() {
        state.isOpen = true;
        dropdown.classList.add("hf-search-open");
    }

    function closeDropdown() {
        state.isOpen = false;
        state.activeIndex = -1;
        dropdown.classList.remove("hf-search-open");
    }

    // --- Keyboard navigation ---
    function updateActiveItem() {
        var items = dropdown.querySelectorAll(".hf-search-item");
        for (var i = 0; i < items.length; i++) {
            if (i === state.activeIndex) {
                items[i].classList.add("hf-search-active");
                // Scroll into view if needed
                items[i].scrollIntoView({ block: "nearest" });
            } else {
                items[i].classList.remove("hf-search-active");
            }
        }
    }

    // --- URL construction ---
    function buildUrl(id, type) {
        var base = "https://huggingface.co";
        switch (type) {
            case "dataset": return base + "/datasets/" + id;
            case "space": return base + "/spaces/" + id;
            default: return base + "/" + id;
        }
    }

    // --- Selection ---
    // Accepts a result object {id, type, ...} from dropdown or a plain string
    // from manual input.
    //
    // forceSubmit: when true, always commit (set props.value) regardless of
    //   submitOnSelect.  Used for explicit Enter-key confirmations.
    function selectResult(resultOrId, forceSubmit) {
        var id, type, url;
        if (resultOrId && typeof resultOrId === "object") {
            id = resultOrId.id;
            type = resultOrId.type;
            url = buildUrl(id, type);
        } else {
            id = String(resultOrId);
            // Infer type when only one type is allowed
            type = (allowedTypes && allowedTypes.length === 1) ? allowedTypes[0] : null;
            url = type ? buildUrl(id, type) : null;
        }

        inputEl.value = id;
        closeDropdown();

        if (submitOnSelect || forceSubmit) {
            // Setting props.value causes Gradio to automatically dispatch
            // the "change" event — no explicit trigger("change") needed.
            props.value = JSON.stringify({ id: id, type: type, url: url });
            state.pendingResult = null;
        } else {
            // submit_on_select=false: fill the input without committing.
            // Cache the full result so that a subsequent Enter press can
            // submit the structured value (preserving type/url).
            state.pendingResult = { id: id, type: type, url: url };
        }
    }

    // --- Filter chips (pre-rendered in HTML template) ---
    // Read existing chip elements from the DOM and initialize state.
    var chipEls = filtersEl.querySelectorAll(".hf-search-filter-chip");

    if (chipEls.length > 0) {
        state.userFilters = [];
        for (var ci2 = 0; ci2 < chipEls.length; ci2++) {
            state.userFilters.push(chipEls[ci2].getAttribute("data-type"));
        }

        // Use event delegation so handlers survive DOM re-renders.
        filtersEl.addEventListener("click", function (e) {
            var target = e.target;
            while (target && target !== filtersEl) {
                if (target.classList && target.classList.contains("hf-search-filter-chip")) {
                    var type = target.getAttribute("data-type");
                    var idx = state.userFilters.indexOf(type);
                    if (idx !== -1) {
                        if (state.userFilters.length <= 1) {
                            // Sole active chip → reset: make all chips active
                            state.userFilters = [];
                            var resetChips = filtersEl.querySelectorAll(".hf-search-filter-chip");
                            for (var ri = 0; ri < resetChips.length; ri++) {
                                state.userFilters.push(resetChips[ri].getAttribute("data-type"));
                            }
                        } else {
                            // Multiple active → exclusive select: keep only the clicked chip
                            state.userFilters = [type];
                        }
                    } else {
                        // Inactive chip → additive: add to current selection
                        state.userFilters.push(type);
                    }
                    syncChipVisuals();

                    // Re-filter cached results if available
                    if (state.lastApiData && state.query) {
                        parseResults(state.lastApiData);
                        if (state.results.length > 0) {
                            renderDropdown();
                            openDropdown();
                        } else {
                            renderEmpty();
                            openDropdown();
                        }
                    }
                    return;
                }
                target = target.parentElement;
            }
        });
    }

    // --- Event listeners ---

    // Input typing
    inputEl.addEventListener("input", function () {
        state.query = inputEl.value.trim();
        state.pendingResult = null;
        if (state.query.length > 0) {
            debouncedSearch(state.query);
        } else {
            state.results = [];
            closeDropdown();
        }
    });

    // Focus opens dropdown if there are results
    inputEl.addEventListener("focus", function () {
        if (state.results.length > 0 && state.query.length > 0) {
            renderDropdown();
            openDropdown();
        }
    });

    // Keyboard navigation
    inputEl.addEventListener("keydown", function (e) {
        if (!state.isOpen) {
            if (e.key === "Enter" && inputEl.value.trim()) {
                // Enter with closed dropdown is always an explicit commit.
                // If the user previously clicked a dropdown item without
                // submitting (submit_on_select=false), reuse the cached
                // structured result so type/url are preserved.
                var pending = state.pendingResult;
                if (pending && pending.id === inputEl.value.trim()) {
                    props.value = JSON.stringify(pending);
                    state.pendingResult = null;
                } else {
                    selectResult(inputEl.value.trim(), true);
                }
                e.preventDefault();
            }
            return;
        }

        switch (e.key) {
            case "ArrowDown":
                e.preventDefault();
                state.activeIndex = Math.min(state.activeIndex + 1, state.results.length - 1);
                updateActiveItem();
                break;
            case "ArrowUp":
                e.preventDefault();
                state.activeIndex = Math.max(state.activeIndex - 1, -1);
                updateActiveItem();
                break;
            case "Enter":
                // Enter with an open dropdown is always an explicit commit.
                e.preventDefault();
                if (state.activeIndex >= 0 && state.activeIndex < state.results.length) {
                    selectResult(state.results[state.activeIndex], true);
                } else if (inputEl.value.trim()) {
                    selectResult(inputEl.value.trim(), true);
                }
                break;
            case "Escape":
                e.preventDefault();
                closeDropdown();
                break;
        }
    });

    // Click on dropdown item (event delegation)
    dropdown.addEventListener("mousedown", function (e) {
        // Prevent input blur which would close dropdown before click registers
        e.preventDefault();

        var target = e.target;
        while (target && target !== dropdown) {
            if (target.classList && target.classList.contains("hf-search-item")) {
                var idx = parseInt(target.getAttribute("data-index"), 10);
                if (!isNaN(idx) && state.results[idx]) {
                    selectResult(state.results[idx]);
                }
                return;
            }
            target = target.parentElement;
        }
    });

    // Clear button
    clearEl.addEventListener("mousedown", function (e) {
        e.preventDefault();
        inputEl.value = "";
        state.query = "";
        state.results = [];
        state.pendingResult = null;
        closeDropdown();
        inputEl.focus();

        // Setting props.value causes Gradio to automatically dispatch "change".
        props.value = "";
    });

    // Click outside to close
    document.addEventListener("mousedown", function (e) {
        if (!root.contains(e.target)) {
            closeDropdown();
        }
    });

    // --- Chip visual sync (re-applies JS state after Gradio DOM morph) ---
    function syncChipVisuals() {
        if (!state.userFilters) return;
        var allChips = filtersEl.querySelectorAll(".hf-search-filter-chip");
        for (var si = 0; si < allChips.length; si++) {
            var chipType = allChips[si].getAttribute("data-type");
            if (state.userFilters.indexOf(chipType) !== -1) {
                allChips[si].classList.add("active");
            } else {
                allChips[si].classList.remove("active");
            }
        }
    }

    // --- Value sync from Python (MutationObserver) ---
    function handleValue() {
        var raw = dataScript.textContent.trim();
        if (!raw || raw === "null" || raw === "undefined") {
            syncChipVisuals();
            return;
        }

        // Value may be JSON (structured) or a plain string (repo ID)
        var displayId = raw;
        try {
            var parsed = JSON.parse(raw);
            if (parsed && typeof parsed === "object" && parsed.id) {
                displayId = parsed.id;
            }
        } catch (_e) {
            // Plain string value - use as-is
        }

        if (displayId !== inputEl.value && !state.isOpen) {
            inputEl.value = displayId;
        }
        syncChipVisuals();
    }

    var observer = new MutationObserver(function () { handleValue(); });
    observer.observe(dataScript, { childList: true, characterData: true, subtree: true });

    // Initial value sync
    handleValue();
})();
