/* Favorite search field (django-admin-search-field).
 *
 * Adds a star toggle next to the search field combobox. The starred field is
 * remembered per model in the browser's localStorage and pre-selected the next
 * time the changelist is opened without an explicit choice in the URL.
 *
 * Progressive enhancement: without JS (or without localStorage) the star
 * stays hidden/inert and the combobox keeps its native behaviour. */
(function () {
    "use strict";

    var STORAGE_PREFIX = "django-admin-search-field:favorite:";

    function readFavorite(key) {
        try {
            return window.localStorage.getItem(key);
        } catch (e) {
            return null;
        }
    }

    function writeFavorite(key, value) {
        try {
            if (value) {
                window.localStorage.setItem(key, value);
            } else {
                window.localStorage.removeItem(key);
            }
        } catch (e) {
            /* localStorage unavailable (private mode, blocked storage): ignore. */
        }
    }

    function hasOption(select, value) {
        for (var i = 0; i < select.options.length; i++) {
            if (select.options[i].value === value) {
                return true;
            }
        }
        return false;
    }

    function init(select, button) {
        var key = STORAGE_PREFIX + select.getAttribute("data-favorite-key");
        var params = new URLSearchParams(window.location.search);
        var searchbar = document.getElementById("searchbar");
        var searchVar = searchbar ? searchbar.name : "q";
        var labelAdd = button.getAttribute("data-label-add");
        var labelRemove = button.getAttribute("data-label-remove");
        var favorite = readFavorite(key);

        // Forget a favorite that no longer exists in search_fields.
        if (favorite && !hasOption(select, favorite)) {
            writeFavorite(key, null);
            favorite = null;
        }

        // Pre-select the favorite only on a "fresh" changelist: an explicit
        // choice in the URL (including "All fields") or an ongoing search
        // must keep reflecting what was actually searched.
        if (favorite && !params.has(select.name) && !params.get(searchVar)) {
            select.value = favorite;
        }

        for (var i = 0; i < select.options.length; i++) {
            select.options[i].setAttribute("data-label", select.options[i].textContent);
        }

        function render() {
            var isFavorite = !!select.value && select.value === favorite;
            var label = isFavorite ? labelRemove : labelAdd;
            button.classList.toggle("is-favorite", isFavorite);
            button.setAttribute("aria-pressed", isFavorite ? "true" : "false");
            button.setAttribute("title", label);
            button.setAttribute("aria-label", label);
            // "All fields" is the default already, so it can't be starred.
            button.disabled = !select.value;

            for (var j = 0; j < select.options.length; j++) {
                var option = select.options[j];
                var text = option.getAttribute("data-label");
                option.textContent = option.value && option.value === favorite ? "★ " + text : text;
            }
        }

        button.addEventListener("click", function () {
            favorite = select.value === favorite ? null : select.value;
            writeFavorite(key, favorite);
            render();
        });
        select.addEventListener("change", render);

        button.hidden = false;
        render();
    }

    var select = document.getElementById("search-field-select");
    var button = document.getElementById("search-field-favorite");
    if (select && button && select.getAttribute("data-favorite-key")) {
        init(select, button);
    }
})();
